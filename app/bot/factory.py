from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from app.settings import settings

logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    return Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    from .middlewares.db_session import DbSessionMiddleware
    from .middlewares.auth import AdminMiddleware
    from .middlewares.throttling import ThrottlingMiddleware
    from .middlewares.lang import LangMiddleware
    from .middlewares.bot_guard import BotGuardMiddleware

    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(ThrottlingMiddleware())
    dp.message.outer_middleware(AdminMiddleware())
    dp.callback_query.outer_middleware(AdminMiddleware())
    # LangMiddleware runs after AdminMiddleware (needs session + event_from_user)
    dp.message.outer_middleware(LangMiddleware())
    dp.callback_query.outer_middleware(LangMiddleware())
    # BotGuard runs last — needs is_admin, session, and lang
    dp.message.outer_middleware(BotGuardMiddleware())
    dp.callback_query.outer_middleware(BotGuardMiddleware())

    from .handlers import (
        start, download, admin_menu, content_review,
        autopost, admin_settings, instagram_auth, fallback,
    )
    from .handlers import broadcast, subscription

    dp.include_routers(
        start.router,
        admin_menu.router,
        content_review.router,
        autopost.router,
        admin_settings.router,
        instagram_auth.router,
        broadcast.router,
        subscription.router,
        download.router,
        fallback.router,  # must be last — catches everything else
    )

    return dp
