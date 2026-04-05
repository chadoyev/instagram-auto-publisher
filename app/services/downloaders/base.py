from __future__ import annotations

import abc
from dataclasses import dataclass

from app.db.models import ContentCategory, MediaType


@dataclass
class DownloadResult:
    file_path: str
    media_type: MediaType
    content_category: ContentCategory
    external_id: str
    description: str
    duration_sec: float | None = None


class BaseDownloader(abc.ABC):
    @abc.abstractmethod
    async def download(self, url: str, user_id: int) -> DownloadResult:
        """Download content and return metadata. Raises on failure."""

    @staticmethod
    def classify_video(duration: float) -> ContentCategory:
        if duration < 15:
            return ContentCategory.story
        if duration < 90:
            return ContentCategory.reels
        return ContentCategory.igtv
