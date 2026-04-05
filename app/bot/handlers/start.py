from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram import Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import UserRepo
from app.i18n import detect_lang, t
from app.settings import settings

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, bot: Bot, lang: str = "ru") -> None:
    user = message.from_user
    if not user:
        return

    # Detect language from Telegram on first visit; DB may not have the user yet
    detected = detect_lang(user.language_code)

    repo = UserRepo(session)
    await repo.upsert(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=user.id in settings.admin_ids,
        language=detected,
    )

    # Use the freshly detected lang for the greeting (DB upsert above only sets it
    # on INSERT, so an existing user's manually overridden lang won't be touched)
    greeting_lang = lang if lang else detected

    # Check subscription requirement (skip for admins)
    if user.id not in settings.admin_ids:
        from app.bot.handlers.subscription import check_user_subscription, build_subscription_prompt
        from app.bot.keyboards.inline import subscription_check_kb

        not_subscribed = await check_user_subscription(bot, user.id, session)
        if not_subscribed:
            prompt = build_subscription_prompt(not_subscribed, greeting_lang)
            from app.db.repositories import SettingsRepo
            channels = await SettingsRepo(session).get_subscription_channels()
            await message.answer(prompt, reply_markup=subscription_check_kb(channels, greeting_lang))
            return

    await message.answer(t("greeting", greeting_lang))
