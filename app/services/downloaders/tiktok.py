from __future__ import annotations

import asyncio
import logging
import os

import aiohttp

from app.db.models import ContentCategory, MediaType
from app.settings import settings

from .base import BaseDownloader, DownloadResult

logger = logging.getLogger(__name__)


class TikTokDownloader(BaseDownloader):
    _MAX_RETRIES = 3
    _RETRY_DELAY = 2

    async def _fetch_video_data(self, url: str) -> dict:
        api_url = f"{settings.tiktok_api_url}/api/hybrid/video_data"
        params = {"url": url}
        headers = {
            "user-agent": (
                "Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 "
                "Mobile Safari/537.36"
            )
        }
        last_exc: BaseException | None = None
        for attempt in range(1, self._MAX_RETRIES + 1):
            try:
                async with aiohttp.ClientSession() as cs:
                    async with cs.get(
                        api_url,
                        params=params,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        resp.raise_for_status()
                        return await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_exc = exc
                logger.warning(
                    "TikTok API attempt %d/%d failed: %s",
                    attempt, self._MAX_RETRIES, exc,
                )
                if attempt < self._MAX_RETRIES:
                    await asyncio.sleep(self._RETRY_DELAY * attempt)
        raise last_exc  # type: ignore[misc]

    async def download(self, url: str, user_id: int) -> DownloadResult:
        data = await self._fetch_video_data(url)

        video_data = data["data"]
        video_id = str(video_data["aweme_id"])
        video_url = video_data["video"]["play_addr"]["url_list"][0]
        author = video_data.get("author", {}).get("unique_id", "") or video_data.get("author", {}).get("nickname", "")
        desc = video_data.get("desc", "")
        duration = video_data.get("video", {}).get("duration", 0) / 1000

        description = desc if desc else settings.default_caption
        if author:
            description += f"\n\nAuthor (TikTok): {author}"

        category = self.classify_video(duration)
        dest_dir = settings.get_media_dir("downloads", str(user_id), "tiktok")
        file_path = str(dest_dir / f"{video_id}.mp4")

        if os.path.exists(file_path):
            raise FileExistsError(file_path)

        async with aiohttp.ClientSession() as cs:
            async with cs.get(video_url, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                resp.raise_for_status()
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(65536):
                        f.write(chunk)

        return DownloadResult(
            file_path=file_path,
            media_type=MediaType.video,
            content_category=category,
            external_id=video_id,
            description=description,
            duration_sec=duration,
        )

