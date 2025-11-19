"""
Telegram бот для управления Instagram Auto Publisher
====================================================

Полностью управляет системой через Telegram интерфейс.
"""

import os
import telebot
from telebot import types
from typing import Optional
from pathlib import Path

from .config import Config
from .database import get_database
from .downloaders import get_downloader
from .uploaders import create_instagram_client, InstagramUploader
from .scheduler import ContentScheduler
from .utils import ensure_directory, get_content_type_from_path, count_files_in_directory


class InstagramBot:
    """Telegram бот для управления Instagram Auto Publisher"""
    
    def __init__(self):
        """Инициализация бота"""
        self.bot = telebot.TeleBot(Config.TELEGRAM_BOT_TOKEN)
        self.db = get_database()
        self.admin_ids = Config.get_admin_ids()
        
        # Создаём Instagram клиент и планировщик
        self.instagram_client = create_instagram_client()
        self.uploader = InstagramUploader(self.instagram_client)
        self.scheduler = ContentScheduler(self.uploader)
        
        # Приветственное сообщение
        self.welcome_message = (
            "👋 Привет!\n"
            "🤖 Я умею скачивать контент из соц сетей:\n"
            "✅ Instagram\n"
            "✅ TikTok (без водяного знака)\n"
            "✅ YouTube Shorts\n\n"
            "🔗 Отправь мне ссылку с желаемым контентом!"
        )
        
        # Регистрируем обработчики
        self._register_handlers()
        
        print("✅ Telegram бот инициализирован")
    
    def _is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return user_id in self.admin_ids
    
    def _create_keyboards(self):
        """Создаёт клавиатуры для бота"""
        # Главное меню администратора
        self.admin_menu = types.InlineKeyboardMarkup()
        self.admin_menu.row_width = 1
        self.admin_menu.add(
            types.InlineKeyboardButton("Оценивать контент", callback_data='content_rate'),
            types.InlineKeyboardButton("📊 Статистика", callback_data='stat'),
            types.InlineKeyboardButton("⚙️ Автопостинг", callback_data='autopost')
        )
        
        # Меню выбора типа контента для оценки
        self.rate_content_menu = types.InlineKeyboardMarkup()
        self.rate_content_menu.row_width = 1
        self.rate_content_menu.add(
            types.InlineKeyboardButton("📹 Смотреть сторис", callback_data='story_view'),
            types.InlineKeyboardButton("🎬 Смотреть клипы", callback_data='reels_view'),
            types.InlineKeyboardButton("📺 Смотреть IGTV", callback_data='igtv_view'),
            types.InlineKeyboardButton("📸 Обычные посты", callback_data='other_posts_view'),
            types.InlineKeyboardButton("📚 Альбомные посты", callback_data='albums_posts_view'),
            types.InlineKeyboardButton("🔀 Смотреть все подряд", callback_data='all_view'),
            types.InlineKeyboardButton("⬅️ Назад", callback_data='back_admin')
        )
        
        # Кнопки оценки контента
        self.tinder_buttons = types.InlineKeyboardMarkup()
        self.tinder_buttons.row_width = 2
        self.tinder_buttons.add(
            types.InlineKeyboardButton("✅", callback_data='yes'),
            types.InlineKeyboardButton("❌", callback_data='no')
        )
        self.tinder_buttons.row_width = 1
        self.tinder_buttons.add(types.InlineKeyboardButton("⬅️ В меню", callback_data='back_admin'))
        
        # Кнопки с возможностью добавить в Stories
        self.tinder_with_story = types.InlineKeyboardMarkup()
        self.tinder_with_story.row_width = 2
        self.tinder_with_story.add(
            types.InlineKeyboardButton("✅", callback_data='yes'),
            types.InlineKeyboardButton("❌", callback_data='no')
        )
        self.tinder_with_story.row_width = 1
        self.tinder_with_story.add(
            types.InlineKeyboardButton("📱 В сторис", callback_data='to_story'),
            types.InlineKeyboardButton("⬅️ В меню", callback_data='back_admin')
        )
        
        # Кнопка "Назад"
        self.back_button = types.InlineKeyboardMarkup()
        self.back_button.add(types.InlineKeyboardButton("⬅️ Назад", callback_data='back_admin'))
        
        # Меню автопостинга
        self.autopost_menu_on = types.InlineKeyboardMarkup()
        self.autopost_menu_on.row_width = 1
        self.autopost_menu_on.add(
            types.InlineKeyboardButton("⏸ Выключить автопостинг", callback_data='autopost_toggle'),
            types.InlineKeyboardButton("⚙️ Настройки", callback_data='settings_autopost'),
            types.InlineKeyboardButton("⬅️ В меню", callback_data='menu')
        )
        
        self.autopost_menu_off = types.InlineKeyboardMarkup()
        self.autopost_menu_off.row_width = 1
        self.autopost_menu_off.add(
            types.InlineKeyboardButton("▶️ Включить автопостинг", callback_data='autopost_toggle'),
            types.InlineKeyboardButton("⚙️ Настройки", callback_data='settings_autopost'),
            types.InlineKeyboardButton("⬅️ В меню", callback_data='menu')
        )
        
        # Меню настроек автопостинга
        self.settings_menu = types.InlineKeyboardMarkup()
        self.settings_menu.row_width = 1
        self.settings_menu.add(
            types.InlineKeyboardButton("⏰ Настройка времени", callback_data='timestamp_settings'),
            types.InlineKeyboardButton("📝 Настройка контента", callback_data='content_settings'),
            types.InlineKeyboardButton("⬅️ В меню", callback_data='menu')
        )
    
    def _register_handlers(self):
        """Регистрирует все обработчики команд и callback'ов"""
        
        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            # Добавляем пользователя в БД если его нет
            if not self.db.user_exists(message.from_user.id):
                self.db.add_user(
                    user_id=message.from_user.id,
                    user_name=message.from_user.first_name or "",
                    user_surname=message.from_user.last_name or "",
                    username=message.from_user.username or ""
                )
            
            self.bot.send_message(message.chat.id, text=self.welcome_message)
        
        @self.bot.message_handler(content_types=['text'])
        def handle_text(message):
            text = message.text.strip()
            
            # Проверка на команду входа в админ-панель
            if text.lower() == 'sliska' and self._is_admin(message.from_user.id):
                self._create_keyboards()
                self.bot.send_message(
                    message.chat.id,
                    text="🔐 Админ-панель:",
                    reply_markup=self.admin_menu
                )
                return
            
            # Обработка ссылок
            downloader = get_downloader(text)
            
            if downloader:
                # Отправляем сообщение о начале загрузки
                loading_msg = self.bot.send_message(message.chat.id, text='⏳ Скачиваю...')
                
                try:
                    # Скачиваем контент
                    success, msg, file_path = downloader.download(text, message.from_user.id)
                    
                    # Удаляем сообщение о загрузке
                    self.bot.delete_message(message.chat.id, loading_msg.message_id)
                    
                    if success and file_path:
                        # Отправляем скачанный файл
                        if os.path.isdir(file_path):
                            # Это альбом
                            self.bot.send_message(message.chat.id, text=msg)
                        elif file_path.endswith('.mp4'):
                            with open(file_path, 'rb') as video:
                                self.bot.send_video(message.chat.id, video, caption=msg)
                        else:
                            with open(file_path, 'rb') as photo:
                                self.bot.send_photo(message.chat.id, photo, caption=msg)
                    else:
                        self.bot.send_message(message.chat.id, text=msg)
                
                except Exception as e:
                    self.bot.delete_message(message.chat.id, loading_msg.message_id)
                    self.bot.send_message(
                        message.chat.id,
                        text=f"❌ Ошибка при обработке: {str(e)}"
                    )
            else:
                self.bot.send_message(message.chat.id, text="❌ Неверная ссылка или формат!")
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            if not self._is_admin(call.from_user.id):
                self.bot.answer_callback_query(call.id, "❌ Доступ запрещён")
                return
            
            self._create_keyboards()
            
            # Обработка различных callback'ов
            if call.data == "back_admin":
                self._handle_back_to_menu(call)
            elif call.data == "content_rate":
                self._handle_content_rate(call)
            elif call.data == "stat":
                self._handle_statistics(call)
            elif call.data == "autopost":
                self._handle_autopost_menu(call)
            elif call.data == "autopost_toggle":
                self._handle_autopost_toggle(call)
            elif call.data == "settings_autopost":
                self._handle_settings_menu(call)
            elif call.data == "menu":
                self._handle_back_to_menu(call)
            # Добавьте другие обработчики по необходимости
    
    def _handle_back_to_menu(self, call):
        """Возврат в главное меню"""
        try:
            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text="🔐 Админ-панель:",
                reply_markup=self.admin_menu
            )
        except:
            pass
    
    def _handle_content_rate(self, call):
        """Показывает меню выбора типа контента"""
        content_stats = self._get_content_statistics()
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text=f"📊 Статистика непроверенного контента:\n\n{content_stats}\n\nВыберите категорию:",
            reply_markup=self.rate_content_menu,
            parse_mode='Markdown'
        )
    
    def _handle_statistics(self, call):
        """Показывает статистику"""
        stats = self._count_approved_files()
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text=f"📊 Статистика готового контента:\n\n{stats}",
            reply_markup=self.admin_menu
        )
    
    def _handle_autopost_menu(self, call):
        """Показывает меню автопостинга"""
        is_active = self.db.get_setting("autopost_status")
        status_text = "🟢 Включен" if is_active else "🔴 Выключен"
        
        content_info = self._get_autopost_content_info()
        
        menu = self.autopost_menu_on if is_active else self.autopost_menu_off
        
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text=f"⚙️ Статус автопостинга: {status_text}\n\n{content_info}",
            reply_markup=menu
        )
    
    def _handle_autopost_toggle(self, call):
        """Переключает автопостинг вкл/выкл"""
        current_status = self.db.get_setting("autopost_status")
        new_status = not current_status
        
        self.db.set_setting("autopost_status", new_status)
        
        if new_status:
            # Включаем автопостинг
            morning = self.db.get_setting("morning_time")
            day = self.db.get_setting("day_time")
            evening = self.db.get_setting("evening_time")
            self.scheduler.start(morning, day, evening)
            status_text = "🟢 Включен"
        else:
            # Выключаем
            self.scheduler.stop()
            status_text = "🔴 Выключен"
        
        content_info = self._get_autopost_content_info()
        menu = self.autopost_menu_on if new_status else self.autopost_menu_off
        
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text=f"⚙️ Статус автопостинга: {status_text}\n\n{content_info}",
            reply_markup=menu
        )
    
    def _handle_settings_menu(self, call):
        """Показывает меню настроек"""
        if self.db.get_setting("autopost_status"):
            self.bot.answer_callback_query(
                call.id,
                "⚠️ Выключите автопостинг перед входом в настройки"
            )
            return
        
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text="⚙️ Выберите категорию настроек:",
            reply_markup=self.settings_menu
        )
    
    # Вспомогательные методы
    
    def _get_content_statistics(self) -> str:
        """Возвращает статистику непроверенного контента"""
        from .utils import count_files_in_directory
        
        stats = {
            "Сторис": 0,
            "Клипы": 0,
            "IGTV": 0,
            "Обычные посты": 0,
            "Альбомы": 0
        }
        
        # Подсчитываем файлы во всех папках пользователей
        base_dir = Config.CONTENT_BASE_DIR
        if os.path.exists(base_dir):
            for user_folder in os.listdir(base_dir):
                user_path = os.path.join(base_dir, user_folder)
                if os.path.isdir(user_path):
                    for platform in ['instagram', 'tiktok', 'yt', 'pinterest']:
                        platform_path = os.path.join(user_path, platform)
                        if os.path.exists(platform_path):
                            # Сторис
                            stats["Сторис"] += count_files_in_directory(f"{platform_path}/storys/video")
                            stats["Сторис"] += count_files_in_directory(f"{platform_path}/storys/photo")
                            # Клипы
                            stats["Клипы"] += count_files_in_directory(f"{platform_path}/video_posts/clips")
                            # IGTV
                            stats["IGTV"] += count_files_in_directory(f"{platform_path}/video_posts/igtv")
        
        # Обычные посты
        stats["Обычные посты"] += count_files_in_directory(f"{base_dir}/photo_posts")
        stats["Обычные посты"] += count_files_in_directory(f"{base_dir}/video_posts", ".mp4")
        
        # Альбомы
        albums_dir = Config.ALBUMS_DIR
        if os.path.exists(albums_dir):
            stats["Альбомы"] = len([d for d in os.listdir(albums_dir) if os.path.isdir(os.path.join(albums_dir, d))])
        
        total = sum(stats.values())
        
        result = "\n".join([f"📁 {k}: {v}" for k, v in stats.items()])
        result += f"\n\n💾 *Всего: {total}*"
        
        return result
    
    def _count_approved_files(self) -> str:
        """Подсчитывает готовые файлы для публикации"""
        counts = {
            "Видео сторис": count_files_in_directory(Config.STORIES_VIDEO_DIR),
            "Фото сторис": count_files_in_directory(Config.STORIES_PHOTO_DIR),
            "Видео посты": count_files_in_directory(Config.POSTS_VIDEO_DIR, ".mp4"),
            "Фото посты": count_files_in_directory(Config.POSTS_PHOTO_DIR),
            "Альбомы": len([d for d in os.listdir(Config.ALBUMS_DIR) if os.path.isdir(os.path.join(Config.ALBUMS_DIR, d))]) if os.path.exists(Config.ALBUMS_DIR) else 0,
            "IGTV": count_files_in_directory(Config.IGTV_DIR),
            "Клипы": count_files_in_directory(Config.CLIPS_DIR)
        }
        
        return "\n".join([f"{k}: {v}" for k, v in counts.items()])
    
    def _get_autopost_content_info(self) -> str:
        """Возвращает информацию о контенте для автопостинга"""
        morning_time = self.db.get_setting("morning_time")
        day_time = self.db.get_setting("day_time")
        evening_time = self.db.get_setting("evening_time")
        
        morning_content = self.db.get_setting("morning_content")
        day_content = self.db.get_setting("day_content")
        evening_content = self.db.get_setting("evening_content")
        
        uploaded_sv = self.db.get_setting("uploaded_video_story")
        uploaded_sf = self.db.get_setting("uploaded_photo_story")
        uploaded_vp = self.db.get_setting("uploaded_video_posts")
        uploaded_fp = self.db.get_setting("uploaded_photo_posts")
        uploaded_ap = self.db.get_setting("uploaded_album_posts")
        uploaded_it = self.db.get_setting("uploaded_igtv")
        uploaded_k = self.db.get_setting("uploaded_clips")
        
        current_position = self.db.get_setting("current_position_content")
        
        info = f"""
⏰ Временные рамки:
🌅 Утро: {morning_time}
☀️ День: {day_time}
🌙 Вечер: {evening_time}

📝 Контент:
Утро: {morning_content}
День: {day_content}
Вечер: {evening_content}

📊 Загружено сегодня:
СВ: {uploaded_sv} | СФ: {uploaded_sf}
ВП: {uploaded_vp} | ФП: {uploaded_fp}
АП: {uploaded_ap} | ИТ: {uploaded_it} | К: {uploaded_k}

📍 Текущая позиция: {current_position}

ℹ️ Расшифровка ключей:
СВ - Сторис видео | СФ - Сторис фото
ВП - Видео пост | ФП - Фото пост
АП - Альбом | ИТ - IGTV | К - Клип
"""
        return info
    
    def run(self):
        """Запускает бота"""
        print("🤖 Запуск Telegram бота...")
        
        # Создаём необходимые директории
        Config.create_directories()
        
        # Запускаем бота
        while True:
            try:
                self.bot.infinity_polling()
            except Exception as e:
                print(f"❌ Ошибка бота: {e}")
                import time
                time.sleep(5)


if __name__ == "__main__":
    print("✅ Модуль bot.py загружен успешно!")

