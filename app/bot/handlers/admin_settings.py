from __future__ import annotations

import re
from datetime import datetime, time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks.data import AutopostCB, ScheduleCB
from app.bot.keyboards.inline import autopost_settings_kb, back_to_menu
from app.bot.states.admin import ScheduleContentState, ScheduleTimeState
from app.db.models import SchedulePhase
from app.db.repositories import SettingsRepo
from app.i18n import t

router = Router(name="admin_settings")

_PHASE_KEYS = {"morning": "phase_morning", "day": "phase_day", "evening": "phase_evening"}

VALID_TARGETS = {
    "story_video", "story_photo", "reels",
    "post_video", "post_photo", "album", "igtv",
}

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})$")


# ── Time settings ─────────────────────────────────────────────

@router.callback_query(ScheduleCB.filter(F.action == "time"))
async def ask_time(
    call: CallbackQuery,
    callback_data: ScheduleCB,
    state: FSMContext,
    is_admin: bool,
    lang: str = "ru",
) -> None:
    if not is_admin:
        return
    phase = callback_data.phase
    await state.set_state(ScheduleTimeState.waiting_input)

    msg_id = call.message.message_id if call.message else None
    chat_id = call.message.chat.id if call.message else None
    await state.update_data(phase=phase, prompt_msg_id=msg_id, chat_id=chat_id, lang=lang)

    now = datetime.now().strftime("%H:%M:%S")
    phase_label = t(_PHASE_KEYS.get(phase, phase), lang)
    if call.message:
        await call.message.edit_text(
            t("settings_time_prompt", lang, phase=phase_label, now=now),
            reply_markup=back_to_menu(lang),
        )
    await call.answer()


@router.message(ScheduleTimeState.waiting_input)
async def receive_time(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool,
) -> None:
    if not is_admin or not message.text:
        return

    data = await state.get_data()
    lang: str = data.get("lang", "ru")
    bot = message.bot

    async def _edit_prompt(text: str, kb=None) -> None:
        if bot and data.get("chat_id") and data.get("prompt_msg_id"):
            try:
                await bot.edit_message_text(
                    text,
                    chat_id=data["chat_id"],
                    message_id=data["prompt_msg_id"],
                    reply_markup=kb,
                    parse_mode="HTML",
                )
            except Exception:
                pass

    await message.delete()

    phase_label = t(_PHASE_KEYS.get(data["phase"], data["phase"]), lang)
    match = TIME_RE.match(message.text.strip())
    if not match:
        await _edit_prompt(
            t("settings_time_invalid", lang, phase=phase_label),
            back_to_menu(lang),
        )
        return

    h1, m1, h2, m2 = (int(x) for x in match.groups())
    try:
        t_start = time(h1, m1)
        t_end = time(h2, m2)
    except ValueError:
        await _edit_prompt(
            t("settings_time_bad", lang, phase=phase_label),
            back_to_menu(lang),
        )
        return

    phase = SchedulePhase(data["phase"])
    repo = SettingsRepo(session)
    await repo.update_schedule_time(phase, t_start, t_end)

    await state.clear()
    await _edit_prompt(
        t("settings_time_saved", lang, phase=phase_label, range=f"{t_start:%H:%M}–{t_end:%H:%M}"),
        autopost_settings_kb(lang),
    )


# ── Content sequence settings ────────────────────────────────

@router.callback_query(ScheduleCB.filter(F.action == "content"))
async def ask_content(
    call: CallbackQuery,
    callback_data: ScheduleCB,
    state: FSMContext,
    is_admin: bool,
    lang: str = "ru",
) -> None:
    if not is_admin:
        return
    phase = callback_data.phase
    await state.set_state(ScheduleContentState.waiting_input)

    msg_id = call.message.message_id if call.message else None
    chat_id = call.message.chat.id if call.message else None
    await state.update_data(phase=phase, prompt_msg_id=msg_id, chat_id=chat_id, lang=lang)

    phase_label = t(_PHASE_KEYS.get(phase, phase), lang)
    if call.message:
        await call.message.edit_text(
            f"{phase_label}\n\n{t('settings_content_prompt', lang)}",
            reply_markup=back_to_menu(lang),
        )
    await call.answer()


@router.message(ScheduleContentState.waiting_input)
async def receive_content(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool,
) -> None:
    if not is_admin or not message.text:
        return

    data = await state.get_data()
    lang: str = data.get("lang", "ru")
    bot = message.bot

    async def _edit_prompt(text: str, kb=None) -> None:
        if bot and data.get("chat_id") and data.get("prompt_msg_id"):
            try:
                await bot.edit_message_text(
                    text,
                    chat_id=data["chat_id"],
                    message_id=data["prompt_msg_id"],
                    reply_markup=kb,
                    parse_mode="HTML",
                )
            except Exception:
                pass

    await message.delete()

    phase_label = t(_PHASE_KEYS.get(data["phase"], data["phase"]), lang)
    parts = [p.strip().lower() for p in message.text.split(",") if p.strip()]
    invalid = [p for p in parts if p not in VALID_TARGETS]
    if invalid:
        await _edit_prompt(
            t("settings_content_invalid", lang,
              phase=phase_label,
              keys=", ".join(invalid),
              prompt=t("settings_content_prompt", lang)),
            back_to_menu(lang),
        )
        return

    sequence = ",".join(parts)
    phase = SchedulePhase(data["phase"])

    repo = SettingsRepo(session)
    await repo.update_schedule_content(phase, sequence)

    await state.clear()
    await _edit_prompt(
        t("settings_content_saved", lang, phase=phase_label, seq=sequence),
        autopost_settings_kb(lang),
    )
