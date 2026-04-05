from __future__ import annotations

import asyncio
import logging

import aiohttp
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks.data import LangCB, MenuCB, NavCB
from app.bot.keyboards.inline import admin_menu_kb, back_to_menu, category_picker_kb
from app.bot.states.admin import LogoUploadState
from app.db.repositories import ContentRepo, SettingsRepo, UserRepo
from app.i18n import t
from app.services.watermark import get_watermark_path
from app.settings import settings

logger = logging.getLogger(__name__)

router = Router(name="admin_menu")


# ── API status helpers ────────────────────────────────────────

async def _fetch_hiker_balance(lang: str = "ru") -> str:
    api_key = settings.hiker_api_key
    if not api_key:
        return t("hiker_key_missing", lang)
    try:
        url = "https://api.hikerapi.com/sys/balance"
        params = {"access_key": api_key}
        async with aiohttp.ClientSession() as cs:
            async with cs.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 404:
                    return t("hiker_endpoint_error", lang)
                resp.raise_for_status()
                data = await resp.json()
                requests = data.get("requests")
                rate = data.get("rate")
                currency = data.get("currency", "USD")
                amount = data.get("amount")
                if requests is not None and amount is not None:
                    req_str = f"{int(requests):,}".replace(",", " ")
                    amount_str = f"{float(amount):.2f}"
                    rate_str = t("hiker_tariff", lang, rate=rate, currency=currency) if rate is not None else ""
                    return f"✅ {req_str} req · ${amount_str}{rate_str}"
                balance = data.get("balance", data.get("credits"))
                if balance is not None:
                    return t("hiker_balance_raw", lang, balance=balance)
                parts = [f"{k}: {v}" for k, v in data.items()]
                return ("✅ " + ", ".join(parts)) if parts else "✅ OK"
    except Exception as exc:
        logger.debug("HikerAPI balance check failed: %s", exc)
        return f"❌ {exc}"


async def _fetch_tiktok_status(lang: str = "ru") -> str:
    try:
        url = f"{settings.tiktok_api_url}/docs"
        async with aiohttp.ClientSession() as cs:
            async with cs.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                return t("tiktok_status_ok", lang) if resp.status == 200 else f"⚠️ HTTP {resp.status}"
    except Exception as exc:
        logger.debug("TikTok API health check failed: %s", exc)
        return f"❌ {exc}"


# ── Main panel builder ────────────────────────────────────────

async def _build_admin_panel(session: AsyncSession, lang: str = "ru") -> tuple[str, object]:
    """Returns (text, keyboard) for the main admin panel."""
    repo = SettingsRepo(session)
    user_repo = UserRepo(session)
    content_repo = ContentRepo(session)

    (
        bot_settings,
        total_users,
        total_downloads,
        counts,
        queue_count,
        by_platform,
        hiker_status,
        tiktok_status,
    ) = await asyncio.gather(
        repo.get_bot_settings(),
        user_repo.total_users(),
        user_repo.total_downloads(),
        content_repo.count_pending_by_category(),
        content_repo.count_queued(),
        user_repo.downloads_by_platform(),
        _fetch_hiker_balance(lang),
        _fetch_tiktok_status(lang),
    )

    pending_total = sum(counts.values())

    bot_status_str = (
        t("admin_bot_enabled", lang) if bot_settings.bot_enabled
        else t("admin_bot_disabled", lang)
    )

    channels = await repo.get_subscription_channels()
    if bot_settings.subscription_required:
        sub_str = t("admin_sub_on", lang, n=len(channels))
    else:
        sub_str = t("admin_sub_off", lang)

    _TT = '<tg-emoji emoji-id="5327982530702359565">🎵</tg-emoji>'
    _IG = '<tg-emoji emoji-id="5319160079465857105">📸</tg-emoji>'
    _YT = '<tg-emoji emoji-id="5334942061349059951">▶️</tg-emoji>'
    platform_icons = {"tiktok": _TT, "instagram": _IG, "youtube": _YT, "other": "🔗"}
    platform_parts = [
        f"{platform_icons.get(k, '•')}{v}"
        for k, v in by_platform.items()
        if v > 0
    ]
    platform_line = "  " + " │ ".join(platform_parts) if platform_parts else f"  {t('admin_no_data', lang)}"

    text = (
        f"{t('admin_panel_header', lang)}\n\n"
        f"{t('admin_users_label', lang, n=total_users)}\n"
        f"{t('admin_downloads_label', lang, n=total_downloads)}\n"
        f"{platform_line}\n"
        f"{t('admin_blocked_label', lang, n=bot_settings.blocked_users_count)}\n\n"
        f"{t('admin_bot_status', lang, status=bot_status_str)}\n"
        f"{t('admin_sub_label', lang, status=sub_str)}\n\n"
        f"{t('admin_pending_label', lang, n=pending_total)}\n"
        f"{t('admin_queued_label', lang, n=queue_count)}\n\n"
        f"{t('admin_api_header', lang)}\n"
        f"  {t('admin_api_hiker', lang)}: {hiker_status}\n"
        f"  {t('admin_api_tiktok', lang)}: {tiktok_status}"
    )

    kb = admin_menu_kb(bot_enabled=bot_settings.bot_enabled, lang=lang)
    return text, kb


