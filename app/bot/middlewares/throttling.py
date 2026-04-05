from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from cachetools import TTLCache


class ThrottlingMiddleware(BaseMiddleware):
    """Simple per-user rate limiter (1 update per 0.5s)."""

    def __init__(self, rate_limit: float = 0.5) -> None:
        self._cache: TTLCache[int, bool] = TTLCache(
            maxsize=10_000, ttl=rate_limit
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user:
            if user.id in self._cache:
                return None
            self._cache[user.id] = True
        return await handler(event, data)
