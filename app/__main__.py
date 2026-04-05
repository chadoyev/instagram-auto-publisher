from __future__ import annotations

import asyncio
import logging
import signal
import sys

from app.settings import settings


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


async def main() -> None:
    _setup_logging()
    logger = logging.getLogger("app")

    logger.info("Instagram Auto Publisher v3.0")
    logger.info("Mode: %s", settings.bot_mode)

    from app.db import init_db, async_session, engine
    from app.db.repositories import SettingsRepo

    logger.info("Initializing database...")
    await init_db()

    async with async_session() as session:
        repo = SettingsRepo(session)
        await repo.ensure_defaults()
        bot_settings = await repo.get_bot_settings()
        if bot_settings.autopost_enabled:
            from app.services.scheduler import start_scheduler
            await start_scheduler(session)
            logger.info("Autopost scheduler resumed")

    from app.bot.factory import create_bot, create_dispatcher
    from app.services.scheduler import set_bot, stop_scheduler

    bot = create_bot()
    dp = create_dispatcher()
    set_bot(bot)

    async def _shutdown() -> None:
        logger.info("Shutting down...")
        await stop_scheduler()
        await bot.session.close()
        await engine.dispose()
        logger.info("Cleanup complete")

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(_shutdown()))
        except NotImplementedError:
            pass

    try:
        if settings.bot_mode == "webhook":
            from app.web.webhook import run_webhook

            await run_webhook(dp, bot)
        else:
            logger.info("Starting long-polling...")
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
    finally:
        await _shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