async def _send_admin_menu(target: Message | CallbackQuery, session: AsyncSession, lang: str = "ru") -> None:
    text, kb = await _build_admin_panel(session, lang)
    if isinstance(target, CallbackQuery) and target.message:
        try:
            await target.message.edit_text(text, reply_markup=kb)
        except Exception:
            await target.message.delete()
            await target.message.answer(text, reply_markup=kb)
        await target.answer()
    else:
        msg = target if isinstance(target, Message) else None
        if msg:
            await msg.answer(text, reply_markup=kb)


# ── Entry point ──────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession, is_admin: bool, lang: str = "ru") -> None:
    if not is_admin:
        return
    await _send_admin_menu(message, session, lang)


@router.callback_query(NavCB.filter(F.to == "admin_menu"))
async def nav_admin_menu(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    await state.clear()
    await _send_admin_menu(call, session, lang)


# ── Refresh ──────────────────────────────────────────────────

@router.callback_query(MenuCB.filter(F.action == "refresh"))
async def menu_refresh(
    call: CallbackQuery, session: AsyncSession, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return
    if call.message:
        await call.message.edit_text("🔄 ...")
    await asyncio.sleep(1)
    text, kb = await _build_admin_panel(session, lang)
    if call.message:
        await call.message.edit_text(text, reply_markup=kb)
    await call.answer()


# ── Toggle bot on/off ─────────────────────────────────────────

@router.callback_query(MenuCB.filter(F.action == "toggle_bot"))
async def menu_toggle_bot(
    call: CallbackQuery, session: AsyncSession, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return
    repo = SettingsRepo(session)
    bot_settings = await repo.get_bot_settings()
    new_state = not bot_settings.bot_enabled
    await repo.set_bot_enabled(new_state)
    status_label = (
        t("admin_bot_enabled", lang) if new_state else t("admin_bot_disabled", lang)
    )
    await call.answer(status_label, show_alert=True)
    text, kb = await _build_admin_panel(session, lang)
    if call.message:
        await call.message.edit_text(text, reply_markup=kb)


# ── Language toggle (admin only) ──────────────────────────────

@router.callback_query(LangCB.filter())
async def toggle_language(
    call: CallbackQuery,
    callback_data: LangCB,
    session: AsyncSession,
    is_admin: bool,
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return

    new_lang = callback_data.lang  # "ru" or "en"
    user_repo = UserRepo(session)
    await user_repo.set_language(call.from_user.id, new_lang)

    confirm_key = "lang_switched_en" if new_lang == "en" else "lang_switched_ru"
    await call.answer(t(confirm_key, new_lang), show_alert=True)

    # Re-render admin panel in the new language
    text, kb = await _build_admin_panel(session, new_lang)
    if call.message:
        try:
            await call.message.edit_text(text, reply_markup=kb)
        except Exception:
            pass


# ── Review ────────────────────────────────────────────────────

@router.callback_query(MenuCB.filter(F.action == "review"))
async def menu_review(
    call: CallbackQuery, session: AsyncSession, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return

    repo = ContentRepo(session)
    counts = await repo.count_pending_by_category()
    total = sum(counts.values())

    text = t("review_pending_header", lang, n=total)
    if call.message:
        await call.message.edit_text(text, reply_markup=category_picker_kb(counts, lang))
    await call.answer()


# ── Detailed stats ────────────────────────────────────────────

@router.callback_query(MenuCB.filter(F.action == "stats"))
async def menu_stats(
    call: CallbackQuery, session: AsyncSession, is_admin: bool, lang: str = "ru"
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return

    repo = ContentRepo(session)
    settings_repo = SettingsRepo(session)

    counts = await repo.count_pending_by_category()
    queue_by_target = await repo.count_queued_by_target()
    stats = await settings_repo.get_today_stats()

    _cat_rows = [
        ("📖", "cat_story", "story"),
        ("🎬", "cat_reels", "reels"),
        ("📷", "cat_post", "post"),
        ("📚", "cat_album", "album"),
        ("📺", "cat_igtv", "igtv"),
    ]
    _target_rows = [
        ("📖", "target_story_video", "story_video"),
        ("📖", "target_story_photo", "story_photo"),
        ("🎬", "target_reels", "reels"),
        ("📷", "target_post_video", "post_video"),
        ("📷", "target_post_photo", "post_photo"),
        ("📚", "target_album", "album"),
        ("📺", "target_igtv", "igtv"),
    ]
    published = {
        "story_video": stats.story_video, "story_photo": stats.story_photo,
        "reels": stats.reels, "post_video": stats.post_video,
        "post_photo": stats.post_photo, "album": stats.album, "igtv": stats.igtv,
    }

    lines = [t("stats_header", lang), "", t("stats_pending", lang)]
    for icon, i18n_key, count_key in _cat_rows:
        lines.append(f"  {icon} {t(i18n_key, lang)}: {counts.get(count_key, 0)}")
    lines.append(f"\n{t('stats_queue', lang)}")
    for icon, i18n_key, target_key in _target_rows:
        lines.append(f"  {icon} {t(i18n_key, lang)}: {queue_by_target.get(target_key, 0)}")
    lines.append(f"\n{t('stats_published', lang)}")
    for icon, i18n_key, target_key in _target_rows:
        lines.append(f"  {icon} {t(i18n_key, lang)}: {published[target_key]}")

    text = "\n".join(lines)
    if call.message:
        await call.message.edit_text(text, reply_markup=back_to_menu(lang))
    await call.answer()


# ── Logo upload ───────────────────────────────────────────────

@router.callback_query(MenuCB.filter(F.action == "logo"))
async def menu_logo(call: CallbackQuery, state: FSMContext, is_admin: bool, lang: str = "ru") -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return

    await state.set_state(LogoUploadState.waiting_file)
    await state.update_data(lang=lang)
    await call.answer()

    active_path = get_watermark_path()
    if call.message:
        await call.message.delete()

    if active_path and call.message:
        sent = await call.message.answer_photo(
            FSInputFile(active_path),
            caption=t("logo_caption_existing", lang),
            reply_markup=back_to_menu(lang),
        )
    elif call.message:
        sent = await call.message.answer(
            t("logo_caption_none", lang),
            reply_markup=back_to_menu(lang),
        )
    else:
        return

    await state.update_data(prompt_msg_id=sent.message_id, chat_id=sent.chat.id)


@router.message(LogoUploadState.waiting_file, F.photo | F.document)
async def receive_logo(message: Message, state: FSMContext, is_admin: bool, lang: str = "ru") -> None:
    if not is_admin:
        return

    bot = message.bot
    if bot is None:
        return

    logo_path = settings.media_root / "logo.png"
    logo_path.parent.mkdir(parents=True, exist_ok=True)

    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
    else:
        return

    tg_file = await bot.get_file(file_id)
    await bot.download_file(tg_file.file_path, destination=str(logo_path))  # type: ignore[arg-type]

    await message.delete()
    data = await state.get_data()
    lang = data.get("lang", "ru")
    if data.get("chat_id") and data.get("prompt_msg_id"):
        try:
            await bot.delete_message(data["chat_id"], data["prompt_msg_id"])
        except Exception:
            pass

    await state.clear()

    sent = await message.answer_photo(
        FSInputFile(str(logo_path)),
        caption=t("logo_updated", lang),
        reply_markup=back_to_menu(lang),
    )
