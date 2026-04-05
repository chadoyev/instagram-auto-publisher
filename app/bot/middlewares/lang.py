from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.i18n import detect_lang


class LangMiddleware(BaseMiddleware):
    """
    Injects ``lang`` ('ru' or 'en') into handler data.

    Priority:
      1. Value stored in DB (User.language) — preserves manual admin override.
      2. Detected from Telegram user.language_code — used for new / unknown users.

    Requires DbSessionMiddleware to run first (so ``session`` is in data).
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        lang = "ru"  # safe default

        if user:
            session = data.get("session")
            if session:
                from app.db.repositories import UserRepo
                db_user = await UserRepo(session).get(user.id)
                if db_user:
                    lang = db_user.language or "ru"
                else:
                    lang = detect_lang(user.language_code)
            else:
                lang = detect_lang(user.language_code)

        data["lang"] = lang
        return await handler(event, data)
