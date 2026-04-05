from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.settings import settings


class AdminMiddleware(BaseMiddleware):
    """Injects `is_admin` flag into handler data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        data["is_admin"] = (
            user is not None and user.id in settings.admin_ids
        )
        return await handler(event, data)
