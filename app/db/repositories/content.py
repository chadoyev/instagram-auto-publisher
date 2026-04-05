from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Content,
    ContentCategory,
    ContentStatus,
    MediaType,
    PublishQueueItem,
    PublishTarget,
    QueueStatus,
    SourcePlatform,
)


class ContentRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get_by_source_url(self, source_url: str) -> Content | None:
        result = await self.s.execute(
            select(Content).where(Content.source_url == source_url)
        )
        return result.scalar_one_or_none()

    async def add(
        self,
        *,
        user_id: int,
        source_url: str,
        source_platform: SourcePlatform,
        external_id: str | None,
        file_path: str,
        media_type: MediaType,
        content_category: ContentCategory,
        description: str = "",
        duration_sec: float | None = None,
        publish_target: PublishTarget | None = None,
    ) -> Content | None:
        """Add content. Returns None if source_url already exists."""
        if await self.get_by_source_url(source_url):
            return None

        item = Content(
            user_id=user_id,
            source_url=source_url,
            source_platform=source_platform,
            external_id=external_id,
            file_path=file_path,
            media_type=media_type,
            content_category=content_category,
            description=description,
            duration_sec=duration_sec,
            publish_target=publish_target,
        )
        self.s.add(item)
        await self.s.commit()
        await self.s.refresh(item)
        return item

    async def get(self, content_id: uuid.UUID) -> Content | None:
        return await self.s.get(Content, content_id)

    async def get_pending_review(
        self,
        category: ContentCategory | None = None,
        limit: int = 1,
        exclude_ids: list[uuid.UUID] | None = None,
    ) -> Sequence[Content]:
        q = select(Content).where(
            Content.status == ContentStatus.pending_review
        )
        if category:
            q = q.where(Content.content_category == category)
        if exclude_ids:
            q = q.where(~Content.id.in_(exclude_ids))
        q = q.order_by(Content.created_at.asc()).limit(limit)
        result = await self.s.execute(q)
        return result.scalars().all()

    async def count_pending(
        self, category: ContentCategory | None = None
    ) -> int:
        q = select(func.count()).select_from(Content).where(
            Content.status == ContentStatus.pending_review
        )
        if category:
            q = q.where(Content.content_category == category)
        result = await self.s.execute(q)
        return result.scalar_one()

    async def count_pending_by_category(self) -> dict[str, int]:
        q = (
            select(Content.content_category, func.count())
            .where(Content.status == ContentStatus.pending_review)
            .group_by(Content.content_category)
        )
        result = await self.s.execute(q)
        return {row[0].value: row[1] for row in result.all()}

    async def set_status(
        self, content_id: uuid.UUID, status: ContentStatus
    ) -> None:
        await self.s.execute(
            update(Content)
            .where(Content.id == content_id)
            .values(status=status)
        )
        await self.s.commit()

    async def update_description(
        self, content_id: uuid.UUID, description: str
    ) -> None:
        await self.s.execute(
            update(Content)
            .where(Content.id == content_id)
            .values(description=description)
        )
        await self.s.commit()

    async def approve(
        self, content_id: uuid.UUID, target: PublishTarget
    ) -> None:
        await self.s.execute(
            update(Content)
            .where(Content.id == content_id)
            .values(
                status=ContentStatus.approved,
                publish_target=target,
            )
        )
        await self.s.commit()

    async def reject(self, content_id: uuid.UUID) -> None:
        await self.s.execute(
            update(Content)
            .where(Content.id == content_id)
            .values(status=ContentStatus.rejected)
        )
        await self.s.commit()

    async def delete_content(self, content_id: uuid.UUID) -> None:
        await self.s.execute(
            delete(Content).where(Content.id == content_id)
        )
        await self.s.commit()

    # ── Queue ──

    async def enqueue(
        self,
        content_id: uuid.UUID,
        target_type: PublishTarget,
    ) -> PublishQueueItem:
        item = PublishQueueItem(
            content_id=content_id,
            target_type=target_type,
        )
        self.s.add(item)
        await self.s.commit()
        await self.s.refresh(item)
        return item

    async def get_queued(
        self, target_type: PublishTarget | None = None, limit: int = 1
    ) -> Sequence[PublishQueueItem]:
        q = (
            select(PublishQueueItem)
            .options(selectinload(PublishQueueItem.content))
            .where(PublishQueueItem.status == QueueStatus.queued)
        )
        if target_type:
            q = q.where(PublishQueueItem.target_type == target_type)
        q = q.order_by(
            PublishQueueItem.priority.desc(),
            PublishQueueItem.created_at.asc(),
        ).limit(limit)
        result = await self.s.execute(q)
        return result.scalars().all()

    async def count_queued(
        self, target_type: PublishTarget | None = None
    ) -> int:
        q = select(func.count()).select_from(PublishQueueItem).where(
            PublishQueueItem.status == QueueStatus.queued
        )
        if target_type:
            q = q.where(PublishQueueItem.target_type == target_type)
        result = await self.s.execute(q)
        return result.scalar_one()

    async def count_queued_by_target(self) -> dict[str, int]:
        q = (
            select(PublishQueueItem.target_type, func.count())
            .where(PublishQueueItem.status == QueueStatus.queued)
            .group_by(PublishQueueItem.target_type)
        )
        result = await self.s.execute(q)
        return {row[0].value: row[1] for row in result.all()}

    async def set_queue_status(
        self, queue_id: uuid.UUID, status: QueueStatus
    ) -> None:
        await self.s.execute(
            update(PublishQueueItem)
            .where(PublishQueueItem.id == queue_id)
            .values(status=status)
        )
        await self.s.commit()
