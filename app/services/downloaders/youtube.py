from __future__ import annotations

import asyncio
import logging
import os
import tempfile

from app.db.models import ContentCategory, MediaType
from app.settings import settings

from .base import BaseDownloader, DownloadResult

logger = logging.getLogger(__name__)


class YouTubeDownloader(BaseDownloader):
    async def download(self, url: str, user_id: int) -> DownloadResult:
        return await asyncio.to_thread(self._blocking_download, url, user_id)

    def _blocking_download(self, url: str, user_id: int) -> DownloadResult:
        import yt_dlp

        dest_dir = settings.get_media_dir("downloads", str(user_id), "youtube")

        with tempfile.TemporaryDirectory() as tmp:
            opts = {
                "format": "best[ext=mp4]/best",
                "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
                "max_filesize": 200 * 1024 * 1024,
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)

            if not info:
                raise RuntimeError("yt-dlp returned no info")

            video_id = info.get("id", "unknown")
            title = info.get("title", "")
            uploader = info.get("uploader", "")
            duration = info.get("duration", 0) or 0
            ext = info.get("ext", "mp4")

            if duration > settings.max_video_duration:
                raise ValueError(
                    f"Video too long: {duration}s > {settings.max_video_duration}s"
                )

            tmp_file = os.path.join(tmp, f"{video_id}.{ext}")
            if not os.path.exists(tmp_file):
                files = os.listdir(tmp)
                if files:
                    tmp_file = os.path.join(tmp, files[0])
                else:
                    raise FileNotFoundError("yt-dlp did not produce a file")

            final_path = str(dest_dir / f"{video_id}.mp4")
            if os.path.exists(final_path):
                raise FileExistsError(final_path)

            import shutil
            shutil.move(tmp_file, final_path)

        description = title if title else settings.default_caption
        if uploader:
            description += f"\n\nAuthor (YT): {uploader}"

        category = self.classify_video(duration)

        return DownloadResult(
            file_path=final_path,
            media_type=MediaType.video,
            content_category=category,
            external_id=video_id,
            description=description,
            duration_sec=duration,
        )
