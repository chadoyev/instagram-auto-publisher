from __future__ import annotations

import logging
import os
import uuid as uuid_mod

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks.data import CategoryCB, ReviewCB, NavCB
from app.bot.keyboards.inline import back_to_menu, review_kb
from app.bot.states.admin import ReviewState
from app.db.models import ContentCategory, ContentStatus, MediaType, PublishTarget
from app.db.repositories import ContentRepo, UserRepo
from app.i18n import t

logger = logging.getLogger(__name__)
router = Router(name="content_review")

CATEGORY_MAP: dict[str, ContentCategory | None] = {
    "story": ContentCategory.story,
    "reels": ContentCategory.reels,
    "igtv": ContentCategory.igtv,
    "post": ContentCategory.post,
    "album": ContentCategory.album,
    "all": None,
}

TARGET_MAP = {
    (ContentCategory.story, MediaType.video): PublishTarget.story_video,
    (ContentCategory.story, MediaType.photo): PublishTarget.story_photo,
    (ContentCategory.reels, MediaType.video): PublishTarget.reels,
    (ContentCategory.igtv, MediaType.video): PublishTarget.igtv,
    (ContentCategory.post, MediaType.video): PublishTarget.post_video,
    (ContentCategory.post, MediaType.photo): PublishTarget.post_photo,
    (ContentCategory.album, MediaType.album): PublishTarget.album,
}

# Maps ContentCategory → i18n key for the label used in review captions
_CAT_LABEL_KEYS: dict[ContentCategory, str] = {
    ContentCategory.story: "cat_label_story",
    ContentCategory.reels: "cat_label_reels",
    ContentCategory.igtv: "cat_label_igtv",
    ContentCategory.post: "cat_label_post",
    ContentCategory.album: "cat_label_album",
}


def _parse_uuid(value: str) -> uuid_mod.UUID:
    return uuid_mod.UUID(value)


def _resolve_target(content) -> PublishTarget:
    key = (content.content_category, content.media_type)
    return TARGET_MAP.get(key, PublishTarget.reels)


def _build_caption(content, lang: str = "ru") -> str:
    desc = content.description or t("review_no_desc", lang)
    cat_key = _CAT_LABEL_KEYS.get(content.content_category, "?")
    cat_label = t(cat_key, lang) if cat_key != "?" else "?"
    return (
        t("review_caption_type", lang, cat=cat_label) + "\n"
        + t("review_caption_desc", lang, desc=str(desc)[:800])
    )


async def _send_album_group(
    bot, chat_id: int, album_dir: str, caption: str, kb, lang: str = "ru"
) -> tuple[Message | None, list[int]]:
    """Send album files as a media group + separate keyboard message."""
    files = sorted(f for f in os.listdir(album_dir) if not f.startswith("."))
    if not files:
        await bot.send_message(chat_id, t("review_album_empty", lang), reply_markup=back_to_menu(lang))
        return None, []

    media_group = []
    for i, fname in enumerate(files[:10]):
        fpath = os.path.join(album_dir, fname)
        ext = os.path.splitext(fname)[1].lower()
        is_first = i == 0
        if ext in (".mp4", ".mov", ".avi", ".mkv"):
            media_group.append(
                InputMediaVideo(
                    media=FSInputFile(fpath),
                    caption=caption if is_first else None,
                    parse_mode="HTML" if is_first else None,
                )
            )
        else:
            media_group.append(
                InputMediaPhoto(
                    media=FSInputFile(fpath),
                    caption=caption if is_first else None,
                    parse_mode="HTML" if is_first else None,
                )
            )

    sent_group = await bot.send_media_group(chat_id, media_group)
    group_ids = [m.message_id for m in sent_group]
    kb_msg = await bot.send_message(chat_id, t("review_rate_album", lang), reply_markup=kb)
    return kb_msg, group_ids


