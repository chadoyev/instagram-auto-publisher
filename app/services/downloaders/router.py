from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Content, SourcePlatform
from app.db.repositories import ContentRepo

from .base import BaseDownloader, DownloadResult
from .instagram import InstagramDownloader
from .tiktok import TikTokDownloader
from .youtube import YouTubeDownloader

logger = logging.getLogger(__name__)

_DOWNLOADERS: dict[str, type[BaseDownloader]] = {
    "tiktok": TikTokDownloader,
    "instagram": InstagramDownloader,
    "youtube": YouTubeDownloader,
}


async def download_content(
    *,
    url: str,
    platform: str,
    user_id: int,
    session: AsyncSession,
    is_admin: bool = False,
) -> Content | None:
    """
    Download content from the given URL, persist metadata to DB.
    Returns the Content ORM object.
    For regular users: on duplicate returns existing Content (so file can be resent).
    For admins: new content is added to review queue; duplicates are not re-added.
    """
    downloader_cls = _DOWNLOADERS.get(platform)
    if not downloader_cls:
        raise ValueError(f"Unsupported platform: {platform}")

    repo = ContentRepo(session)

    downloader = downloader_cls()
    try:
        result: DownloadResult = await downloader.download(url, user_id)
    except FileExistsError:
        logger.info("Duplicate content (file exists): %s", url)
        return await repo.get_by_source_url(url)

    content = await repo.add(
        user_id=user_id,
        source_url=url,
        source_platform=SourcePlatform(platform),
        external_id=result.external_id,
        file_path=result.file_path,
        media_type=result.media_type,
        content_category=result.content_category,
        description=result.description,
        duration_sec=result.duration_sec,
    )

    if content is None:
        # URL already in DB — return existing record so user can get the file
        return await repo.get_by_source_url(url)

    return content
