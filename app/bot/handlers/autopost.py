from __future__ import annotations

import logging
from datetime import datetime, time

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks.data import AutopostCB, MenuCB
from app.bot.keyboards.inline import (
    autopost_menu_kb,
    autopost_settings_kb,
    phase_picker_kb,
)
from app.db.repositories import ContentRepo, SettingsRepo
from app.i18n import t

logger = logging.getLogger(__name__)
router = Router(name="autopost")

_PHASE_KEYS = {"morning": "phase_morning", "day": "phase_day", "evening": "phase_evening"}

_TARGET_ICONS = {
    "story_video": "🎬",
    "story_photo": "📸",
    "reels": "▶️",
    "post_video": "🎥",
    "post_photo": "🖼",
    "album": "🗂",
    "igtv": "📺",
}

_TARGET_KEYS = {
    "story_video": "target_story_video",
    "story_photo": "target_story_photo",
    "reels": "target_reels",
    "post_video": "target_post_video",
    "post_photo": "target_post_photo",
    "album": "target_album",
    "igtv": "target_igtv",
}


def _fmt_sequence(seq: str, lang: str = "ru") -> str:
    if not seq:
        return f"  {t('autopost_sequence_empty', lang)}"
    parts = [t(_TARGET_KEYS.get(p.strip(), p.strip()), lang) for p in seq.split(",")]
    return "  " + " → ".join(parts)


def _is_active_phase(t_start: time, t_end: time, now: time) -> bool:
    if t_start <= t_end:
        return t_start <= now < t_end
    return now >= t_start or now < t_end


def _fmt_queue_breakdown(by_target: dict[str, int], lang: str = "ru") -> list[str]:
    if not by_target:
        return [f"  {t('autopost_queue_empty', lang)}"]
    lines = []
    for key, count in sorted(by_target.items(), key=lambda x: -x[1]):
        icon = _TARGET_ICONS.get(key, "•")
        label = t(_TARGET_KEYS.get(key, key), lang)
        lines.append(f"  {icon} {label}: <b>{count}</b>")
    return lines


async def _show_autopost_menu(
    call: CallbackQuery, session: AsyncSession, lang: str = "ru"
) -> None:
    repo = SettingsRepo(session)
    bot_settings = await repo.get_bot_settings()
    status = t("autopost_enabled", lang) if bot_settings.autopost_enabled else t("autopost_disabled", lang)

    schedules = await repo.get_schedules()
    content_repo = ContentRepo(session)
    total_queued = await content_repo.count_queued()
    by_target = await content_repo.count_queued_by_target()

    now_dt = datetime.now()
    now_time = now_dt.time()
    now_str = now_dt.strftime("%H:%M:%S")

    lines = [
        t("autopost_header", lang, status=status),
        t("autopost_server_time", lang, time=now_str),
        "",
        t("autopost_schedule_header", lang),
    ]

    for s in schedules:
        active = _is_active_phase(s.time_start, s.time_end, now_time)
        phase_label = t(_PHASE_KEYS.get(s.phase.value, s.phase.value), lang)
        prefix = "▶️ " if active else "   "
        header = f"{prefix}<b>{phase_label}</b> ({s.time_start:%H:%M}–{s.time_end:%H:%M})"
        if active:
            header += f"  {t('autopost_now', lang)}"
        lines.append(header)
        lines.append(_fmt_sequence(s.content_sequence, lang))
        lines.append("")

    lines.append(t("autopost_queue_total", lang, n=total_queued))
    lines.extend(_fmt_queue_breakdown(by_target, lang))

    text = "\n".join(lines)
    if call.message:
        await call.message.edit_text(
            text, reply_markup=autopost_menu_kb(bot_settings.autopost_enabled, lang=lang)
        )
    await call.answer()


@router.callback_query(MenuCB.filter(F.action == "autopost"))
async def menu_autopost(
    call: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    lang: str = "ru",
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return
    await _show_autopost_menu(call, session, lang)


@router.callback_query(AutopostCB.filter(F.action == "toggle"))
async def toggle_autopost(
    call: CallbackQuery,
    session: AsyncSession,
    is_admin: bool,
    lang: str = "ru",
) -> None:
    if not is_admin:
        return
    repo = SettingsRepo(session)
    bot_settings = await repo.get_bot_settings()
    new_state = not bot_settings.autopost_enabled
    await repo.set_autopost(new_state)

    if new_state:
        from app.services.scheduler import start_scheduler
        await start_scheduler(session)
        await call.answer(t("autopost_toggled_on", lang))
    else:
        from app.services.scheduler import stop_scheduler
        await stop_scheduler()
        await call.answer(t("autopost_toggled_off", lang))

    await _show_autopost_menu(call, session, lang)


@router.callback_query(AutopostCB.filter(F.action == "settings"))
async def autopost_settings(
    call: CallbackQuery, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        return
    if call.message:
        await call.message.edit_text(
            t("autopost_settings_header", lang),
            reply_markup=autopost_settings_kb(lang=lang),
        )
    await call.answer()


@router.callback_query(AutopostCB.filter(F.action == "time_settings"))
async def time_settings(call: CallbackQuery, is_admin: bool, lang: str = "ru") -> None:
    if not is_admin:
        return
    if call.message:
        await call.message.edit_text(
            t("autopost_pick_phase_time", lang),
            reply_markup=phase_picker_kb("time", lang=lang),
        )
    await call.answer()


@router.callback_query(AutopostCB.filter(F.action == "content_settings"))
async def content_settings(call: CallbackQuery, is_admin: bool, lang: str = "ru") -> None:
    if not is_admin:
        return
    if call.message:
        await call.message.edit_text(
            t("autopost_pick_phase_content", lang),
            reply_markup=phase_picker_kb("content", lang=lang),
        )
    await call.answer()