async def _send_content(
    call: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    category: str,
    lang: str = "ru",
) -> None:
    data = await state.get_data()
    skipped_ids_str: list[str] = data.get("skipped_ids", [])
    skipped_uuids = [uuid_mod.UUID(s) for s in skipped_ids_str] if skipped_ids_str else None
    prev_album_group_ids: list[int] = data.get("album_group_ids", [])

    repo = ContentRepo(session)
    cat_enum = CATEGORY_MAP.get(category)
    items = await repo.get_pending_review(category=cat_enum, limit=1, exclude_ids=skipped_uuids)

    if not items and skipped_ids_str:
        skipped_uuids = None
        await state.update_data(skipped_ids=[])
        items = await repo.get_pending_review(category=cat_enum, limit=1)

    chat_id = call.message.chat.id if call.message else call.from_user.id

    if not items:
        if call.message:
            try:
                await call.message.delete()
            except Exception:
                pass
            for mid in prev_album_group_ids:
                try:
                    await call.bot.delete_message(chat_id, mid)
                except Exception:
                    pass
        await state.update_data(album_group_ids=[])
        await call.bot.send_message(
            chat_id,
            t("review_no_content", lang),
            reply_markup=back_to_menu(lang),
        )
        await call.answer()
        return

    content = items[0]
    show_story_btn = content.content_category not in (
        ContentCategory.story, ContentCategory.album
    )

    cap = _build_caption(content, lang)

    await state.set_state(ReviewState.viewing)
    await state.update_data(content_id=str(content.id), category=category)

    kb = review_kb(str(content.id), show_story_btn=show_story_btn, lang=lang)

    if call.message:
        try:
            await call.message.delete()
        except Exception:
            pass
        for mid in prev_album_group_ids:
            try:
                await call.bot.delete_message(chat_id, mid)
            except Exception:
                pass

    await state.update_data(album_group_ids=[])

    if not os.path.exists(content.file_path):
        logger.warning("File missing: %s", content.file_path)
        await repo.set_status(content.id, ContentStatus.rejected)
        await call.bot.send_message(
            chat_id, t("review_file_missing_skip", lang), reply_markup=back_to_menu(lang)
        )
        return

    sent_msg: Message | None = None
    album_group_ids: list[int] = []
    try:
        if content.media_type == MediaType.video:
            sent_msg = await call.bot.send_video(
                chat_id, FSInputFile(content.file_path), caption=cap, reply_markup=kb,
            )
        elif content.media_type == MediaType.photo:
            sent_msg = await call.bot.send_photo(
                chat_id, FSInputFile(content.file_path), caption=cap, reply_markup=kb,
            )
        elif content.media_type == MediaType.album:
            sent_msg, album_group_ids = await _send_album_group(
                call.bot, chat_id, content.file_path, cap, kb, lang
            )
    except Exception:
        logger.exception("Failed to send content %s", content.id)
        await call.bot.send_message(
            chat_id, t("review_send_failed", lang), reply_markup=back_to_menu(lang)
        )

    if sent_msg:
        await state.update_data(
            review_message_id=sent_msg.message_id,
            album_group_ids=album_group_ids,
        )

    await call.answer()


async def _resend_current_content(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    lang: str = "ru",
) -> None:
    data = await state.get_data()
    content_id_str = data.get("content_id")
    review_message_id = data.get("review_message_id")
    album_group_ids: list[int] = data.get("album_group_ids", [])
    if not content_id_str:
        return

    repo = ContentRepo(session)
    content = await repo.get(_parse_uuid(content_id_str))
    if not content:
        await message.answer(t("review_file_missing", lang), reply_markup=back_to_menu(lang))
        return

    show_story_btn = content.content_category not in (
        ContentCategory.story, ContentCategory.album
    )
    cap = _build_caption(content, lang)
    kb = review_kb(str(content.id), show_story_btn=show_story_btn, lang=lang)
    chat_id = message.chat.id

    if content.media_type in (MediaType.video, MediaType.photo) and review_message_id:
        try:
            await message.bot.edit_message_caption(
                chat_id=chat_id,
                message_id=review_message_id,
                caption=cap,
                reply_markup=kb,
                parse_mode="HTML",
            )
            return
        except Exception:
            logger.warning("Failed to edit caption for %s, falling back to resend", content.id)

    if not os.path.exists(content.file_path):
        await message.answer(t("review_file_missing", lang), reply_markup=back_to_menu(lang))
        return

    if review_message_id:
        try:
            await message.bot.delete_message(chat_id, review_message_id)
        except Exception:
            pass
    for mid in album_group_ids:
        try:
            await message.bot.delete_message(chat_id, mid)
        except Exception:
            pass
    await state.update_data(album_group_ids=[])

    sent_msg: Message | None = None
    new_album_group_ids: list[int] = []
    try:
        if content.media_type == MediaType.video:
            sent_msg = await message.answer_video(
                FSInputFile(content.file_path), caption=cap, reply_markup=kb
            )
        elif content.media_type == MediaType.photo:
            sent_msg = await message.answer_photo(
                FSInputFile(content.file_path), caption=cap, reply_markup=kb
            )
        elif content.media_type == MediaType.album:
            sent_msg, new_album_group_ids = await _send_album_group(
                message.bot, chat_id, content.file_path, cap, kb, lang
            )
    except Exception:
        logger.exception("Failed to resend content %s", content.id)
        await message.answer(t("review_send_failed", lang), reply_markup=back_to_menu(lang))

    if sent_msg:
        await state.update_data(
            review_message_id=sent_msg.message_id,
            album_group_ids=new_album_group_ids,
        )


