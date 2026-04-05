from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callbacks.data import (
    AutopostCB,
    BroadcastCB,
    CategoryCB,
    InstagramCB,
    LangCB,
    MenuCB,
    NavCB,
    ReviewCB,
    ScheduleCB,
    SubscriptionCB,
)
from app.i18n import t


# ── Navigation ────────────────────────────────────────────────

def back_to_menu(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("btn_back_menu", lang),
            callback_data=NavCB(to="admin_menu").pack(),
        )]
    ])


# ── Admin main menu ──────────────────────────────────────────

def admin_menu_kb(bot_enabled: bool = True, lang: str = "ru") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t("btn_refresh", lang), callback_data=MenuCB(action="refresh"))
    b.button(text=t("btn_review", lang), callback_data=MenuCB(action="review"))
    b.button(text=t("btn_stats", lang), callback_data=MenuCB(action="stats"))
    b.button(text=t("btn_autopost", lang), callback_data=MenuCB(action="autopost"))
    b.button(text=t("btn_instagram", lang), callback_data=InstagramCB(action="status"))
    b.button(text=t("btn_logo", lang), callback_data=MenuCB(action="logo"))
    toggle_text = t("btn_bot_off", lang) if bot_enabled else t("btn_bot_on", lang)
    b.button(text=toggle_text, callback_data=MenuCB(action="toggle_bot"))
    b.button(text=t("btn_broadcast", lang), callback_data=MenuCB(action="broadcast"))
    b.button(text=t("btn_subscription", lang), callback_data=MenuCB(action="subscription"))
    new_lang = "en" if lang == "ru" else "ru"
    b.button(text=t("btn_lang_switch", lang), callback_data=LangCB(lang=new_lang))
    b.adjust(1, 2, 2, 2, 1, 1, 1)
    return b.as_markup()


def instagram_status_kb(has_session: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if has_session:
        b.button(text=t("btn_ig_relogin", lang), callback_data=InstagramCB(action="login"))
        b.button(text=t("btn_ig_delete_session", lang), callback_data=InstagramCB(action="delete_session"))
    else:
        b.button(text=t("btn_ig_login", lang), callback_data=InstagramCB(action="login"))
    b.button(text=t("btn_ig_vpn_config", lang), callback_data=InstagramCB(action="vpn_config"))
    b.button(text=t("btn_back_menu", lang), callback_data=NavCB(to="admin_menu"))
    b.adjust(1)
    return b.as_markup()


# ── Category picker ──────────────────────────────────────────

def category_picker_kb(counts: dict[str, int], lang: str = "ru") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    labels = {
        "story": t("cat_story", lang),
        "reels": t("cat_reels", lang),
        "igtv": t("cat_igtv", lang),
        "post": t("cat_post", lang),
        "album": t("cat_album", lang),
        "all": t("cat_all", lang),
    }
    for key, label in labels.items():
        cnt = counts.get(key, 0)
        total = sum(counts.values()) if key == "all" else cnt
        b.button(
            text=f"{label} ({total})",
            callback_data=CategoryCB(category=key),
        )
    b.button(text=t("btn_back_menu", lang), callback_data=NavCB(to="admin_menu"))
    b.adjust(2, 2, 1, 1)
    return b.as_markup()


# ── Review (tinder) ──────────────────────────────────────────

def review_kb(
    content_id: str, show_story_btn: bool = True, lang: str = "ru"
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅", callback_data=ReviewCB(action="approve", content_id=content_id))
    b.button(text="❌", callback_data=ReviewCB(action="reject", content_id=content_id))
    if show_story_btn:
        b.button(
            text=t("btn_to_story", lang),
            callback_data=ReviewCB(action="to_story", content_id=content_id),
        )
    b.button(text=t("btn_skip", lang), callback_data=ReviewCB(action="skip", content_id=content_id))
    b.button(text=t("btn_back_menu", lang), callback_data=NavCB(to="admin_menu"))
    if show_story_btn:
        b.adjust(2, 1, 1, 1)
    else:
        b.adjust(2, 1, 1)
    return b.as_markup()


# ── Autopost ─────────────────────────────────────────────────

def autopost_menu_kb(is_enabled: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    toggle_text = t("btn_autopost_off", lang) if is_enabled else t("btn_autopost_on", lang)
    b.button(text=toggle_text, callback_data=AutopostCB(action="toggle"))
    b.button(text=t("btn_autopost_settings", lang), callback_data=AutopostCB(action="settings"))
    b.button(text=t("btn_back_menu", lang), callback_data=NavCB(to="admin_menu"))
    b.adjust(1)
    return b.as_markup()


def autopost_settings_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t("btn_time_settings", lang), callback_data=AutopostCB(action="time_settings"))
    b.button(text=t("btn_content_settings", lang), callback_data=AutopostCB(action="content_settings"))
    b.button(text=t("btn_back", lang), callback_data=MenuCB(action="autopost"))
    b.adjust(1)
    return b.as_markup()


def phase_picker_kb(action: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """action = 'time' or 'content'"""
    b = InlineKeyboardBuilder()
    phases = [("morning", "phase_morning"), ("day", "phase_day"), ("evening", "phase_evening")]
    for phase, i18n_key in phases:
        b.button(text=t(i18n_key, lang), callback_data=ScheduleCB(action=action, phase=phase))
    b.button(text=t("btn_back", lang), callback_data=AutopostCB(action="settings"))
    b.adjust(3, 1)
    return b.as_markup()


# ── Broadcast ─────────────────────────────────────────────────

def broadcast_preview_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t("btn_broadcast_send", lang), callback_data=BroadcastCB(action="send"))
    b.button(text=t("btn_broadcast_edit", lang), callback_data=BroadcastCB(action="edit"))
    b.button(text=t("btn_back_menu", lang), callback_data=NavCB(to="admin_menu"))
    b.adjust(2, 1)
    return b.as_markup()


def broadcast_report_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("btn_back_menu", lang),
            callback_data=NavCB(to="admin_menu").pack(),
        )]
    ])


# ── Subscription ──────────────────────────────────────────────

def subscription_manage_kb(
    channels: list[dict], required: bool, lang: str = "ru"
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    toggle_text = t("btn_sub_toggle_off", lang) if required else t("btn_sub_toggle_on", lang)
    b.button(text=toggle_text, callback_data=SubscriptionCB(action="toggle"))
    for i, ch in enumerate(channels):
        b.button(
            text=f"❌ {ch['title']}",
            callback_data=SubscriptionCB(action="remove", value=str(i)),
        )
    b.button(text=t("btn_sub_add", lang), callback_data=SubscriptionCB(action="add"))
    b.button(text=t("btn_back_menu", lang), callback_data=NavCB(to="admin_menu"))
    b.adjust(1)
    return b.as_markup()


def subscription_check_kb(channels: list[dict], lang: str = "ru") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for ch in channels:
        b.button(text=f"👉 {ch['title']}", url=ch["url"])
    b.button(text=t("sub_btn_check", lang), callback_data=SubscriptionCB(action="check"))
    b.adjust(1)
    return b.as_markup()
