from __future__ import annotations

import asyncio
import logging
import os
import threading
from pathlib import Path

from app.db.models import PublishTarget
from app.settings import settings

from .watermark import (
    apply_watermark,
    apply_watermark_to_dir,
    cleanup_watermark,
    cleanup_watermark_dir,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 30

TRANSIENT_ERRORS = (
    "Please wait a few minutes",
    "feedback_required",
    "challenge_required",
    "login_required",
    "checkpoint_required",
    "connection",
    "timeout",
    "Throttled",
    "rate limit",
    "try again",
    "temporarily blocked",
)


def _is_transient(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(err.lower() in msg for err in TRANSIENT_ERRORS)


class InstagramPublisher:

    def __init__(self) -> None:
        self._client = None
        self._awaiting_challenge = False
        self._challenge_code: str | None = None
        self._challenge_event = threading.Event()

    # ── Challenge handler (called from sync/thread context) ───

    def _challenge_code_handler(self, username: str, choice) -> str:
        """Called by instagrapi when Instagram requires a verification code."""
        self._awaiting_challenge = True
        self._challenge_event.clear()
        logger.info("Challenge required for %s, choice=%s", username, choice)
        if not self._challenge_event.wait(timeout=300):
            self._awaiting_challenge = False
            raise TimeoutError("Challenge code not provided in time (5 min timeout)")
        code = self._challenge_code or ""
        self._challenge_code = None
        self._awaiting_challenge = False
        return code

    def provide_challenge_code(self, code: str) -> None:
        """Call this from the bot when admin submits the verification code."""
        self._challenge_code = code
        self._challenge_event.set()

    # ── Login ─────────────────────────────────────────────────

    def _do_login(self) -> None:
        from instagrapi import Client
        cl = Client()
        cl.delay_range = [1, 3]
        cl.challenge_code_handler = self._challenge_code_handler
        session_path = settings.ig_session_path
        if session_path.exists():
            cl.load_settings(session_path)
        cl.login(settings.ig_username, settings.ig_password.get_secret_value())
        session_path.parent.mkdir(parents=True, exist_ok=True)
        cl.dump_settings(session_path)
        self._client = cl
        logger.info("Instagram login successful")

    async def async_login(self) -> None:
        """Login to Instagram in a background thread. Supports challenge flow."""
        self._awaiting_challenge = False
        self._challenge_event.clear()
        await asyncio.to_thread(self._do_login)

    def is_logged_in(self) -> bool:
        return self._client is not None

    def has_session(self) -> bool:
        return settings.ig_session_path.exists()

    def delete_session(self) -> None:
        if settings.ig_session_path.exists():
            settings.ig_session_path.unlink()
        self._client = None
        logger.info("Instagram session deleted")

    # ── Internal client getter ────────────────────────────────

    def _get_client(self):
        if self._client is None:
            from instagrapi import Client
            cl = Client()
            cl.delay_range = [1, 3]
            cl.challenge_code_handler = self._challenge_code_handler
            session_path = settings.ig_session_path
            if session_path.exists():
                cl.load_settings(session_path)
                cl.login(
                    settings.ig_username,
                    settings.ig_password.get_secret_value(),
                )
            else:
                cl.login(
                    settings.ig_username,
                    settings.ig_password.get_secret_value(),
                )
                cl.dump_settings(session_path)
            logger.info("Instagram client initialized")
            self._client = cl
        return self._client

    def _save_session(self) -> None:
        if self._client:
            try:
                self._client.dump_settings(settings.ig_session_path)
            except Exception:
                logger.exception("Failed to save session")

    def _relogin(self) -> None:
        logger.warning("Re-login to Instagram...")
        self._client = None
        self._get_client()

    async def publish(
        self,
        file_path: str,
        target: PublishTarget,
        caption: str = "",
    ) -> bool:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = await self._do_publish(file_path, target, caption)
                self._save_session()
                return result
            except Exception as exc:
                logger.exception(
                    "Publish attempt %d/%d failed for %s",
                    attempt, MAX_RETRIES, file_path,
                )
                if attempt < MAX_RETRIES and _is_transient(exc):
                    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.info("Retrying in %ds...", delay)
                    self._relogin()
                    await asyncio.sleep(delay)
                else:
                    return False
        return False

    async def _do_publish(
        self, file_path: str, target: PublishTarget, caption: str
    ) -> bool:
        dispatch = {
            PublishTarget.story_video: lambda: self._upload_story_video(file_path),
            PublishTarget.story_photo: lambda: self._upload_story_photo(file_path),
            PublishTarget.reels: lambda: self._upload_reels(file_path, caption),
            PublishTarget.post_video: lambda: self._upload_video_post(file_path, caption),
            PublishTarget.post_photo: lambda: self._upload_photo_post(file_path, caption),
            PublishTarget.album: lambda: self._upload_album(file_path, caption),
            PublishTarget.igtv: lambda: self._upload_igtv(file_path, caption),
        }
        handler = dispatch.get(target)
        if not handler:
            logger.error("Unknown target: %s", target)
            return False
        return await handler()

    async def _upload_story_video(self, path: str) -> bool:
        wm_path = await apply_watermark(path)
        try:
            cl = self._get_client()
            await asyncio.to_thread(cl.video_upload_to_story, wm_path)
            return True
        finally:
            await cleanup_watermark(wm_path, path)

    async def _upload_story_photo(self, path: str) -> bool:
        wm_path = await apply_watermark(path)
        try:
            cl = self._get_client()
            await asyncio.to_thread(cl.photo_upload_to_story, wm_path)
            return True
        finally:
            await cleanup_watermark(wm_path, path)

    async def _upload_reels(self, path: str, caption: str) -> bool:
        wm_path = await apply_watermark(path)
        try:
            cl = self._get_client()
            await asyncio.to_thread(cl.clip_upload, wm_path, caption)
            return True
        finally:
            await cleanup_watermark(wm_path, path)

    async def _upload_video_post(self, path: str, caption: str) -> bool:
        wm_path = await apply_watermark(path)
        try:
            cl = self._get_client()
            await asyncio.to_thread(cl.video_upload, wm_path, caption)
            return True
        finally:
            await cleanup_watermark(wm_path, path)

    async def _upload_photo_post(self, path: str, caption: str) -> bool:
        wm_path = await apply_watermark(path)
        try:
            cl = self._get_client()
            await asyncio.to_thread(cl.photo_upload, wm_path, caption)
            return True
        finally:
            await cleanup_watermark(wm_path, path)

    async def _upload_album(self, path: str, caption: str) -> bool:
        if not os.path.isdir(path):
            logger.error("Album path is not a directory: %s", path)
            return False
        wm_dir, wm_files = await apply_watermark_to_dir(path)
        if not wm_files:
            return False
        try:
            cl = self._get_client()
            await asyncio.to_thread(cl.album_upload, wm_files, caption)
            return True
        finally:
            await cleanup_watermark_dir(wm_dir, path)

    async def _upload_igtv(self, path: str, caption: str) -> bool:
        wm_path = await apply_watermark(path)
        try:
            cl = self._get_client()
            title = caption[:50] if caption else "Video"
            await asyncio.to_thread(cl.igtv_upload, wm_path, title, caption)
            return True
        finally:
            await cleanup_watermark(wm_path, path)


publisher = InstagramPublisher()
