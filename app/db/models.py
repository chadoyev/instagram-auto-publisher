from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────

class SourcePlatform(str, enum.Enum):
    tiktok = "tiktok"
    instagram = "instagram"
    youtube = "youtube"
    other = "other"


class MediaType(str, enum.Enum):
    video = "video"
    photo = "photo"
    album = "album"


class ContentCategory(str, enum.Enum):
    story = "story"
    reels = "reels"
    post = "post"
    igtv = "igtv"
    album = "album"


class ContentStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    queued = "queued"
    publishing = "publishing"
    published = "published"
    failed = "failed"


class PublishTarget(str, enum.Enum):
    story_video = "story_video"
    story_photo = "story_photo"
    reels = "reels"
    post_video = "post_video"
    post_photo = "post_photo"
    album = "album"
    igtv = "igtv"


class QueueStatus(str, enum.Enum):
    queued = "queued"
    publishing = "publishing"
    published = "published"
    failed = "failed"


class SchedulePhase(str, enum.Enum):
    morning = "morning"
    day = "day"
    evening = "evening"


# ── Models ────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String(2), default="ru")
    downloads_count: Mapped[int] = mapped_column(Integer, default=0)
    approved_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    contents: Mapped[list[Content]] = relationship(back_populates="user")


class Content(Base):
    __tablename__ = "contents"
    __table_args__ = (
        UniqueConstraint("source_url", name="uq_content_source_url"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), index=True
    )
    source_url: Mapped[str] = mapped_column(Text)
    source_platform: Mapped[SourcePlatform] = mapped_column(
        Enum(SourcePlatform)
    )
    external_id: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(Text)
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType))
    content_category: Mapped[ContentCategory] = mapped_column(
        Enum(ContentCategory)
    )
    description: Mapped[str] = mapped_column(Text, default="")
    duration_sec: Mapped[float | None] = mapped_column(Float)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.pending_review, index=True
    )
    publish_target: Mapped[PublishTarget | None] = mapped_column(
        Enum(PublishTarget)
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="contents")
    queue_item: Mapped[PublishQueueItem | None] = relationship(
        back_populates="content"
    )


class PublishQueueItem(Base):
    __tablename__ = "publish_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contents.id"), unique=True
    )
    target_type: Mapped[PublishTarget] = mapped_column(Enum(PublishTarget))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_phase: Mapped[SchedulePhase | None] = mapped_column(
        Enum(SchedulePhase)
    )
    status: Mapped[QueueStatus] = mapped_column(
        Enum(QueueStatus), default=QueueStatus.queued, index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    content: Mapped[Content] = relationship(back_populates="queue_item")


class PublishSchedule(Base):
    __tablename__ = "publish_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phase: Mapped[SchedulePhase] = mapped_column(
        Enum(SchedulePhase), unique=True
    )
    time_start: Mapped[time] = mapped_column(Time)
    time_end: Mapped[time] = mapped_column(Time)
    content_sequence: Mapped[str] = mapped_column(
        Text, default=""
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stats_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    story_video: Mapped[int] = mapped_column(Integer, default=0)
    story_photo: Mapped[int] = mapped_column(Integer, default=0)
    reels: Mapped[int] = mapped_column(Integer, default=0)
    post_video: Mapped[int] = mapped_column(Integer, default=0)
    post_photo: Mapped[int] = mapped_column(Integer, default=0)
    album: Mapped[int] = mapped_column(Integer, default=0)
    igtv: Mapped[int] = mapped_column(Integer, default=0)


class BotSettings(Base):
    """Single-row table for global bot settings."""

    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, default=1
    )
    autopost_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    current_phase: Mapped[str] = mapped_column(String(20), default="")
    current_position: Mapped[int] = mapped_column(Integer, default=0)

    # Bot on/off for regular users
    bot_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # Count of users who blocked the bot (updated after broadcast)
    blocked_users_count: Mapped[int] = mapped_column(Integer, default=0)
    # Mandatory channel subscription
    subscription_required: Mapped[bool] = mapped_column(Boolean, default=False)
    # JSON: [{"id": "@channel", "title": "Title", "url": "https://t.me/channel"}]
    subscription_channels: Mapped[str] = mapped_column(Text, default="")
