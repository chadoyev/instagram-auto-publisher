from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db import async_session
from app.db.models import PublishTarget, QueueStatus, SchedulePhase
from app.db.repositories import ContentRepo, SettingsRepo
from app.settings import settings

from .instagram_publisher import publisher

logger = logging.getLogger(__name__)

_bot_instance = None
_stop_event: asyncio.Event | None = None


async def _interruptible_sleep(seconds: float) -> bool:
    """
    Sleep for `seconds`. Returns True if completed normally,
    False if stop was signalled (scheduler shutting down).
    """
    global _stop_event
    if _stop_event is None or seconds <= 0:
        return True

    sleep_task = asyncio.ensure_future(asyncio.sleep(seconds))
    stop_task = asyncio.ensure_future(_stop_event.wait())

    try:
        done, pending = await asyncio.wait(
            {sleep_task, stop_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
    except asyncio.CancelledError:
        sleep_task.cancel()
        stop_task.cancel()
        return False

    for t in pending:
        t.cancel()
        try:
            await t
        except (asyncio.CancelledError, Exception):
            pass

    return stop_task not in done


def set_bot(bot) -> None:
    global _bot_instance
    _bot_instance = bot


async def _notify_admins(text: str) -> None:
    if not _bot_instance:
        return
    for admin_id in settings.admin_ids:
        try:
            await _bot_instance.send_message(admin_id, text)
        except Exception:
            logger.exception("Failed to notify admin %s", admin_id)

_scheduler: AsyncIOScheduler | None = None

TARGET_STAT_MAP = {
    PublishTarget.story_video: "story_video",
    PublishTarget.story_photo: "story_photo",
    PublishTarget.reels: "reels",
    PublishTarget.post_video: "post_video",
    PublishTarget.post_photo: "post_photo",
    PublishTarget.album: "album",
    PublishTarget.igtv: "igtv",
}


async def _publish_phase(phase: SchedulePhase) -> None:
    """Publish all content items for a given schedule phase."""
    logger.info("Starting publish phase: %s", phase.value)

    try:
        async with async_session() as session:
            settings_repo = SettingsRepo(session)
            schedule = await settings_repo.get_schedule(phase)
            if not schedule or not schedule.content_sequence:
                return

            content_repo = ContentRepo(session)
            targets = [t.strip() for t in schedule.content_sequence.split(",") if t.strip()]

            if not targets:
                return

            t_start = datetime.combine(datetime.today(), schedule.time_start)
            t_end = datetime.combine(datetime.today(), schedule.time_end)
            total_seconds = (t_end - t_start).total_seconds()
            interval = total_seconds / len(targets) if targets else 0

            for i, target_name in enumerate(targets):
                # Check if stop was requested before each item
                if _stop_event and _stop_event.is_set():
                    logger.info("Publish phase %s: stop requested, exiting", phase.value)
                    return

                try:
                    target = PublishTarget(target_name)
                except ValueError:
                    logger.warning("Unknown target in sequence: %s", target_name)
                    continue

                items = await content_repo.get_queued(target_type=target, limit=1)
                if not items:
                    logger.info("No queued content for %s", target_name)
                    continue

                item = items[0]
                content = item.content

                await content_repo.set_queue_status(item.id, QueueStatus.publishing)

                success = await publisher.publish(
                    file_path=content.file_path,
                    target=target,
                    caption=content.description,
                )

                if success:
                    await content_repo.set_queue_status(item.id, QueueStatus.published)
                    stat_field = TARGET_STAT_MAP.get(target)
                    if stat_field:
                        await settings_repo.increment_stat(stat_field)
                    logger.info("Published: %s -> %s", content.id, target_name)
                else:
                    await content_repo.set_queue_status(item.id, QueueStatus.failed)
                    logger.error("Failed to publish: %s", content.id)
                    await _notify_admins(
                        f"❌ <b>Ошибка публикации</b>\n\n"
                        f"Контент: <code>{content.id}</code>\n"
                        f"Тип: {target_name}\n"
                        f"Файл: {content.file_path}"
                    )

                if i < len(targets) - 1:
                    jitter = random.randint(-30, 30)
                    delay = max(60, int(interval) + jitter)
                    logger.info("Waiting %ds before next publish", delay)
                    if not await _interruptible_sleep(delay):
                        logger.info("Publish phase %s interrupted by stop", phase.value)
                        return

    except asyncio.CancelledError:
        logger.info("Publish phase %s cancelled (scheduler shutdown)", phase.value)
        return

    logger.info("Finished publish phase: %s", phase.value)


async def start_scheduler(session=None) -> None:
    global _scheduler, _stop_event

    if _scheduler and _scheduler.running:
        return

    _stop_event = asyncio.Event()
    _scheduler = AsyncIOScheduler()

    if session is None:
        async with async_session() as session:
            settings_repo = SettingsRepo(session)
            schedules = await settings_repo.get_schedules()
    else:
        settings_repo = SettingsRepo(session)
        schedules = await settings_repo.get_schedules()

    for sched in schedules:
        if not sched.is_active:
            continue
        _scheduler.add_job(
            _publish_phase,
            CronTrigger(
                hour=sched.time_start.hour,
                minute=sched.time_start.minute,
            ),
            args=[sched.phase],
            id=f"publish_{sched.phase.value}",
            replace_existing=True,
        )
        logger.info(
            "Scheduled %s at %s:%02d",
            sched.phase.value,
            sched.time_start.hour,
            sched.time_start.minute,
        )

    _scheduler.start()
    logger.info("Scheduler started")


async def stop_scheduler() -> None:
    global _scheduler, _stop_event
    # Signal any sleeping phase to wake up and exit cleanly
    if _stop_event:
        _stop_event.set()
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
    _stop_event = None
    logger.info("Scheduler stopped")
