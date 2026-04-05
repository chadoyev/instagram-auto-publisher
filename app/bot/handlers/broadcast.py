from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks.data import BroadcastCB, MenuCB
from app.bot.keyboards.inline import back_to_menu, broadcast_preview_kb, broadcast_report_kb
from app.bot.states.admin import BroadcastState
from app.db.repositories import SettingsRepo, UserRepo
from app.i18n import t

logger = logging.getLogger(__name__)
router = Router(name="broadcast")


# ── Entry point ──────────────────────────────────────────────

@router.callback_query(MenuCB.filter(F.action == "broadcast"))
async def menu_broadcast(
    call: CallbackQuery, state: FSMContext, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return

    if call.message:
        await call.message.edit_text(t("broadcast_header", lang), reply_markup=back_to_menu(lang))
    await state.update_data(
        bc_panel_msg_id=call.message.message_id if call.message else None,
        bc_preview_msg_id=None,
        bc_lang=lang,
    )
    await state.set_state(BroadcastState.waiting_message)
    await call.answer()


# ── Receive broadcast message ─────────────────────────────────

@router.message(BroadcastState.waiting_message)
async def broadcast_receive(
    message: Message, state: FSMContext, bot: Bot
) -> None:
    data = await state.get_data()
    lang: str = data.get("bc_lang", "ru")

    if not (message.text or message.photo or message.video or message.video_note):
        await message.answer(t("broadcast_unsupported", lang))
        return

    panel_msg_id = data.get("bc_panel_msg_id")
    chat_id = message.chat.id

    old_preview_id = data.get("bc_preview_msg_id")
    if old_preview_id:
        try:
            await bot.delete_message(chat_id, old_preview_id)
        except Exception:
            pass

    if panel_msg_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=panel_msg_id,
                text=t("broadcast_preview_header", lang),
            )
        except Exception:
            pass

    try:
        preview_msg = await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=chat_id,
            message_id=message.message_id,
            reply_markup=broadcast_preview_kb(lang),
        )
        preview_msg_id = preview_msg.message_id
    except Exception as exc:
        logger.error("Broadcast preview error: %s", exc)
        await message.answer(t("broadcast_save_err", lang))
        return

    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(
        bc_src_chat_id=chat_id,
        bc_preview_msg_id=preview_msg_id,
    )
    await state.set_state(None)


# ── Broadcast actions ─────────────────────────────────────────

@router.callback_query(BroadcastCB.filter(F.action == "send"))
async def broadcast_send(
    call: CallbackQuery, state: FSMContext, bot: Bot
) -> None:
    data = await state.get_data()
    lang: str = data.get("bc_lang", "ru")
    src_chat_id = data.get("bc_src_chat_id")
    preview_msg_id = data.get("bc_preview_msg_id")

    if not src_chat_id or not preview_msg_id:
        await call.answer(t("broadcast_no_data", lang), show_alert=True)
        return

    chat_id = call.message.chat.id
    panel_msg_id = data.get("bc_panel_msg_id")

    if panel_msg_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=panel_msg_id,
                text=t("broadcast_started_header", lang),
            )
        except Exception:
            pass

    await state.clear()
    await call.answer(t("broadcast_started", lang))

    asyncio.create_task(
        _run_broadcast(bot, chat_id, src_chat_id, preview_msg_id, panel_msg_id, lang)
    )


@router.callback_query(BroadcastCB.filter(F.action == "edit"))
async def broadcast_edit(
    call: CallbackQuery, state: FSMContext, bot: Bot
) -> None:
    data = await state.get_data()
    lang: str = data.get("bc_lang", "ru")
    chat_id = call.message.chat.id
    panel_msg_id = data.get("bc_panel_msg_id")
    preview_msg_id = data.get("bc_preview_msg_id")

    if preview_msg_id:
        try:
            await bot.delete_message(chat_id, preview_msg_id)
        except Exception:
            pass

    if panel_msg_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=panel_msg_id,
                text=t("broadcast_edit_header", lang),
                reply_markup=back_to_menu(lang),
            )
        except Exception:
            new_msg = await bot.send_message(
                chat_id, t("broadcast_edit_header", lang), reply_markup=back_to_menu(lang)
            )
            await state.update_data(bc_panel_msg_id=new_msg.message_id)

    await state.update_data(bc_preview_msg_id=None, bc_src_chat_id=None)
    await state.set_state(BroadcastState.waiting_message)
    await call.answer()


@router.callback_query(BroadcastCB.filter(F.action == "close_report"))
async def broadcast_close_report(call: CallbackQuery) -> None:
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer()


# ── Broadcast runner ──────────────────────────────────────────

async def _run_broadcast(
    bot: Bot,
    admin_chat_id: int,
    src_chat_id: int,
    src_message_id: int,
    panel_msg_id: int | None,
    lang: str = "ru",
) -> None:
    from app.db import async_session

    try:
        async with async_session() as s:
            user_ids = await UserRepo(s).get_all_ids()

        delivered = 0
        failed = 0

        for uid in user_ids:
            try:
                await bot.copy_message(
                    chat_id=uid,
                    from_chat_id=src_chat_id,
                    message_id=src_message_id,
                )
                delivered += 1
            except Exception:
                failed += 1
            await asyncio.sleep(0.05)

        try:
            await bot.delete_message(chat_id=src_chat_id, message_id=src_message_id)
        except Exception:
            pass

        async with async_session() as s:
            await SettingsRepo(s).update_blocked_count(failed)

        report = t("broadcast_done", lang, delivered=delivered, failed=failed)
        if panel_msg_id:
            try:
                await bot.edit_message_text(
                    chat_id=admin_chat_id,
                    message_id=panel_msg_id,
                    text=report,
                    reply_markup=broadcast_report_kb(lang),
                )
                return
            except Exception:
                pass
        await bot.send_message(admin_chat_id, report, reply_markup=broadcast_report_kb(lang))

    except Exception as exc:
        logger.error("Broadcast task error: %s", exc)
        try:
            await bot.send_message(admin_chat_id, t("broadcast_error", lang, exc=exc))
        except Exception:
            pass
