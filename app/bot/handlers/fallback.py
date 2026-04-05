from __future__ import annotations

from aiogram import Router
from aiogram.types import Message

from app.i18n import t

router = Router(name="fallback")


@router.message()
async def on_unknown(message: Message, lang: str = "ru") -> None:
    await message.answer(t("help", lang))
