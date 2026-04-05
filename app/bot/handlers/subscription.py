from __future__ import annotations

import logging
import re

from aiogram import F, Router
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks.data import MenuCB, SubscriptionCB
from app.bot.keyboards.inline import (
    back_to_menu,
    subscription_check_kb,
    subscription_manage_kb,
)
from app.bot.states.admin import SubscriptionAddState
from app.db.repositories import SettingsRepo
from app.i18n import t

logger = logging.getLogger(__name__)
router = Router(name="subscription")

# Regex for @username or t.me links
_TG_USERNAME_RE = re.compile(r"^@?([\w]{4,})$")
_TG_LINK_RE = re.compile(r"(?:https?://)?t\.me/([\w]+)", re.IGNORECASE)


def _parse_channel_input(text: str) -> str | None:
    """Extract channel username from user input. Returns '@username' or None."""
    text = text.strip()
    m = _TG_LINK_RE.search(text)
    if m:
        return f"@{m.group(1)}"
    m = _TG_USERNAME_RE.match(text)
    if m:
        return f"@{m.group(1)}"
    return None


# ── Admin: manage subscriptions ───────────────────────────────

@router.callback_query(MenuCB.filter(F.action == "subscription"))
async def menu_subscription(
    call: CallbackQuery, session: AsyncSession, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return
    await _show_subscription_manage(call, session, lang)
    await call.answer()


async def _show_subscription_manage(
    call: CallbackQuery, session: AsyncSession, lang: str = "ru"
) -> None:
    repo = SettingsRepo(session)
    bs = await repo.get_bot_settings()
    channels = await repo.get_subscription_channels()

    status = (
        t("sub_manage_status_on", lang) if bs.subscription_required
        else t("sub_manage_status_off", lang)
    )
    if channels:
        ch_lines = "\n".join(
            f"  {i + 1}. {ch['title']} ({ch['id']})" for i, ch in enumerate(channels)
        )
    else:
        ch_lines = f"  {t('sub_manage_no_channels', lang)}"

    text = (
        f"{t('sub_manage_title', lang)}\n\n"
        f"{t('sub_manage_status', lang, status=status)}\n\n"
        f"{t('sub_manage_channels', lang)}\n{ch_lines}\n\n"
        f"{t('sub_manage_note', lang)}"
    )
    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=subscription_manage_kb(channels, bs.subscription_required, lang),
        )


@router.callback_query(SubscriptionCB.filter(F.action == "toggle"))
async def subscription_toggle(
    call: CallbackQuery, session: AsyncSession, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return
    repo = SettingsRepo(session)
    bs = await repo.get_bot_settings()
    new_val = not bs.subscription_required
    await repo.set_subscription_required(new_val)
    toast = t("sub_toggle_on_toast", lang) if new_val else t("sub_toggle_off_toast", lang)
    await call.answer(toast, show_alert=True)
    await _show_subscription_manage(call, session, lang)


@router.callback_query(SubscriptionCB.filter(F.action == "add"))
async def subscription_add_prompt(
    call: CallbackQuery, state: FSMContext, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return
    if call.message:
        await call.message.edit_text(t("sub_add_header", lang), reply_markup=back_to_menu(lang))
    await state.update_data(
        sub_panel_msg_id=call.message.message_id if call.message else None,
        sub_lang=lang,
    )
    await state.set_state(SubscriptionAddState.waiting_input)
    await call.answer()


@router.message(SubscriptionAddState.waiting_input, F.text)
async def subscription_add_receive(
    message: Message, state: FSMContext, bot: Bot, session: AsyncSession, is_admin: bool
) -> None:
    if not is_admin:
        await state.clear()
        return

    data = await state.get_data()
    lang: str = data.get("sub_lang", "ru")
    panel_msg_id = data.get("sub_panel_msg_id")

    username = _parse_channel_input(message.text or "")
    await message.delete()

    if not username:
        if panel_msg_id:
            try:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=panel_msg_id,
                    text=t("sub_add_invalid", lang),
                    reply_markup=back_to_menu(lang),
                )
            except Exception:
                pass
        return

    # Resolve channel info via Telegram API
    try:
        chat = await bot.get_chat(username)
        title = chat.title or chat.username or username
        if chat.username:
            url = f"https://t.me/{chat.username}"
        else:
            url = f"https://t.me/c/{str(chat.id).replace('-100', '')}"
        channel_id = username
    except Exception as exc:
        logger.warning("Cannot resolve channel %s: %s", username, exc)
        if panel_msg_id:
            try:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=panel_msg_id,
                    text=t("sub_add_resolve_err", lang, username=username),
                    reply_markup=back_to_menu(lang),
                )
            except Exception:
                pass
        return

    repo = SettingsRepo(session)
    channels = await repo.get_subscription_channels()

    if any(ch["id"] == channel_id for ch in channels):
        if panel_msg_id:
            try:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=panel_msg_id,
                    text=t("sub_already_added", lang, title=title),
                    reply_markup=back_to_menu(lang),
                )
            except Exception:
                pass
        await state.clear()
        return

    channels.append({"id": channel_id, "title": title, "url": url})
    await repo.save_subscription_channels(channels)
    await state.clear()

    bs = await repo.get_bot_settings()
    status = (
        t("sub_manage_status_on", lang) if bs.subscription_required
        else t("sub_manage_status_off", lang)
    )
    ch_lines = "\n".join(
        f"  {i + 1}. {ch['title']} ({ch['id']})" for i, ch in enumerate(channels)
    )
    text = (
        f"{t('sub_added_ok', lang, title=title)}\n\n"
        f"{t('sub_manage_title', lang)}\n\n"
        f"{t('sub_manage_status', lang, status=status)}\n\n"
        f"{t('sub_manage_channels', lang)}\n{ch_lines}"
    )
    if panel_msg_id:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=panel_msg_id,
                text=text,
                reply_markup=subscription_manage_kb(channels, bs.subscription_required, lang),
            )
        except Exception:
            await message.answer(
                text,
                reply_markup=subscription_manage_kb(channels, bs.subscription_required, lang),
            )


