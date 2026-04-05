"""Internationalisation helpers.

Supported languages: "ru" (default), "en".
Usage:
    from app.i18n import t, detect_lang
    text = t("greeting", lang)
    text = t("dl_too_big", lang, mb=45)
"""
from __future__ import annotations

_TT = '<tg-emoji emoji-id="5327982530702359565">🎵</tg-emoji>'
_IG = '<tg-emoji emoji-id="5319160079465857105">📸</tg-emoji>'
_YT = '<tg-emoji emoji-id="5334942061349059951">▶️</tg-emoji>'

_STRINGS: dict[str, dict[str, str]] = {
    "ru": {
        # ── Start ─────────────────────────────────────────────────
        "greeting": (
            "👋 Привет!\n\n"
            "Я умею скачивать видео и фото из соцсетей "
            "<b>без водяного знака</b>:\n\n"
            f"  {_TT} TikTok\n"
            f"  {_IG} Instagram (посты, рилсы, сторис)\n"
            f"  {_YT} YouTube Shorts\n\n"
            "Просто отправь мне ссылку — и я пришлю файл!\n\n"
            "<b>Скачать сторисы по нику:</b>\n"
            "  <code>@username-all</code> — все активные сторисы\n"
            "  <code>@username-3</code> — конкретный сторис по номеру"
        ),
        # ── Fallback ──────────────────────────────────────────────
        "help": (
            "🤔 Не понял.\n\n"
            "Отправь мне ссылку на видео из:\n"
            "  • TikTok\n"
            "  • Instagram\n"
            "  • YouTube Shorts\n\n"
            "И я скачаю его для тебя без водяного знака!"
        ),
        # ── Download ──────────────────────────────────────────────
        "dl_busy": "⏳ У тебя уже 2 активных скачивания. Подожди.",
        "dl_no_hiker": "⚠️ HIKER_API_KEY не настроен — скачивание недоступно.",
        "dl_fetching": "⏳ Получаю {label} @{username}...",
        "dl_no_stories": "📭 У @{username} нет активных сторисов.",
        "dl_sending_stories": "📤 Отправляю {count} сторис(ов)...",
        "dl_stories_err": "❌ Не удалось получить сторисы. Проверь username или попробуй позже.",
        "dl_stories_index_err": "❌ {exc}",
        "dl_done_stories": "✅ Готово! Отправлено: {count}",
        "dl_done_stories_queued": ", добавлено в очередь оценки: {queued}",
        "dl_downloading": "⏳ Скачиваю...",
        "dl_err": "❌ Ошибка при скачивании. Попробуй другую ссылку.",
        "dl_null": "❌ Не удалось скачать контент.",
        "dl_sending": "📤 Отправляю файл...",
        "dl_done": "✅ Готово!",
        "dl_too_big": "⚠️ Файл слишком большой ({mb} МБ). Лимит Telegram — 50 МБ.",
        "dl_unsupported": "❌ Платформа не поддерживается",
        "dl_story_all": "все сторисы",
        "dl_story_n": "сторис #{n}",
        # ── Subscription (user-facing) ─────────────────────────────
        "sub_prompt": (
            "👋 Для использования бота необходимо подписаться на каналы:\n\n"
            "{ch_list}\n\n"
            "После подписки нажми кнопку ниже."
        ),
        "sub_btn_check": "✅ Я подписался",
        "sub_done_ok": "✅ Готово! Можешь использовать бота.",
        "sub_done": "✅ Готово!",
        "sub_not_yet": "❌ Ты ещё не подписан на: {ch_names}",
        "sub_confirmed": "✅ Подписка подтверждена! Теперь можешь использовать бота.",
        # ── Bot guard ─────────────────────────────────────────────
        "guard_disabled_msg": "🤖 Бот временно недоступен. Попробуйте позже.",
        "guard_disabled_cb": "🤖 Бот временно недоступен",
        "guard_sub_required": "Необходимо подписаться на каналы",
        # ── Admin panel ───────────────────────────────────────────
        "admin_panel_header": "🔧 <b>Админ-панель</b>",
        "admin_users_label": "👥 <b>Пользователей:</b> {n}",
        "admin_downloads_label": "📥 <b>Скачиваний:</b> {n}",
        "admin_blocked_label": "🚫 <b>Заблокировали бота:</b> {n}",
        "admin_bot_status": "🤖 <b>Статус бота:</b> {status}",
        "admin_bot_enabled": "🟢 Включён",
        "admin_bot_disabled": "🔴 Выключен",
        "admin_sub_label": "🔔 <b>Обяз. подписка:</b> {status}",
        "admin_sub_on": "🟢 Вкл ({n} кан.)",
        "admin_sub_off": "🔴 Выкл",
        "admin_pending_label": "📋 <b>На проверке:</b> {n}",
        "admin_queued_label": "📦 <b>В очереди:</b> {n}",
        "admin_api_header": "<b>🔌 API:</b>",
        "admin_no_data": "нет данных",
        "admin_api_hiker": "HikerAPI",
        "admin_api_tiktok": "TikTok Downloader",
        # ── Admin keyboard buttons ────────────────────────────────
        "btn_refresh": "🔄 Обновить",
        "btn_review": "📋 Оценивать контент",
        "btn_stats": "📊 Статистика",
        "btn_autopost": "⏰ Автопостинг",
        "btn_instagram": "📸 Instagram",
        "btn_logo": "🖼 Логотип",
        "btn_bot_off": "🔴 Выключить бот",
        "btn_bot_on": "🟢 Включить бот",
        "btn_broadcast": "📢 Рассылка",
        "btn_subscription": "🔔 Подписки",
        "btn_lang_switch": "🌐 Switch to English",
        "btn_back_menu": "« Меню",
        "btn_back": "« Назад",
        # ── Category picker ───────────────────────────────────────
        "cat_story": "📖 Сторис",
        "cat_reels": "🎬 Рилсы",
        "cat_igtv": "📺 IGTV",
        "cat_post": "📷 Посты",
        "cat_album": "📚 Альбомы",
        "cat_all": "🔀 Все подряд",
        # ── Review ────────────────────────────────────────────────
        "btn_to_story": "📖 В сторис",
        "btn_skip": "⏭ Пропустить",
        "review_no_content": "📭 Контент в этой категории отсутствует!",
        "review_file_missing_skip": "⚠️ Файл не найден, пропускаю...",
        "review_file_missing": "⚠️ Файл не найден",
        "review_send_failed": "⚠️ Не удалось отправить контент",
        "review_content_not_found": "Контент не найден",
        "review_album_empty": "⚠️ Альбом пуст",
        "review_rate_album": "⬆️ Оцени альбом:",
        "review_approved": "✅ Одобрено!",
        "review_rejected": "❌ Удалено!",
        "review_to_story": "📖 В сторис!",
        "review_no_desc": "<i>Описание отсутствует</i>",
        "review_caption_type": "<b>Тип:</b> {cat}",
        "review_caption_desc": "<b>Описание:</b>\n<code>{desc}</code>",
        "review_pending_header": "📁 <b>Непроверенного контента:</b> {n}\n\nВыбери категорию:",
        # ── Content category labels (used in review captions) ─────
        "cat_label_story": "сторис",
        "cat_label_reels": "рилс",
        "cat_label_igtv": "IGTV",
        "cat_label_post": "пост",
        "cat_label_album": "альбом",
        # ── Phase labels ──────────────────────────────────────────
        "phase_morning": "🌅 Утро",
        "phase_day": "☀️ День",
        "phase_evening": "🌙 Вечер",
        # ── Target labels (autopost sequence) ─────────────────────
        "target_story_video": "сторис-видео",
        "target_story_photo": "сторис-фото",
        "target_reels": "рилс",
        "target_post_video": "видео-пост",
        "target_post_photo": "фото-пост",
        "target_album": "альбом",
        "target_igtv": "igtv",
        # ── Autopost ──────────────────────────────────────────────
        "btn_autopost_off": "🔴 Выключить",
        "btn_autopost_on": "🟢 Включить",
        "btn_autopost_settings": "⚙️ Настройки",
        "btn_time_settings": "🕐 Временные промежутки",
        "btn_content_settings": "📝 Контент-сиквенс",
        "autopost_enabled": "🟢 Включен",
        "autopost_disabled": "🔴 Выключен",
        "autopost_header": "⏰ <b>Автопостинг:</b> {status}",
        "autopost_server_time": "🕐 Время сервера: <code>{time}</code>",
        "autopost_schedule_header": "<b>Расписание:</b>",
        "autopost_now": "<i>← сейчас</i>",
        "autopost_sequence_empty": "<i>не задан</i>",
        "autopost_queue_empty": "<i>очередь пуста</i>",
        "autopost_queue_total": "📦 <b>Очередь на публикацию: {n}</b>",
        "autopost_toggled_on": "🟢 Автопостинг включен!",
        "autopost_toggled_off": "🔴 Автопостинг выключен!",
        "autopost_settings_header": "⚙️ <b>Настройки автопостинга</b>",
        "autopost_pick_phase_time": "🕐 Выберите фазу для настройки времени:",
        "autopost_pick_phase_content": "📝 Выберите фазу для настройки контента:",
        # ── Admin settings (schedule) ─────────────────────────────
        "settings_time_prompt": (
            "{phase}\n"
            "🕐 Время сервера: <code>{now}</code>\n\n"
            "Введите временной промежуток в формате:\n"
            "<code>08:00-12:00</code>"
        ),
        "settings_time_invalid": (
            "{phase}\n\n"
            "❌ Неверный формат. Пример: <code>08:00-12:00</code>\n\n"
            "Введите временной промежуток заново:"
        ),
        "settings_time_bad": (
            "{phase}\n\n"
            "❌ Неверное время. Пример: <code>08:00-12:00</code>"
        ),
        "settings_time_saved": "✅ Время для {phase} обновлено: {range}",
        "settings_content_prompt": (
            "Введите последовательность контента через запятую:\n\n"
            "<b>Доступные ключи:</b>\n"
            "  <code>story_video</code> — сторис видео\n"
            "  <code>story_photo</code> — сторис фото\n"
            "  <code>reels</code> — рилс\n"
            "  <code>post_video</code> — видео пост\n"
            "  <code>post_photo</code> — фото пост\n"
            "  <code>album</code> — альбом\n"
            "  <code>igtv</code> — IGTV\n\n"
            "Пример:\n<code>reels,story_video,post_photo</code>"
        ),
        "settings_content_invalid": (
            "{phase}\n\n"
            "❌ Неизвестные ключи: <code>{keys}</code>\n\n"
            "{prompt}"
        ),
        "settings_content_saved": "✅ Контент для {phase} обновлён:\n<code>{seq}</code>",
        # ── Broadcast ─────────────────────────────────────────────
        "btn_broadcast_send": "📨 Отправить",
        "btn_broadcast_edit": "✏️ Изменить",
        "broadcast_header": (
            "📢 <b>Рассылка</b>\n\n"
            "Отправьте сообщение для рассылки.\n"
            "Поддерживается: текст (с любым форматированием), фото, видео, кружок.\n"
            "Для медиа можно добавить подпись.\n\n"
            "<i>Форматирование (жирный, курсив, ссылки и т.д.) сохраняется.</i>"
        ),
        "broadcast_edit_header": (
            "📢 <b>Рассылка</b>\n\n"
            "Отправьте новое сообщение для рассылки.\n"
            "Поддерживается: текст (с любым форматированием), фото, видео, кружок."
        ),
        "broadcast_unsupported": "❌ Неподдерживаемый тип. Отправьте текст, фото, видео или кружок.",
        "broadcast_preview_header": "📢 <b>Предпросмотр рассылки:</b>",
        "broadcast_save_err": "❌ Не удалось сохранить сообщение для рассылки.",
        "broadcast_no_data": "Нет данных для рассылки",
        "broadcast_started_header": "📢 Рассылка запущена...",
        "broadcast_started": "📨 Рассылка запущена!",
        "broadcast_done": "📢 <b>Рассылка завершена</b>\n\n✅ Доставлено: {delivered}\n❌ Не доставлено: {failed}",
        "broadcast_error": "❌ Ошибка рассылки: {exc}",
        # ── Instagram auth ────────────────────────────────────────
        "ig_not_set": "<не задан>",
        "ig_session_yes": "✅ Есть",
        "ig_session_no": "❌ Нет",
        "ig_status_text": (
            "📸 <b>Instagram</b>\n\n"
            "<b>Аккаунт:</b> @{username}\n"
            "<b>Файл сессии:</b> {session_status}\n\n"
            "<i>💡 Если авторизуешься впервые с нового IP — "
            "нажми «📥 VPN конфиг», подключись с телефона, "
            "открой Instagram, затем нажми «Авторизоваться».</i>"
        ),
        "ig_session_deleted": "🗑 Сессия удалена.\n\n",
        "ig_session_deleted_toast": "Сессия удалена",
        "ig_vpn_not_found": (
            "❌ VPN конфиг ещё не создан.\n"
            "<i>WireGuard контейнер генерирует его при первом запуске — "
            "подожди минуту и попробуй снова.</i>"
        ),
        "ig_vpn_caption": "📥 WireGuard конфиг — импортируй в приложение на телефоне",
        "ig_vpn_send_err": "❌ Ошибка отправки конфига:\n<code>{exc}</code>",
        "ig_connecting": (
            "🔄 Подключаюсь к Instagram...\n\n"
            "<i>Это может занять несколько секунд.</i>"
        ),
        "ig_challenge_prompt": (
            "📱 <b>Instagram требует подтверждение!</b>\n\n"
            "Введи код из SMS или Email:\n"
            "<i>(у тебя есть 5 минут)</i>"
        ),
        "ig_login_ok": "✅ <b>Авторизован успешно!</b>\n\n",
        "ig_login_err": "❌ <b>Ошибка авторизации:</b>\n<code>{exc}</code>",
        "ig_challenge_expired": "⚠️ Сессия подтверждения истекла. Попробуй авторизоваться заново.",
        "ig_code_sent": "🔑 Код <code>{code}</code> отправлен, жду подтверждения...",
        # ── Subscription management (admin) ───────────────────────
        "btn_sub_toggle_off": "🔴 Отключить подписку",
        "btn_sub_toggle_on": "🟢 Включить подписку",
        "btn_sub_add": "➕ Добавить канал",
        # ── Lang switch ───────────────────────────────────────────
        "lang_switched_en": "Language switched to English 🇬🇧",
        "lang_switched_ru": "Язык переключён на русский 🇷🇺",
        # ── HikerAPI / TikTok status ──────────────────────────────
        "hiker_key_missing": "⚠️ ключ не задан",
        "hiker_endpoint_error": "❌ endpoint не найден",
        "hiker_tariff": " · тариф {rate} {currency}",
        "hiker_balance_raw": "✅ баланс: {balance}",
        "tiktok_status_ok": "✅ доступен",
        # ── Stats ─────────────────────────────────────────────────
        "stats_header": "📊 <b>Статистика на сегодня</b>",
        "stats_pending": "<b>На проверке:</b>",
        "stats_queue": "<b>В очереди на публикацию:</b>",
        "stats_published": "<b>Опубликовано сегодня:</b>",
        # ── Logo ──────────────────────────────────────────────────
        "logo_caption_existing": (
            "🖼 <b>Логотип вотермарка</b>\n\n"
            "Отправь PNG-файл (желательно с прозрачным фоном) "
            "для замены логотипа.\nИли нажми «Меню» для отмены."
        ),
        "logo_caption_none": (
            "❌ <b>Логотип не загружен</b>\n\n"
            "Отправь PNG-файл (желательно с прозрачным фоном) "
            "для установки логотипа.\nИли нажми «Меню» для отмены."
        ),
        "logo_updated": "✅ <b>Логотип обновлён!</b>\n\nБудет применяться ко всем следующим публикациям.",
        # ── Instagram keyboard buttons ────────────────────────────
        "btn_ig_login": "🔑 Авторизоваться",
        "btn_ig_relogin": "🔄 Переавторизоваться",
        "btn_ig_delete_session": "🗑 Удалить сессию",
        "btn_ig_vpn_config": "📥 VPN конфиг",
        # ── Subscription management (admin) ───────────────────────
        "sub_manage_title": "🔔 <b>Обязательная подписка</b>",
        "sub_manage_status": "Статус: {status}",
        "sub_manage_status_on": "🟢 включена",
        "sub_manage_status_off": "🔴 выключена",
        "sub_manage_channels": "<b>Каналы:</b>",
        "sub_manage_no_channels": "<i>Каналы не добавлены</i>",
        "sub_manage_note": (
            "<i>Когда подписка включена, пользователи должны "
            "подписаться на все каналы перед использованием бота.</i>"
        ),
        "sub_toggle_on_toast": "Подписка включена",
        "sub_toggle_off_toast": "Подписка выключена",
        "sub_add_header": (
            "➕ <b>Добавить канал</b>\n\n"
            "Отправьте @username или ссылку на канал:\n"
            "<code>@mychannel</code>\n"
            "<code>https://t.me/mychannel</code>\n\n"
            "<b>Важно:</b> бот должен быть администратором канала "
            "для проверки подписки пользователей."
        ),
        "sub_add_invalid": (
            "❌ Не удалось распознать канал.\n\n"
            "Отправьте <code>@username</code> или "
            "<code>https://t.me/username</code>:"
        ),
        "sub_add_resolve_err": (
            "❌ Не удалось получить информацию о <code>{username}</code>.\n\n"
            "Убедитесь, что бот добавлен в канал как администратор, "
            "и повторите попытку:"
        ),
        "sub_already_added": "⚠️ Канал <b>{title}</b> уже добавлен.",
        "sub_added_ok": "✅ Канал <b>{title}</b> добавлен!",
        "sub_remove_not_found": "Канал не найден",
        "sub_remove_done": "Канал «{title}» удалён",
    },
    "en": {
        # ── Start ─────────────────────────────────────────────────
        "greeting": (
            "👋 Hi!\n\n"
            "I can download videos and photos from social media "
            "<b>without watermarks</b>:\n\n"
            f"  {_TT} TikTok\n"
            f"  {_IG} Instagram (posts, reels, stories)\n"
            f"  {_YT} YouTube Shorts\n\n"
            "Just send me a link and I'll send back the file!\n\n"
            "<b>Download stories by username:</b>\n"
            "  <code>@username-all</code> — all active stories\n"
            "  <code>@username-3</code> — a specific story by number"
        ),
        # ── Fallback ──────────────────────────────────────────────
        "help": (
            "🤔 Didn't understand that.\n\n"
            "Send me a video link from:\n"
            "  • TikTok\n"
            "  • Instagram\n"
            "  • YouTube Shorts\n\n"
            "And I'll download it for you without a watermark!"
        ),
        # ── Download ──────────────────────────────────────────────
        "dl_busy": "⏳ You already have 2 active downloads. Please wait.",
        "dl_no_hiker": "⚠️ HIKER_API_KEY not configured — downloading unavailable.",
        "dl_fetching": "⏳ Fetching {label} @{username}...",
        "dl_no_stories": "📭 @{username} has no active stories.",
        "dl_sending_stories": "📤 Sending {count} story/stories...",
        "dl_stories_err": "❌ Failed to get stories. Check the username or try again later.",
        "dl_stories_index_err": "❌ {exc}",
        "dl_done_stories": "✅ Done! Sent: {count}",
        "dl_done_stories_queued": ", added to review queue: {queued}",
        "dl_downloading": "⏳ Downloading...",
        "dl_err": "❌ Download error. Try a different link.",
        "dl_null": "❌ Failed to download content.",
        "dl_sending": "📤 Sending file...",
        "dl_done": "✅ Done!",
        "dl_too_big": "⚠️ File too large ({mb} MB). Telegram limit is 50 MB.",
        "dl_unsupported": "❌ Platform not supported",
        "dl_story_all": "all stories",
        "dl_story_n": "story #{n}",
        # ── Subscription (user-facing) ─────────────────────────────
        "sub_prompt": (
            "👋 To use the bot, please subscribe to the following channels:\n\n"
            "{ch_list}\n\n"
            "After subscribing, press the button below."
        ),
        "sub_btn_check": "✅ I subscribed",
        "sub_done_ok": "✅ Done! You can now use the bot.",
        "sub_done": "✅ Done!",
        "sub_not_yet": "❌ You're not subscribed to: {ch_names}",
        "sub_confirmed": "✅ Subscription confirmed! You can now use the bot.",
        # ── Bot guard ─────────────────────────────────────────────
        "guard_disabled_msg": "🤖 Bot temporarily unavailable. Try again later.",
        "guard_disabled_cb": "🤖 Bot temporarily unavailable",
        "guard_sub_required": "Please subscribe to the required channels",
        # ── Admin panel ───────────────────────────────────────────
        "admin_panel_header": "🔧 <b>Admin Panel</b>",
        "admin_users_label": "👥 <b>Users:</b> {n}",
        "admin_downloads_label": "📥 <b>Downloads:</b> {n}",
        "admin_blocked_label": "🚫 <b>Blocked bot:</b> {n}",
        "admin_bot_status": "🤖 <b>Bot status:</b> {status}",
        "admin_bot_enabled": "🟢 Enabled",
        "admin_bot_disabled": "🔴 Disabled",
        "admin_sub_label": "🔔 <b>Forced subscription:</b> {status}",
        "admin_sub_on": "🟢 On ({n} ch.)",
        "admin_sub_off": "🔴 Off",
        "admin_pending_label": "📋 <b>Pending review:</b> {n}",
        "admin_queued_label": "📦 <b>In queue:</b> {n}",
        "admin_api_header": "<b>🔌 API:</b>",
        "admin_no_data": "no data",
        "admin_api_hiker": "HikerAPI",
        "admin_api_tiktok": "TikTok Downloader",
        # ── Admin keyboard buttons ────────────────────────────────
        "btn_refresh": "🔄 Refresh",
        "btn_review": "📋 Review content",
        "btn_stats": "📊 Statistics",
        "btn_autopost": "⏰ Autopost",
        "btn_instagram": "📸 Instagram",
        "btn_logo": "🖼 Logo",
        "btn_bot_off": "🔴 Disable bot",
        "btn_bot_on": "🟢 Enable bot",
        "btn_broadcast": "📢 Broadcast",
        "btn_subscription": "🔔 Subscriptions",
        "btn_lang_switch": "🌐 Переключить на русский",
        "btn_back_menu": "« Menu",
        "btn_back": "« Back",
        # ── Category picker ───────────────────────────────────────
        "cat_story": "📖 Stories",
        "cat_reels": "🎬 Reels",
        "cat_igtv": "📺 IGTV",
        "cat_post": "📷 Posts",
        "cat_album": "📚 Albums",
        "cat_all": "🔀 All",
        # ── Review ────────────────────────────────────────────────
        "btn_to_story": "📖 To story",
        "btn_skip": "⏭ Skip",
        "review_no_content": "📭 No content in this category!",
        "review_file_missing_skip": "⚠️ File not found, skipping...",
        "review_file_missing": "⚠️ File not found",
        "review_send_failed": "⚠️ Failed to send content",
        "review_content_not_found": "Content not found",
        "review_album_empty": "⚠️ Album is empty",
        "review_rate_album": "⬆️ Rate this album:",
        "review_approved": "✅ Approved!",
        "review_rejected": "❌ Deleted!",
        "review_to_story": "📖 To story!",
        "review_no_desc": "<i>No description</i>",
        "review_caption_type": "<b>Type:</b> {cat}",
        "review_caption_desc": "<b>Description:</b>\n<code>{desc}</code>",
        "review_pending_header": "📁 <b>Pending content:</b> {n}\n\nChoose a category:",
        # ── Content category labels ───────────────────────────────
        "cat_label_story": "story",
        "cat_label_reels": "reels",
        "cat_label_igtv": "IGTV",
        "cat_label_post": "post",
        "cat_label_album": "album",
        # ── Phase labels ──────────────────────────────────────────
        "phase_morning": "🌅 Morning",
        "phase_day": "☀️ Day",
        "phase_evening": "🌙 Evening",
        # ── Target labels ─────────────────────────────────────────
        "target_story_video": "story video",
        "target_story_photo": "story photo",
        "target_reels": "reels",
        "target_post_video": "video post",
        "target_post_photo": "photo post",
        "target_album": "album",
        "target_igtv": "igtv",
        # ── Autopost ──────────────────────────────────────────────
        "btn_autopost_off": "🔴 Disable",
        "btn_autopost_on": "🟢 Enable",
        "btn_autopost_settings": "⚙️ Settings",
        "btn_time_settings": "🕐 Time intervals",
        "btn_content_settings": "📝 Content sequence",
        "autopost_enabled": "🟢 Enabled",
        "autopost_disabled": "🔴 Disabled",
        "autopost_header": "⏰ <b>Autopost:</b> {status}",
        "autopost_server_time": "🕐 Server time: <code>{time}</code>",
        "autopost_schedule_header": "<b>Schedule:</b>",
        "autopost_now": "<i>← now</i>",
        "autopost_sequence_empty": "<i>not set</i>",
        "autopost_queue_empty": "<i>queue is empty</i>",
        "autopost_queue_total": "📦 <b>Publish queue: {n}</b>",
        "autopost_toggled_on": "🟢 Autopost enabled!",
        "autopost_toggled_off": "🔴 Autopost disabled!",
        "autopost_settings_header": "⚙️ <b>Autopost settings</b>",
        "autopost_pick_phase_time": "🕐 Choose a phase to set the time:",
        "autopost_pick_phase_content": "📝 Choose a phase to set the content:",
        # ── Admin settings (schedule) ─────────────────────────────
        "settings_time_prompt": (
            "{phase}\n"
            "🕐 Server time: <code>{now}</code>\n\n"
            "Enter the time range in format:\n"
            "<code>08:00-12:00</code>"
        ),
        "settings_time_invalid": (
            "{phase}\n\n"
            "❌ Invalid format. Example: <code>08:00-12:00</code>\n\n"
            "Enter the time range again:"
        ),
        "settings_time_bad": (
            "{phase}\n\n"
            "❌ Invalid time. Example: <code>08:00-12:00</code>"
        ),
        "settings_time_saved": "✅ Time for {phase} updated: {range}",
        "settings_content_prompt": (
            "Enter the content sequence separated by commas:\n\n"
            "<b>Available keys:</b>\n"
            "  <code>story_video</code> — story video\n"
            "  <code>story_photo</code> — story photo\n"
            "  <code>reels</code> — reels\n"
            "  <code>post_video</code> — video post\n"
            "  <code>post_photo</code> — photo post\n"
            "  <code>album</code> — album\n"
            "  <code>igtv</code> — IGTV\n\n"
            "Example:\n<code>reels,story_video,post_photo</code>"
        ),
        "settings_content_invalid": (
            "{phase}\n\n"
            "❌ Unknown keys: <code>{keys}</code>\n\n"
            "{prompt}"
        ),
        "settings_content_saved": "✅ Content for {phase} updated:\n<code>{seq}</code>",
        # ── Broadcast ─────────────────────────────────────────────
        "btn_broadcast_send": "📨 Send",
        "btn_broadcast_edit": "✏️ Edit",
        "broadcast_header": (
            "📢 <b>Broadcast</b>\n\n"
            "Send a message to broadcast.\n"
            "Supported: text (any formatting), photo, video, video note.\n"
            "Media can include a caption.\n\n"
            "<i>Formatting (bold, italic, links, etc.) is preserved.</i>"
        ),
        "broadcast_edit_header": (
            "📢 <b>Broadcast</b>\n\n"
            "Send a new message to broadcast.\n"
            "Supported: text (any formatting), photo, video, video note."
        ),
        "broadcast_unsupported": "❌ Unsupported type. Send text, photo, video, or video note.",
        "broadcast_preview_header": "📢 <b>Broadcast preview:</b>",
        "broadcast_save_err": "❌ Failed to save the message for broadcast.",
        "broadcast_no_data": "No broadcast data",
        "broadcast_started_header": "📢 Broadcast started...",
        "broadcast_started": "📨 Broadcast started!",
        "broadcast_done": "📢 <b>Broadcast complete</b>\n\n✅ Delivered: {delivered}\n❌ Failed: {failed}",
        "broadcast_error": "❌ Broadcast error: {exc}",
        # ── Instagram auth ────────────────────────────────────────
        "ig_not_set": "<not set>",
        "ig_session_yes": "✅ Exists",
        "ig_session_no": "❌ None",
        "ig_status_text": (
            "📸 <b>Instagram</b>\n\n"
            "<b>Account:</b> @{username}\n"
            "<b>Session file:</b> {session_status}\n\n"
            "<i>💡 If logging in for the first time from a new IP — "
            "press «📥 VPN config», connect your phone, "
            "open Instagram, then press «Authorize».</i>"
        ),
        "ig_session_deleted": "🗑 Session deleted.\n\n",
        "ig_session_deleted_toast": "Session deleted",
        "ig_vpn_not_found": (
            "❌ VPN config not created yet.\n"
            "<i>The WireGuard container generates it on first run — "
            "wait a minute and try again.</i>"
        ),
        "ig_vpn_caption": "📥 WireGuard config — import it into the app on your phone",
        "ig_vpn_send_err": "❌ Error sending config:\n<code>{exc}</code>",
        "ig_connecting": (
            "🔄 Connecting to Instagram...\n\n"
            "<i>This may take a few seconds.</i>"
        ),
        "ig_challenge_prompt": (
            "📱 <b>Instagram requires verification!</b>\n\n"
            "Enter the code from SMS or Email:\n"
            "<i>(you have 5 minutes)</i>"
        ),
        "ig_login_ok": "✅ <b>Authorized successfully!</b>\n\n",
        "ig_login_err": "❌ <b>Authorization error:</b>\n<code>{exc}</code>",
        "ig_challenge_expired": "⚠️ Verification session expired. Try authorizing again.",
        "ig_code_sent": "🔑 Code <code>{code}</code> sent, waiting for confirmation...",
        # ── Subscription management (admin) ───────────────────────
        "btn_sub_toggle_off": "🔴 Disable subscription",
        "btn_sub_toggle_on": "🟢 Enable subscription",
        "btn_sub_add": "➕ Add channel",
        # ── Lang switch ───────────────────────────────────────────
        "lang_switched_en": "Language switched to English 🇬🇧",
        "lang_switched_ru": "Язык переключён на русский 🇷🇺",
        # ── HikerAPI / TikTok status ──────────────────────────────
        "hiker_key_missing": "⚠️ key not set",
        "hiker_endpoint_error": "❌ endpoint not found",
        "hiker_tariff": " · plan {rate} {currency}",
        "hiker_balance_raw": "✅ balance: {balance}",
        "tiktok_status_ok": "✅ available",
        # ── Stats ─────────────────────────────────────────────────
        "stats_header": "📊 <b>Today's Statistics</b>",
        "stats_pending": "<b>Pending review:</b>",
        "stats_queue": "<b>In publish queue:</b>",
        "stats_published": "<b>Published today:</b>",
        # ── Logo ──────────────────────────────────────────────────
        "logo_caption_existing": (
            "🖼 <b>Watermark logo</b>\n\n"
            "Send a PNG file (preferably with a transparent background) "
            "to replace the logo.\nOr press «Menu» to cancel."
        ),
        "logo_caption_none": (
            "❌ <b>No logo uploaded</b>\n\n"
            "Send a PNG file (preferably with a transparent background) "
            "to set the logo.\nOr press «Menu» to cancel."
        ),
        "logo_updated": "✅ <b>Logo updated!</b>\n\nWill be applied to all future publications.",
        # ── Instagram keyboard buttons ────────────────────────────
        "btn_ig_login": "🔑 Authorize",
        "btn_ig_relogin": "🔄 Re-authorize",
        "btn_ig_delete_session": "🗑 Delete session",
        "btn_ig_vpn_config": "📥 VPN config",
        # ── Subscription management (admin) ───────────────────────
        "sub_manage_title": "🔔 <b>Forced subscription</b>",
        "sub_manage_status": "Status: {status}",
        "sub_manage_status_on": "🟢 enabled",
        "sub_manage_status_off": "🔴 disabled",
        "sub_manage_channels": "<b>Channels:</b>",
        "sub_manage_no_channels": "<i>No channels added</i>",
        "sub_manage_note": (
            "<i>When subscription is enabled, users must subscribe "
            "to all channels before using the bot.</i>"
        ),
        "sub_toggle_on_toast": "Subscription enabled",
        "sub_toggle_off_toast": "Subscription disabled",
        "sub_add_header": (
            "➕ <b>Add channel</b>\n\n"
            "Send @username or a channel link:\n"
            "<code>@mychannel</code>\n"
            "<code>https://t.me/mychannel</code>\n\n"
            "<b>Important:</b> the bot must be an administrator of the channel "
            "to verify user subscriptions."
        ),
        "sub_add_invalid": (
            "❌ Could not parse channel input.\n\n"
            "Send <code>@username</code> or "
            "<code>https://t.me/username</code>:"
        ),
        "sub_add_resolve_err": (
            "❌ Could not fetch info for <code>{username}</code>.\n\n"
            "Make sure the bot is added to the channel as an admin, "
            "then try again:"
        ),
        "sub_already_added": "⚠️ Channel <b>{title}</b> is already added.",
        "sub_added_ok": "✅ Channel <b>{title}</b> added!",
        "sub_remove_not_found": "Channel not found",
        "sub_remove_done": "Channel «{title}» removed",
    },
}


def t(key: str, lang: str = "ru", **kwargs: object) -> str:
    """Return localised string for *key* in *lang*, falling back to Russian."""
    strings = _STRINGS.get(lang, _STRINGS["ru"])
    template = strings.get(key) or _STRINGS["ru"].get(key, key)
    return template.format(**kwargs) if kwargs else template


def detect_lang(language_code: str | None) -> str:
    """Detect 'ru' or 'en' from Telegram language_code field."""
    if language_code and language_code.startswith("ru"):
        return "ru"
    return "en"
