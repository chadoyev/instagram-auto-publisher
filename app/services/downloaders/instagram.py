from __future__ import annotations

import asyncio
import logging
import os

import aiohttp

from app.db.models import ContentCategory, MediaType
from app.settings import settings

from .base import BaseDownloader, DownloadResult

logger = logging.getLogger(__name__)


class InstagramDownloader(BaseDownloader):
    def __init__(self) -> None:
        self.api_key = settings.hiker_api_key

    async def download(self, url: str, user_id: int) -> DownloadResult:
        if "stories" in url:
            return await self._download_story(url, user_id)
        return await self._download_post(url, user_id)

    async def _download_story(self, url: str, user_id: int) -> DownloadResult:
        api_url = "https://api.hikerapi.com/v1/story/by/url"
        params = {"url": url, "access_key": self.api_key}

        async with aiohttp.ClientSession() as cs:
            async with cs.get(api_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                data = await resp.json()

        pk = str(data["pk"])
        media_type_code = data["media_type"]

        dest_dir = settings.get_media_dir("downloads", str(user_id), "instagram")

        if media_type_code == 2:
            file_path = str(dest_dir / f"{pk}.mp4")
            m_type = MediaType.video
        else:
            file_path = str(dest_dir / f"{pk}.jpg")
            m_type = MediaType.photo

        if os.path.exists(file_path):
            raise FileExistsError(file_path)

        download_url = f"https://api.hikerapi.com/v1/story/download?id={data['id']}&access_key={self.api_key}"
        async with aiohttp.ClientSession() as cs:
            async with cs.get(download_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                resp.raise_for_status()
                content = await resp.read()

        await asyncio.to_thread(self._write, file_path, content)

        return DownloadResult(
            file_path=file_path,
            media_type=m_type,
            content_category=ContentCategory.story,
            external_id=pk,
            description=settings.default_caption,
        )

    async def _download_post(self, url: str, user_id: int) -> DownloadResult:
        api_url = "https://api.hikerapi.com/v1/media/by/url"
        params = {"url": url, "access_key": self.api_key}

        async with aiohttp.ClientSession() as cs:
            async with cs.get(api_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                data = await resp.json()

        pk = str(data["pk"])
        media_type_code = data["media_type"]
        product_type = data.get("product_type", "feed")
        caption = data.get("caption_text", "") or ""
        author = data.get("user", {}).get("username", "")

        description = caption if caption else settings.default_caption
        if author:
            description += f"\n\nAuthor (IG): @{author}"

        dest_dir = settings.get_media_dir("downloads", str(user_id), "instagram")

        if media_type_code == 2:
            video_url = data["video_url"]
            file_path = str(dest_dir / f"{pk}.mp4")

            if os.path.exists(file_path):
                raise FileExistsError(file_path)

            async with aiohttp.ClientSession() as cs:
                async with cs.get(video_url, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    resp.raise_for_status()
                    content = await resp.read()

            await asyncio.to_thread(self._write, file_path, content)

            if product_type == "clips":
                category = ContentCategory.reels
            elif product_type == "igtv":
                category = ContentCategory.igtv
            else:
                category = ContentCategory.post

            return DownloadResult(
                file_path=file_path,
                media_type=MediaType.video,
                content_category=category,
                external_id=pk,
                description=description,
            )

        elif media_type_code == 1:
            image_url = data["thumbnail_url"]
            file_path = str(dest_dir / f"{pk}.jpg")

            if os.path.exists(file_path):
                raise FileExistsError(file_path)

            async with aiohttp.ClientSession() as cs:
                async with cs.get(image_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    resp.raise_for_status()
                    content = await resp.read()

            await asyncio.to_thread(self._write, file_path, content)

            return DownloadResult(
                file_path=file_path,
                media_type=MediaType.photo,
                content_category=ContentCategory.post,
                external_id=pk,
                description=description,
            )

        elif media_type_code == 8:
            album_dir = settings.get_media_dir(
                "downloads", str(user_id), "instagram", f"album_{pk}"
            )
            album_path = str(album_dir)

            resources = data.get("resources", [])
            for idx, src in enumerate(resources):
                if src["media_type"] == 2:
                    dl_url = src["video_url"]
                    fpath = str(album_dir / f"{idx}.mp4")
                else:
                    dl_url = src["thumbnail_url"]
                    fpath = str(album_dir / f"{idx}.jpg")

                async with aiohttp.ClientSession() as cs:
                    async with cs.get(dl_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                        resp.raise_for_status()
                        content = await resp.read()
                await asyncio.to_thread(self._write, fpath, content)

            return DownloadResult(
                file_path=album_path,
                media_type=MediaType.album,
                content_category=ContentCategory.album,
                external_id=pk,
                description=description,
            )

        raise ValueError(f"Unknown media_type: {media_type_code}")

    async def fetch_user_stories(
        self, username: str, user_id: int, index: int | None = None
    ) -> list[DownloadResult]:
        """Download active stories for an Instagram user via v2 API.

        Args:
            username: Instagram username (without @).
            user_id:  Telegram user ID (for storage path).
            index:    1-based story number; None means all stories.

        Returns list of DownloadResult (may be empty if user has no active stories).
        Raises IndexError if index is out of range.
        """
        api_url = "https://api.hikerapi.com/v2/user/stories/by/username"
        params = {"username": username, "access_key": self.api_key}

        async with aiohttp.ClientSession() as cs:
            async with cs.get(api_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                data = await resp.json()

        stories = self._extract_story_items(data)

        if not stories:
            return []

        if index is not None:
            if index < 1 or index > len(stories):
                raise IndexError(
                    f"Сторис #{index} не найдена. Активных сторисов: {len(stories)}"
                )
            stories = [stories[index - 1]]

        dest_dir = settings.get_media_dir("downloads", str(user_id), "instagram", "stories")
        results: list[DownloadResult] = []

        for story in stories:
            result = await self._download_story_item(story, dest_dir)
            if result:
                results.append(result)

        return results

    @staticmethod
    def _extract_story_items(data: object) -> list:
        """Parse v2 story response — handles multiple wrapping formats."""
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return []
        # {"items": [...]}
        if isinstance(data.get("items"), list):
            return data["items"]
        # {"reel": {"items": [...]}}
        reel = data.get("reel")
        if isinstance(reel, dict) and isinstance(reel.get("items"), list):
            return reel["items"]
        # {"reels": {"<user_id>": {"items": [...]}}}
        reels = data.get("reels")
        if isinstance(reels, dict):
            for v in reels.values():
                if isinstance(v, dict) and isinstance(v.get("items"), list):
                    return v["items"]
        # fallback — first list value found
        for v in data.values():
            if isinstance(v, list) and v:
                return v
        return []

    async def _download_story_item(
        self, story: dict, dest_dir
    ) -> DownloadResult | None:
        pk = str(story.get("pk") or story.get("id") or "")
        if not pk:
            logger.warning("Story item has no pk/id, skipping")
            return None

        media_type_code = story.get("media_type", 1)

        if media_type_code == 2:
            file_path = str(dest_dir / f"{pk}.mp4")
            m_type = MediaType.video
            dl_url = story.get("video_url") or story.get("video_versions", [{}])[0].get("url")
        else:
            file_path = str(dest_dir / f"{pk}.jpg")
            m_type = MediaType.photo
            dl_url = (
                story.get("thumbnail_url")
                or story.get("image_url")
                or self._best_image_url(story)
            )

        if not dl_url:
            logger.warning("No media URL for story %s, skipping", pk)
            return None

        if not os.path.exists(file_path):
            async with aiohttp.ClientSession() as cs:
                async with cs.get(dl_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    resp.raise_for_status()
                    content = await resp.read()
            await asyncio.to_thread(self._write, file_path, content)

        return DownloadResult(
            file_path=file_path,
            media_type=m_type,
            content_category=ContentCategory.story,
            external_id=pk,
            description=settings.default_caption,
        )

    @staticmethod
    def _best_image_url(story: dict) -> str | None:
        """Extract the best available image URL from image_versions2."""
        candidates = story.get("image_versions2", {}).get("candidates", [])
        if candidates:
            return candidates[0].get("url")
        return None

    @staticmethod
    def _write(path: str, data: bytes) -> None:
        with open(path, "wb") as f:
            f.write(data)
