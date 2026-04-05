from __future__ import annotations

import asyncio
import logging
import os
import re
from collections import defaultdict

from aiogram import F, Router
from aiogram.types import FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MediaType, SourcePlatform
from app.db.repositories import ContentRepo, UserRepo
from app.i18n import t
from app.settings import settings

logger = logging.getLogger(__name__)
router = Router(name="download")

TELEGRAM_FILE_LIMIT = 50 * 1024 * 1024  # 50 MB

# Max 2 simultaneous downloads per user; rejects immediately if both slots busy
_USER_SEMAPHORES: dict[int, asyncio.Semaphore] = defaultdict(lambda: asyncio.Semaphore(2))

URL_PATTERN = re.compile(
    r"https?://(www\.)?"
    r"(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com|"
    r"instagram\.com|"
    r"youtube\.com|youtu\.be)"
    r"\S*",
    re.IGNORECASE,
)

# @username-all  or  @username-3
STORY_PATTERN = re.compile(r"^\s*@([\w.]+)-(all|\d+)\s*$", re.IGNORECASE)


def _detect_platform(url: str) -> str | None:
    lower = url.lower()
    if "tiktok.com" in lower:
        return "tiktok"
    if "instagram.com" in lower:
        return "instagram"
    if "youtube.com" in lower or "youtu.be" in lower:
        return "youtube"
    return None


async def _send_file_to_user(message: Message, file_path: str, media_type: MediaType, lang: str = "ru") -> None:
    """Send the downloaded file back to the user with size check."""
    exists = await asyncio.to_thread(os.path.exists, file_path)
    if not exists:
        return

    is_dir = await asyncio.to_thread(os.path.isdir, file_path)
    if is_dir:
        entries = await asyncio.to_thread(os.listdir, file_path)
        files = sorted(
            os.path.join(file_path, f)
            for f in entries
            if not f.startswith(".")
        )
        for fpath in files[:10]:
            await _send_single_file(message, fpath, lang)
        return

    await _send_single_file(message, file_path, lang)


async def _send_single_file(message: Message, file_path: str, lang: str = "ru") -> None:
    file_size = await asyncio.to_thread(os.path.getsize, file_path)
    if file_size > TELEGRAM_FILE_LIMIT:
        await message.answer(t("dl_too_big", lang, mb=file_size // (1024 * 1024)))
        return

    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in (".mp4", ".mov", ".avi", ".mkv"):
            await message.answer_video(FSInputFile(file_path))
        elif ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
            await message.answer_photo(FSInputFile(file_path))
        else:
            await message.answer_document(FSInputFile(file_path))
    except Exception:
        logger.exception("Failed to send file %s to user", file_path)


@router.message(F.text.regexp(STORY_PATTERN))
async def on_story_command(message: Message, session: AsyncSession, lang: str = "ru") -> None:
    """Handle @username-all / @username-N to download Instagram stories."""
    text = (message.text or "").strip()
    m = STORY_PATTERN.match(text)
    if not m:
        return

    username = m.group(1)
    index_str = m.group(2).lower()
    index = None if index_str == "all" else int(index_str)

    from app.services.downloaders.instagram import InstagramDownloader

    downloader = InstagramDownloader()
    if not downloader.api_key:
        await message.answer(t("dl_no_hiker", lang))
        return

    sem = _USER_SEMAPHORES[message.from_user.id]
    if sem.locked():
        await message.answer(t("dl_busy", lang))
        return

    label = t("dl_story_all", lang) if index is None else t("dl_story_n", lang, n=index)
    progress_msg = await message.answer(t("dl_fetching", lang, label=label, username=username))

    async with sem:
        try:
            results = await downloader.fetch_user_stories(
                username=username,
                user_id=message.from_user.id,
                index=index,
            )
        except IndexError as exc:
            await progress_msg.edit_text(t("dl_stories_index_err", lang, exc=exc))
            return
        except Exception:
            logger.exception("Stories fetch failed for @%s", username)
            await progress_msg.edit_text(t("dl_stories_err", lang))
            return

        if not results:
            await progress_msg.edit_text(t("dl_no_stories", lang, username=username))
            return

        await progress_msg.edit_text(t("dl_sending_stories", lang, count=len(results)))

        repo = ContentRepo(session)
        user = message.from_user
        saved = 0
        for result in results:
            source_url = f"instagram://story/{result.external_id}"
            content = await repo.add(
                user_id=user.id,
                source_url=source_url,
                source_platform=SourcePlatform.instagram,
                external_id=result.external_id,
                file_path=result.file_path,
                media_type=result.media_type,
                content_category=result.content_category,
                description=result.description,
            )
            if content:
                saved += 1
            await _send_file_to_user(message, result.file_path, result.media_type, lang)

    status = t("dl_done_stories", lang, count=len(results))
    if saved:
        status += t("dl_done_stories_queued", lang, queued=saved)
    await progress_msg.edit_text(status)


@router.message(F.text.regexp(URL_PATTERN))
async def on_link(message: Message, session: AsyncSession, lang: str = "ru") -> None:
    url = message.text.strip() if message.text else ""
    platform = _detect_platform(url)

    if not platform:
        await message.answer(t("dl_unsupported", lang))
        return

    user = message.from_user
    if not user:
        return

    sem = _USER_SEMAPHORES[user.id]
    if sem.locked():
        await message.answer(t("dl_busy", lang))
        return

    user_repo = UserRepo(session)
    await user_repo.upsert(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=user.id in settings.admin_ids,
    )

    progress_msg = await message.answer(t("dl_downloading", lang))

    from app.services.downloaders.router import download_content

    is_admin: bool = user.id in settings.admin_ids
    async with sem:
        try:
            result = await download_content(
                url=url, platform=platform, user_id=user.id, session=session,
                is_admin=is_admin,
            )
        except Exception:
            logger.exception("Download failed: %s", url)
            await progress_msg.edit_text(t("dl_err", lang))
            return

    if result is None:
        await progress_msg.edit_text(t("dl_null", lang))
        return

    await progress_msg.edit_text(t("dl_sending", lang))

    await _send_file_to_user(message, result.file_path, result.media_type, lang)

    await progress_msg.edit_text(t("dl_done", lang))
    await user_repo.increment_downloads(user.id)
