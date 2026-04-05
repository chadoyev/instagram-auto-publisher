from __future__ import annotations

import json
from datetime import date, time

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    BotSettings,
    DailyStats,
    PublishSchedule,
    SchedulePhase,
)

DEFAULT_SCHEDULES = [
    {
        "phase": SchedulePhase.morning,
        "time_start": time(8, 0),
        "time_end": time(12, 0),
        "content_sequence": "story_video,story_photo,post_photo",
    },
    {
        "phase": SchedulePhase.day,
        "time_start": time(12, 0),
        "time_end": time(18, 0),
        "content_sequence": "post_video,reels,post_photo",
    },
    {
        "phase": SchedulePhase.evening,
        "time_start": time(18, 0),
        "time_end": time(23, 0),
        "content_sequence": "story_video,album,reels",
    },
]


class SettingsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    # ── Bot settings (single-row) ──

    async def ensure_defaults(self) -> None:
        result = await self.s.execute(select(BotSettings))
        if not result.scalar_one_or_none():
            self.s.add(BotSettings(id=1))
            await self.s.commit()

        for sched in DEFAULT_SCHEDULES:
            stmt = (
                pg_insert(PublishSchedule)
                .values(**sched)
                .on_conflict_do_nothing(index_elements=[PublishSchedule.phase])
            )
            await self.s.execute(stmt)
        await self.s.commit()

    async def get_bot_settings(self) -> BotSettings:
        result = await self.s.execute(select(BotSettings))
        row = result.scalar_one_or_none()
        if not row:
            await self.ensure_defaults()
            result = await self.s.execute(select(BotSettings))
            row = result.scalar_one()
        return row

    async def set_autopost(self, enabled: bool) -> None:
        await self.s.execute(
            update(BotSettings).where(BotSettings.id == 1).values(
                autopost_enabled=enabled
            )
        )
        await self.s.commit()

    async def update_position(self, phase: str, position: int) -> None:
        await self.s.execute(
            update(BotSettings).where(BotSettings.id == 1).values(
                current_phase=phase, current_position=position
            )
        )
        await self.s.commit()

    async def set_bot_enabled(self, enabled: bool) -> None:
        await self.s.execute(
            update(BotSettings).where(BotSettings.id == 1).values(bot_enabled=enabled)
        )
        await self.s.commit()

    async def update_blocked_count(self, count: int) -> None:
        await self.s.execute(
            update(BotSettings).where(BotSettings.id == 1).values(blocked_users_count=count)
        )
        await self.s.commit()

    async def set_subscription_required(self, required: bool) -> None:
        await self.s.execute(
            update(BotSettings).where(BotSettings.id == 1).values(subscription_required=required)
        )
        await self.s.commit()

    async def get_subscription_channels(self) -> list[dict]:
        bs = await self.get_bot_settings()
        if not bs.subscription_channels:
            return []
        try:
            return json.loads(bs.subscription_channels)
        except Exception:
            return []

    async def save_subscription_channels(self, channels: list[dict]) -> None:
        raw = json.dumps(channels, ensure_ascii=False)
        await self.s.execute(
            update(BotSettings).where(BotSettings.id == 1).values(subscription_channels=raw)
        )
        await self.s.commit()

    # ── Schedules ──

    async def get_schedules(self) -> list[PublishSchedule]:
        result = await self.s.execute(
            select(PublishSchedule).order_by(PublishSchedule.phase)
        )
        return list(result.scalars().all())

    async def get_schedule(self, phase: SchedulePhase) -> PublishSchedule | None:
        result = await self.s.execute(
            select(PublishSchedule).where(PublishSchedule.phase == phase)
        )
        return result.scalar_one_or_none()

    async def update_schedule_time(
        self, phase: SchedulePhase, start: time, end: time
    ) -> None:
        await self.s.execute(
            update(PublishSchedule)
            .where(PublishSchedule.phase == phase)
            .values(time_start=start, time_end=end)
        )
        await self.s.commit()

    async def update_schedule_content(
        self, phase: SchedulePhase, sequence: str
    ) -> None:
        await self.s.execute(
            update(PublishSchedule)
            .where(PublishSchedule.phase == phase)
            .values(content_sequence=sequence)
        )
        await self.s.commit()

    # ── Daily stats ──

    async def get_today_stats(self) -> DailyStats:
        today = date.today()
        result = await self.s.execute(
            select(DailyStats).where(DailyStats.stats_date == today)
        )
        row = result.scalar_one_or_none()
        if not row:
            row = DailyStats(stats_date=today)
            self.s.add(row)
            await self.s.commit()
            await self.s.refresh(row)
        return row

    async def increment_stat(self, field_name: str) -> None:
        today = date.today()
        stats = await self.get_today_stats()
        current = getattr(stats, field_name, 0)
        await self.s.execute(
            update(DailyStats)
            .where(DailyStats.stats_date == today)
            .values(**{field_name: current + 1})
        )
        await self.s.commit()
