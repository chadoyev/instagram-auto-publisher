from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix="menu"):
    action: str


class ReviewCB(CallbackData, prefix="rv"):
    """Callback for content review (tinder-like)."""
    action: str  # approve, reject, to_story, skip
    content_id: str  # UUID as hex string


class CategoryCB(CallbackData, prefix="cat"):
    """Choose review category."""
    category: str  # story, reels, igtv, post, album, all


class AutopostCB(CallbackData, prefix="ap"):
    action: str  # toggle, settings, back


class ScheduleCB(CallbackData, prefix="sch"):
    """Schedule settings."""
    action: str  # time, content
    phase: str   # morning, day, evening


class NavCB(CallbackData, prefix="nav"):
    """Generic navigation."""
    to: str


class InstagramCB(CallbackData, prefix="ig"):
    """Instagram auth panel actions."""
    action: str  # status, login, delete_session


class BroadcastCB(CallbackData, prefix="bc"):
    """Broadcast flow actions."""
    action: str  # send, edit, close_report


class SubscriptionCB(CallbackData, prefix="sub"):
    """Subscription management actions."""
    action: str  # manage, toggle, add, remove, check
    value: str = ""  # channel index for remove


class LangCB(CallbackData, prefix="lang"):
    """Admin language switch."""
    lang: str  # "ru" or "en"