# ── Category selection ────────────────────────────────────────

@router.callback_query(CategoryCB.filter())
async def on_category(
    call: CallbackQuery,
    callback_data: CategoryCB,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool,
    lang: str = "ru",
) -> None:
    if not is_admin:
        await call.answer("⛔", show_alert=True)
        return
    await state.update_data(skipped_ids=[])
    await _send_content(call, session, state, callback_data.category, lang)


# ── Review actions ────────────────────────────────────────────

@router.callback_query(ReviewCB.filter(F.action == "approve"))
async def on_approve(
    call: CallbackQuery,
    callback_data: ReviewCB,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool,
    lang: str = "ru",
) -> None:
    if not is_admin:
        return

    repo = ContentRepo(session)
    content = await repo.get(_parse_uuid(callback_data.content_id))
    if not content:
        await call.answer(t("review_content_not_found", lang))
        return

    target = _resolve_target(content)
    await repo.approve(content.id, target)
    await repo.enqueue(content.id, target)

    user_repo = UserRepo(session)
    await user_repo.increment_approved(content.user_id)

    await call.answer(t("review_approved", lang))
    await state.update_data(skipped_ids=[])
    data = await state.get_data()
    await _send_content(call, session, state, data.get("category", "all"), lang)


@router.callback_query(ReviewCB.filter(F.action == "reject"))
async def on_reject(
    call: CallbackQuery,
    callback_data: ReviewCB,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool,
    lang: str = "ru",
) -> None:
    if not is_admin:
        return

    repo = ContentRepo(session)
    content = await repo.get(_parse_uuid(callback_data.content_id))
    if content:
        if os.path.exists(content.file_path):
            try:
                os.remove(content.file_path)
            except OSError:
                pass
        await repo.reject(content.id)

    await call.answer(t("review_rejected", lang))
    await state.update_data(skipped_ids=[])
    data = await state.get_data()
    await _send_content(call, session, state, data.get("category", "all"), lang)


@router.callback_query(ReviewCB.filter(F.action == "to_story"))
async def on_to_story(
    call: CallbackQuery,
    callback_data: ReviewCB,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool,
    lang: str = "ru",
) -> None:
    if not is_admin:
        return

    repo = ContentRepo(session)
    content = await repo.get(_parse_uuid(callback_data.content_id))
    if not content:
        await call.answer(t("review_content_not_found", lang))
        return

    target = PublishTarget.story_video if content.media_type == MediaType.video else PublishTarget.story_photo
    await repo.approve(content.id, target)
    await repo.enqueue(content.id, target)

    user_repo = UserRepo(session)
    await user_repo.increment_approved(content.user_id)

    await call.answer(t("review_to_story", lang))
    await state.update_data(skipped_ids=[])
    data = await state.get_data()
    await _send_content(call, session, state, data.get("category", "all"), lang)


@router.callback_query(ReviewCB.filter(F.action == "skip"))
async def on_skip(
    call: CallbackQuery,
    callback_data: ReviewCB,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool,
    lang: str = "ru",
) -> None:
    if not is_admin:
        return
    data = await state.get_data()
    skipped_ids: list[str] = data.get("skipped_ids", [])
    content_id = data.get("content_id")
    if content_id and content_id not in skipped_ids:
        skipped_ids = [*skipped_ids, content_id]
        await state.update_data(skipped_ids=skipped_ids)
    await call.answer("⏭")
    await _send_content(call, session, state, data.get("category", "all"), lang)


# ── Inline description edit ──────────────────────────────────

@router.message(ReviewState.viewing)
async def on_description_text(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    is_admin: bool,
    lang: str = "ru",
) -> None:
    if not is_admin or not message.text:
        return

    data = await state.get_data()
    content_id_str = data.get("content_id")
    if not content_id_str:
        return

    repo = ContentRepo(session)
    await repo.update_description(_parse_uuid(content_id_str), message.text)

    try:
        await message.delete()
    except Exception:
        pass

    await _resend_current_content(message, session, state, lang)
