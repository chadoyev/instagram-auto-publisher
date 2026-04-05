from __future__ import annotations

import asyncio
import logging
import os

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.bot.callbacks.data import InstagramCB, MenuCB
from app.bot.keyboards.inline import admin_menu_kb, back_to_menu, instagram_status_kb
from app.bot.states.admin import InstagramState
from app.i18n import t
from app.services.instagram_publisher import publisher
from app.settings import settings

logger = logging.getLogger(__name__)
router = Router(name="instagram_auth")

WG_CONFIG_PATH = "/app/wg_config/peer1/peer1.conf"


def _status_text(lang: str = "ru") -> str:
    username = settings.ig_username or t("ig_not_set", lang)
    session_status = t("ig_session_yes", lang) if publisher.has_session() else t("ig_session_no", lang)
    return t("ig_status_text", lang, username=username, session_status=session_status)


@router.callback_query(InstagramCB.filter(F.action == "status"))
async def on_instagram_status(
    call: CallbackQuery, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return
    if call.message:
        await call.message.edit_text(
            _status_text(lang),
            reply_markup=instagram_status_kb(publisher.has_session(), lang),
        )
    await call.answer()


@router.callback_query(InstagramCB.filter(F.action == "delete_session"))
async def on_delete_session(
    call: CallbackQuery, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return
    publisher.delete_session()
    if call.message:
        await call.message.edit_text(
            t("ig_session_deleted", lang) + _status_text(lang),
            reply_markup=instagram_status_kb(publisher.has_session(), lang),
        )
    await call.answer(t("ig_session_deleted_toast", lang))


@router.callback_query(InstagramCB.filter(F.action == "vpn_config"))
async def on_vpn_config(
    call: CallbackQuery, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return
    await call.answer()

    chat_id = call.message.chat.id if call.message else call.from_user.id

    if call.message:
        try:
            await call.message.delete()
        except Exception:
            pass

    if not os.path.exists(WG_CONFIG_PATH):
        await call.bot.send_message(chat_id, t("ig_vpn_not_found", lang))
        await call.bot.send_message(
            chat_id,
            _status_text(lang),
            reply_markup=instagram_status_kb(publisher.has_session(), lang),
        )
        return

    try:
        await call.bot.send_document(
            chat_id,
            FSInputFile(WG_CONFIG_PATH, filename="peer1.conf"),
            caption=t("ig_vpn_caption", lang),
        )
    except Exception as exc:
        await call.bot.send_message(chat_id, t("ig_vpn_send_err", lang, exc=exc))

    await call.bot.send_message(
        chat_id,
        _status_text(lang),
        reply_markup=instagram_status_kb(publisher.has_session(), lang),
    )


@router.callback_query(InstagramCB.filter(F.action == "login"))
async def on_login(
    call: CallbackQuery, state: FSMContext, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return

    await call.answer()
    progress_msg_id: int | None = None
    if call.message:
        await call.message.edit_text(t("ig_connecting", lang), reply_markup=None)
        progress_msg_id = call.message.message_id

    chat_id = call.message.chat.id if call.message else call.from_user.id
    asyncio.get_event_loop().create_task(
        _login_task(call.bot, chat_id, state, progress_msg_id, lang)
    )


async def _login_task(
    bot, chat_id: int, state: FSMContext, progress_msg_id: int | None = None, lang: str = "ru"
) -> None:
    async def _reply(text: str, reply_markup=None) -> None:
        if progress_msg_id:
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=progress_msg_id,
                    text=text,
                    reply_markup=reply_markup,
                )
                return
            except Exception:
                pass
        await bot.send_message(chat_id, text, reply_markup=reply_markup)

    login_task = asyncio.create_task(asyncio.to_thread(publisher._do_login))

    while not login_task.done():
        if publisher._awaiting_challenge:
            await state.set_state(InstagramState.waiting_challenge_code)
            if progress_msg_id:
                try:
                    await bot.delete_message(chat_id, progress_msg_id)
                except Exception:
                    pass
            await bot.send_message(chat_id, t("ig_challenge_prompt", lang))
            try:
                await login_task
                await state.clear()
                await bot.send_message(
                    chat_id,
                    t("ig_login_ok", lang) + _status_text(lang),
                    reply_markup=instagram_status_kb(publisher.has_session(), lang),
                )
            except Exception as exc:
                await state.clear()
                logger.exception("Instagram login failed after challenge")
                await bot.send_message(
                    chat_id,
                    t("ig_login_err", lang, exc=exc),
                    reply_markup=instagram_status_kb(publisher.has_session(), lang),
                )
            return
        await asyncio.sleep(0.3)

    try:
        login_task.result()
        await _reply(
            t("ig_login_ok", lang) + _status_text(lang),
            reply_markup=instagram_status_kb(publisher.has_session(), lang),
        )
    except Exception as exc:
        logger.exception("Instagram login failed")
        await _reply(
            t("ig_login_err", lang, exc=exc),
            reply_markup=instagram_status_kb(publisher.has_session(), lang),
        )


@router.message(InstagramState.waiting_challenge_code)
async def on_challenge_code(
    message: Message, state: FSMContext, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin or not message.text:
        return

    code = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass

    if not publisher._awaiting_challenge:
        await state.clear()
        await message.answer(
            t("ig_challenge_expired", lang),
            reply_markup=instagram_status_kb(publisher.has_session(), lang),
        )
        return

    publisher.provide_challenge_code(code)
    await message.answer(t("ig_code_sent", lang, code=code))