@router.callback_query(SubscriptionCB.filter(F.action == "remove"))
async def subscription_remove(
    call: CallbackQuery,
    callback_data: SubscriptionCB,
    session: AsyncSession,
    is_admin: bool,
    lang: str = "ru",
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return

    repo = SettingsRepo(session)
    channels = await repo.get_subscription_channels()

    try:
        idx = int(callback_data.value)
        removed = channels.pop(idx)
    except (ValueError, IndexError):
        await call.answer(t("sub_remove_not_found", lang), show_alert=True)
        return

    await repo.save_subscription_channels(channels)
    await call.answer(t("sub_remove_done", lang, title=removed["title"]))
    await _show_subscription_manage(call, session, lang)


# ── User: subscription check ──────────────────────────────────

@router.callback_query(SubscriptionCB.filter(F.action == "check"))
async def subscription_check(
    call: CallbackQuery, session: AsyncSession, bot: Bot, lang: str = "ru"
) -> None:
    """User pressed 'I subscribed' — recheck their membership."""
    repo = SettingsRepo(session)
    bs = await repo.get_bot_settings()

    if not bs.subscription_required:
        if call.message:
            await call.message.delete()
        await call.answer(t("sub_done_ok", lang))
        await bot.send_message(call.from_user.id, t("greeting", lang))
        return

    channels = await repo.get_subscription_channels()
    if not channels:
        if call.message:
            await call.message.delete()
        await call.answer(t("sub_done", lang))
        await bot.send_message(call.from_user.id, t("greeting", lang))
        return

    user_id = call.from_user.id
    not_subscribed = await _check_unsubscribed(bot, user_id, channels)

    if not_subscribed:
        ch_names = ", ".join(ch["title"] for ch in not_subscribed)
        await call.answer(t("sub_not_yet", lang, ch_names=ch_names), show_alert=True)
    else:
        if call.message:
            await call.message.delete()
        await call.answer(t("sub_confirmed", lang))
        await bot.send_message(call.from_user.id, t("greeting", lang))


async def _check_unsubscribed(bot: Bot, user_id: int, channels: list[dict]) -> list[dict]:
    """Returns list of channels the user is NOT subscribed to."""
    not_subscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["id"], user_id)
            if member.status in ("left", "kicked", "banned"):
                not_subscribed.append(ch)
        except Exception as exc:
            logger.debug("Cannot check membership for %s in %s: %s", user_id, ch["id"], exc)
    return not_subscribed


async def check_user_subscription(
    bot: Bot, user_id: int, session: AsyncSession
) -> list[dict]:
    """Returns channels the user needs to subscribe to. Empty list = all good."""
    repo = SettingsRepo(session)
    bs = await repo.get_bot_settings()
    if not bs.subscription_required:
        return []
    channels = await repo.get_subscription_channels()
    if not channels:
        return []
    return await _check_unsubscribed(bot, user_id, channels)


def build_subscription_prompt(not_subscribed: list[dict], lang: str = "ru") -> str:
    ch_list = "\n".join(f"  • {ch['title']}" for ch in not_subscribed)
    return t("sub_prompt", lang, ch_list=ch_list)
