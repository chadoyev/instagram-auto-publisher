from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.i18n import t

logger = logging.getLogger(__name__)

# Callback prefixes that must always pass through (subscription check button)
_ALWAYS_PASS_CB_PREFIXES = ("sub:check",)


class BotGuardMiddleware(BaseMiddleware):
    """
    Runs after AdminMiddleware and LangMiddleware so ``is_admin``, ``session``,
    and ``lang`` are already in data.

    For non-admin users:
    1. If bot_enabled=False → reply "bot unavailable" and stop.
    2. If subscription_required=True → check membership; if missing → show prompt and stop.
       Exception: /start command always passes through (user gets registered first).
       Exception: SubscriptionCB(action="check") always passes through.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        is_admin: bool = data.get("is_admin", False)
        if is_admin:
            return await handler(event, data)

        session = data.get("session")
        if session is None:
            return await handler(event, data)

        lang: str = data.get("lang", "ru")

        from app.db.repositories import SettingsRepo
        repo = SettingsRepo(session)
        bs = await repo.get_bot_settings()

        # ── 1. Bot enabled check ──────────────────────────────
        if not bs.bot_enabled:
            if isinstance(event, Message):
                await event.answer(t("guard_disabled_msg", lang))
            elif isinstance(event, CallbackQuery):
                await event.answer(t("guard_disabled_cb", lang), show_alert=True)
            return None

        # ── 2. Subscription check ─────────────────────────────
        if not bs.subscription_required:
            return await handler(event, data)

        # Always let /start through — start.py handles its own subscription prompt
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)

        # Always let the "I subscribed" callback through
        if isinstance(event, CallbackQuery) and event.data:
            for prefix in _ALWAYS_PASS_CB_PREFIXES:
                if event.data.startswith(prefix):
                    return await handler(event, data)

        channels = await repo.get_subscription_channels()
        if not channels:
            return await handler(event, data)

        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        bot = getattr(event, "bot", None)
        if bot is None:
            return await handler(event, data)

        from app.bot.handlers.subscription import _check_unsubscribed, build_subscription_prompt
        from app.bot.keyboards.inline import subscription_check_kb

        not_subscribed = await _check_unsubscribed(bot, user.id, channels)
        if not not_subscribed:
            return await handler(event, data)

        prompt_text = build_subscription_prompt(not_subscribed, lang)
        kb = subscription_check_kb(channels, lang)

        if isinstance(event, Message):
            await event.answer(prompt_text, reply_markup=kb)
        elif isinstance(event, CallbackQuery):
            await event.answer(t("guard_sub_required", lang), show_alert=True)
            if event.message:
                await event.message.answer(prompt_text, reply_markup=kb)
        return None
