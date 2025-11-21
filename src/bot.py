import json
import pathlib
import shutil
import threading
import time
import schedule
import telebot
from PIL import Image
from telebot import types
from telebot.types import InputMediaPhoto, InputMediaVideo
import sqlite3
from pytubefix import YouTube
import requests
from moviepy.editor import *
from pathlib import Path
from urllib.parse import quote
import os
from ast import literal_eval
from instagrapi import Client

from .config import Config
from .database import get_database
from .scheduler import StartLoop


class InstagramBot:
    """Telegram бот для управления Instagram Auto Publisher"""
    
    def __init__(self):
        """Инициализация бота"""
        self.bot = telebot.TeleBot(Config.TELEGRAM_BOT_TOKEN)
        self.db = get_database()
        self.admin_ids = Config.get_admin_ids()
        
        # Создаём Instagram клиент
        self.cl = Client(json.load(open(Config.INSTAGRAM_SESSION_FILE)))
        
        # Создаём планировщик
        self.loop = StartLoop(self.db, self.cl)
        
        # Дефолтное описание для контента
        self.default_caption = Config.DEFAULT_CAPTION
        
        # Приветственное сообщение
        self.hello = (
            "👋Привет!\n"
            "🤖Я умею скачивать контент из соц сетей:\n"
            "✅Instagram\n"
            "✅TikTok(без водянного знака)\n"
            "✅YouTube Shorts\n\n"
            "🔗Ты можешь отправить мне ссылку с желаемым контентом, который ты хочешь скачать!"
        )
        
        # Инициализируем клавиатуры
        self._create_keyboards()
        
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
        self.content_view = types.InlineKeyboardButton("Оценивать контент!", callback_data='content_rate')
        self.button_stat = types.InlineKeyboardButton("Обновить статистику", callback_data='stat')
        self.button_autopost = types.InlineKeyboardButton("Автопостинг", callback_data='autopost')
        self.admin_menu.add(self.content_view, self.button_stat, self.button_autopost)
        
        # Меню выбора типа контента
        self.rate_content = types.InlineKeyboardMarkup()
        self.rate_content.row_width = 1
        self.story_view = types.InlineKeyboardButton("Смотреть истории!", callback_data='story_view')
        self.reels_view = types.InlineKeyboardButton("Смотреть клипы!", callback_data='reels_view')
        self.igtv_view = types.InlineKeyboardButton("Смотреть IGTV", callback_data='igtv_view')
        self.other_posts_view = types.InlineKeyboardButton("Смотреть обычные посты!", callback_data='other_posts_view')
        self.albums_posts_view = types.InlineKeyboardButton("Смотреть альбомные посты!", callback_data='albums_posts_view')
        self.all_view = types.InlineKeyboardButton("Смотреть все подряд!", callback_data='all_view')
        self.back_admin = types.InlineKeyboardButton("Вернуться в меню!", callback_data='back_admin')
        self.rate_content.add(self.story_view, self.reels_view, self.igtv_view, self.other_posts_view, 
                             self.albums_posts_view, self.all_view, self.back_admin)
        
        # Кнопки оценки (тиндер)
        self.tinder = types.InlineKeyboardMarkup()
        self.tinder.row_width = 2
        self.yes = types.InlineKeyboardButton("✅", callback_data='yes')
        self.no = types.InlineKeyboardButton("❌", callback_data='no')
        self.tinder.add(self.yes, self.no)
        self.tinder.row_width = 1
        self.tinder.add(self.back_admin)
        
        # Кнопки оценки с кнопкой "В сторис"
        self.tinder_with_story = types.InlineKeyboardMarkup()
        self.tinder_with_story.row_width = 2
        self.tinder_with_story.add(self.yes, self.no)
        self.tinder_with_story.row_width = 1
        self.story_add = types.InlineKeyboardButton("В сторис", callback_data='to_story')
        self.tinder_with_story.add(self.story_add)
        self.tinder_with_story.row_width = 1
        self.tinder_with_story.add(self.back_admin)
        
        # Кнопка назад
        self.admin_back_mark = types.InlineKeyboardMarkup()
        self.admin_back_mark.row_width = 1
        self.admin_back_mark.add(self.back_admin)
        
        # Меню автопостинга
        self.button_settings_autopost = types.InlineKeyboardButton("Настройки автопостинга", callback_data='settings_autopost')
        self.button_menu = types.InlineKeyboardButton("В меню", callback_data="menu")
        
        # Меню настроек
        self.menu_settings_autopost = types.InlineKeyboardMarkup()
        self.menu_settings_autopost.row_width = 1
        self.button_timestamp_settings_autopost = types.InlineKeyboardButton("Настройка временных промежутков",
                                                                              callback_data='timestamp_settings')
        self.button_content_settings_autopost = types.InlineKeyboardButton("Настройка контента",
                                                                           callback_data='content_settings')
        self.menu_settings_autopost.add(self.button_timestamp_settings_autopost, 
                                       self.button_content_settings_autopost, self.button_menu)
        
        # Меню настроек времени
        self.menu_timestamp_autopost_settings = types.InlineKeyboardMarkup()
        self.menu_timestamp_autopost_settings.row_width = 1
        self.button_timestamp_morning = types.InlineKeyboardButton("Временные промежутки для утра",
                                                                   callback_data="timestamp_morning")
        self.button_timestamp_day = types.InlineKeyboardButton("Временные промежутки для дня", 
                                                               callback_data="timestamp_day")
        self.button_timestamp_evening = types.InlineKeyboardButton("Временные промежутки для вечера",
                                                                   callback_data="timestamp_evening")
        self.button_back_menu_settings = types.InlineKeyboardButton("Назад меню настроек", 
                                                                    callback_data="back_menu_settings")
        self.menu_timestamp_autopost_settings.add(self.button_timestamp_morning, self.button_timestamp_day,
                                                 self.button_timestamp_evening, self.button_back_menu_settings)
        
        # Меню настроек контента
        self.menu_content_autopost_settings = types.InlineKeyboardMarkup()
        self.menu_content_autopost_settings.row_width = 1
        self.button_content_morning = types.InlineKeyboardButton("Задать контент для утра",
                                                                 callback_data="content_morning")
        self.button_content_day = types.InlineKeyboardButton("Задать контент для дня", 
                                                            callback_data="content_day")
        self.button_content_evening = types.InlineKeyboardButton("Задать контент для вечера",
                                                                 callback_data="content_evening")
        self.menu_content_autopost_settings.add(self.button_content_morning, self.button_content_day,
                                               self.button_content_evening, self.button_back_menu_settings)
        
        # Меню "назад к настройкам"
        self.back_menu_settings = types.InlineKeyboardMarkup()
        self.back_menu_settings.row_width = 1
        self.back_menu_settings.add(self.button_back_menu_settings)
        
        # Меню "в меню"
        self.back_menu = types.InlineKeyboardMarkup()
        self.back_menu.row_width = 1
        self.back_menu.add(self.button_menu)
    
    # ========================================
    # Вспомогательные функции из OLD версии
    # ========================================
    
    def convert_webp_to_jpeg(self, story_pk):
        """Конвертирует webp в jpeg для stories"""
        for con in os.listdir("storys/photo"):
            if con.endswith(".webp"):
                im = Image.open("storys/photo/" + con).convert("RGB")
                im.save("storys/photo/" + str(story_pk) + ".jpg", "jpeg")
                os.remove("storys/photo/" + con)
    
    def convert_webp_to_jpeg_u(self, con):
        """Конвертирует webp в jpeg для постов"""
        if con.endswith(".webp"):
            fi = os.path.splitext(con)[0]
            im = Image.open("photo_posts/" + con).convert("RGB")
            im.save("photo_posts/" + str(fi) + ".jpg", "jpeg")
            os.remove("photo_posts/" + con)
            return str(fi+".jpg")
        else:
            return con
    
    def media_pk_cut(self, file, ask):
        """Достаёт описание контента из БД"""
        if ask == True:
            ppp = file.count('_')
            file = os.path.splitext(file)[0]
            file = (file.split('_')[ppp])
        try:
            baza = "SELECT content_description FROM contents WHERE media_pk = {}".format(file)
            result = self.db.cursor.execute(baza).fetchone()
            return (result[0])
        except:
            return (" ")
    
    def count_files(self):
        """Подсчитывает количество файлов"""
        count_story_photo = len(os.listdir("storys/photo"))
        count_story_video = len(os.listdir("storys/video"))
        count_post_video_temp = os.listdir("video_posts")
        co1 = 0
        for file in count_post_video_temp:
            if file.endswith(".mp4"):
                co1 += 1
        count_post_video = co1
        count_post_image = len(os.listdir("photo_posts"))
        count_albums = len(os.listdir("albums_posts"))
        count_igtv = len(os.listdir("video_posts/igtv"))
        count_clips = len(os.listdir("video_posts/clips"))
        count_msg = "Количество видео сторис: " + str(count_story_video) + "\nКоличество фото сторис: " + str(
            count_story_photo) + "\nКоличество видео постов: " + str(count_post_video) + "\nКоличество фото постов: " + str(
            count_post_image) + "\nКоличество альбомных постов: " + str(count_albums) + "\nКоличество IGTV: " + str(
            count_igtv) + "\nКоличество клипов: " + str(count_clips)
        return count_msg
    
    def set_morning_timestamp(self, message):
        """Устанавливает временной промежуток для утра"""
        self.db.set_setting("morning_time", message.text)
        self.bot.send_message(message.chat.id, text="Временной промежуток для утра добавлен!")
        self.bot.send_message(chat_id=message.chat.id, text="Выберите нужную категорию настроек:",
                            reply_markup=self.menu_settings_autopost)
    
    def set_day_timestamp(self, message):
        """Устанавливает временной промежуток для дня"""
        self.db.set_setting("day_time", message.text)
        self.bot.send_message(message.chat.id, text="Временной промежуток для дня добавлен!")
        self.bot.send_message(chat_id=message.chat.id, text="Выберите нужную категорию настроек:",
                            reply_markup=self.menu_settings_autopost)
    
    def set_evening_timestamp(self, message):
        """Устанавливает временной промежуток для вечера"""
        self.db.set_setting("evening_time", message.text)
        self.bot.send_message(message.chat.id, text="Временной промежуток для вечера добавлен!")
        self.bot.send_message(chat_id=message.chat.id, text="Выберите нужную категорию настроек:",
                            reply_markup=self.menu_settings_autopost)
    
    def set_morning_content(self, message):
        """Устанавливает контент для утра"""
        self.db.set_setting("morning_content", message.text)
        self.bot.send_message(message.chat.id, text="Контент для утра добавлен!")
        self.bot.send_message(chat_id=message.chat.id, text="Выберите нужную категорию настроек:",
                            reply_markup=self.menu_settings_autopost)
    
    def set_day_content(self, message):
        """Устанавливает контент для дня"""
        self.db.set_setting("day_content", message.text)
        self.bot.send_message(message.chat.id, text="Контент для дня добавлен!")
        self.bot.send_message(chat_id=message.chat.id, text="Выберите нужную категорию настроек:",
                            reply_markup=self.menu_settings_autopost)
    
    def set_evening_content(self, message):
        """Устанавливает контент для вечера"""
        self.db.set_setting("evening_content", message.text)
        self.bot.send_message(message.chat.id, text="Контент для вечера добавлен!")
        self.bot.send_message(chat_id=message.chat.id, text="Выберите нужную категорию настроек:",
                            reply_markup=self.menu_settings_autopost)
    
    def content_count(self):
        """Возвращает информацию о контенте для автопостинга"""
        morning_content = self.db.get_setting("morning_content")
        day_content = self.db.get_setting("day_content")
        evening_content = self.db.get_setting("evening_content")
        morning = morning_content.split("-")
        day = day_content.split("-")
        evening = evening_content.split("-")
        story_video = morning.count("СВ") + day.count("СВ") + evening.count("СВ")
        story_photo = morning.count("СФ") + day.count("СФ") + evening.count("СФ")
        post_video = morning.count("ВП") + day.count("ВП") + evening.count("ВП")
        post_photo = morning.count("ФП") + day.count("ФП") + evening.count("ФП")
        post_album = morning.count("АП") + day.count("АП") + evening.count("АП")
        igtv = morning.count("ИТ") + day.count("ИТ") + evening.count("ИТ")
        clips = morning.count("К") + day.count("К") + evening.count("К")
        story_video_u = self.db.get_setting("uploaded_video_story")
        story_photo_u = self.db.get_setting("uploaded_photo_story")
        post_video_u = self.db.get_setting("uploaded_video_posts")
        post_photo_u = self.db.get_setting("uploaded_photo_posts")
        post_album_u = self.db.get_setting("uploaded_album_posts")
        igtv_u = self.db.get_setting("uploaded_igtv")
        clips_u = self.db.get_setting("uploaded_clips")
        current_position_content = self.db.get_setting("current_position_content")
        morning_time = self.db.get_setting("morning_time")
        day_time = self.db.get_setting("day_time")
        evening_time = self.db.get_setting("evening_time")
        info = "Временные рамки:\nУтро: {}\nДень: {}\nВечер: {}\n\nЗагружено сегодня:\nВидео сторис: {}/{}\nФото сторис: {}/{}\nВидео постов: {}/{}\nФото поста: {}/{}\nАльбомных постов: {}/{}\nIGTV: {}/{}\nКлипов: {}/{}\n\nРасшифровка ключей: \nСВ - Сторис видео\nСФ - Сторис фото\nВП - Видео пост\nФП - Фото пост\nАП - Альбомный пост\nИТ - IGTV\nК - Клип\n\nУтренний контент: {}\nДневной контент: {}\nВечерний контент: {}\nТекущая позиция автопоста: {}".format(
            morning_time, day_time, evening_time, story_video_u, story_video, story_photo_u, story_photo, post_video_u, post_video, post_photo_u, post_photo,
            post_album_u, post_album, igtv_u, igtv, clips_u, clips, morning_content, day_content, evening_content, current_position_content)
        return info
    
    def get_menu_autopost(self, status):
        """Возвращает меню автопостинга в зависимости от статуса"""
        if status:
            autopost_menu = types.InlineKeyboardMarkup()
            autopost_menu.row_width = 1
            button_autopost_on_off = types.InlineKeyboardButton("Выключить автопостинг", callback_data='autopost_on_off')
            autopost_menu.add(button_autopost_on_off, self.button_settings_autopost, self.button_menu)
            return autopost_menu
        else:
            autopost_menu = types.InlineKeyboardMarkup()
            autopost_menu.row_width = 1
            button_autopost_on_off = types.InlineKeyboardButton("Включить автопостинг", callback_data='autopost_on_off')
            autopost_menu.add(button_autopost_on_off, self.button_settings_autopost, self.button_menu)
            return autopost_menu
    
    def get_time(self):
        """Получает временные рамки из БД"""
        morning = self.db.get_setting("morning_time").split("-")
        day = self.db.get_setting("day_time").split("-")
        evening = self.db.get_setting("evening_time").split("-")
        return morning, day, evening
    
    def set_active_content(self, id, content):
        """Устанавливает активный контент для пользователя"""
        self.db.set_user_state(id, 'active_content', str(content))
    
    def get_active_content(self, id):
        """Получает активный контент пользователя"""
        return self.db.get_user_state(id, 'active_content')
    
    def get_from_bd(self, id, column):
        """Получает значение из БД для пользователя"""
        return self.db.get_user_field(id, column)
    
    def set_to_bd(self, id, column, value):
        """Устанавливает значение в БД для пользователя"""
        self.db.set_user_field(id, column, str(value))
    
    def get_all_id(self, user_id):
        """Проверяет существование пользователя"""
        return self.db.user_exists(user_id)
    
    def db_add_user(self, user_id: int, user_name: str, user_surname: str, username: str):
        """Добавляет пользователя в БД"""
        self.db.add_user(user_id, user_name, user_surname, username)
    
    def db_add_content(self, user_id: int, link_content: str, media_pk: int, content_description: str):
        """Добавляет контент в БД"""
        return self.db.add_content(user_id, link_content, str(media_pk), content_description)
    
    def db_get_content(self, file):
        """Получает описание и тип контента из БД"""
        caption = ""
        content_id = str(os.path.splitext(os.path.basename(file))[0])
        result = self.db.cursor.execute(f"SELECT content_description FROM contents WHERE media_pk = '{content_id}'").fetchone()
        if result != None:
            desc = "\n\n*Описание:*\n`{}`".format(result[0])
        else:
            desc = "\n\n_Описание отсутствует!_"
        path = pathlib.Path(file)
        dlina = len(list(path.parents))
        no_need1 = str(list(path.parents)[-dlina])
        no_need2 = str(list(path.parents)[-dlina + 1])
        content_type = no_need1.replace(no_need2 + os.sep, "")
        if (content_type == 'photo') or (content_type == 'video'):
            caption = '*Тип контента:* _сторис_'
        if content_type == 'clips':
            caption = '*Тип контента:* _клип_'
        if content_type == 'igtv':
            caption = '*Тип контента:* _IGTV_'
        if (content_type == 'photo_posts') or (content_type == 'video_posts'):
            caption = '*Тип контента:* _обычный пост_'
        if content_type == 'albums_posts':
            caption = '*Тип контента:* _альбомный пост_'
        return desc, caption
    
    def construct(self, content):
        """Собирает контент из папок пользователей (функция из OLD версии)"""
        folders_workers = os.listdir("users_content")
        if content == 'storys':
            arr_content = []
            for folder in folders_workers:
                currentDirectory1 = pathlib.Path(f"users_content/{folder}/instagram/storys/photo")
                currentDirectory6 = pathlib.Path(f"users_content/{folder}/instagram/storys/video")
                currentDirectory2 = pathlib.Path(f"users_content/{folder}/pinterest/storys/video")
                currentDirectory3 = pathlib.Path(f"users_content/{folder}/pinterest/storys/photo")
                currentDirectory4 = pathlib.Path(f"users_content/{folder}/tiktok/storys/video")
                currentDirectory5 = pathlib.Path(f"users_content/{folder}/yt/storys/video")
                currentPattern = "*.*"
                for currentFile1 in currentDirectory1.glob(currentPattern):
                    arr_content.append(currentFile1)
                for currentFile2 in currentDirectory2.glob(currentPattern):
                    arr_content.append(currentFile2)
                for currentFile3 in currentDirectory3.glob(currentPattern):
                    arr_content.append(currentFile3)
                for currentFile4 in currentDirectory4.glob(currentPattern):
                    arr_content.append(currentFile4)
                for currentFile5 in currentDirectory5.glob(currentPattern):
                    arr_content.append(currentFile5)
                for currentFile6 in currentDirectory6.glob(currentPattern):
                    arr_content.append(currentFile6)
            return arr_content
        if content == 'clips':
            arr_content = []
            for folder in folders_workers:
                currentDirectory1 = pathlib.Path(f"users_content/{folder}/instagram/video_posts/clips")
                currentDirectory2 = pathlib.Path(f"users_content/{folder}/pinterest/video_posts/clips")
                currentDirectory4 = pathlib.Path(f"users_content/{folder}/tiktok/video_posts/clips")
                currentDirectory5 = pathlib.Path(f"users_content/{folder}/yt/video_posts/clips")
                currentPattern = "*.mp4"
                for currentFile1 in currentDirectory1.glob(currentPattern):
                    arr_content.append(currentFile1)
                for currentFile2 in currentDirectory2.glob(currentPattern):
                    arr_content.append(currentFile2)
                for currentFile4 in currentDirectory4.glob(currentPattern):
                    arr_content.append(currentFile4)
                for currentFile5 in currentDirectory5.glob(currentPattern):
                    arr_content.append(currentFile5)
            return arr_content
        if content == 'igtv':
            arr_content = []
            for folder in folders_workers:
                currentDirectory1 = pathlib.Path(f"users_content/{folder}/instagram/video_posts/igtv")
                currentDirectory2 = pathlib.Path(f"users_content/{folder}/pinterest/video_posts/igtv")
                currentDirectory4 = pathlib.Path(f"users_content/{folder}/tiktok/video_posts/igtv")
                currentDirectory5 = pathlib.Path(f"users_content/{folder}/yt/video_posts/igtv")
                currentPattern = "*.mp4"
                for currentFile1 in currentDirectory1.glob(currentPattern):
                    arr_content.append(currentFile1)
                for currentFile2 in currentDirectory2.glob(currentPattern):
                    arr_content.append(currentFile2)
                for currentFile4 in currentDirectory4.glob(currentPattern):
                    arr_content.append(currentFile4)
                for currentFile5 in currentDirectory5.glob(currentPattern):
                    arr_content.append(currentFile5)
            return arr_content
        if content == 'other_posts':
            arr_content = []
            for folder in folders_workers:
                currentDirectory1 = pathlib.Path(f"users_content/{folder}/instagram/photo_posts")
                currentDirectory2 = pathlib.Path(f"users_content/{folder}/instagram/video_posts")
                currentPattern = "*.*"
                for currentFile1 in currentDirectory1.glob(currentPattern):
                    arr_content.append(currentFile1)
                for currentFile2 in currentDirectory2.glob(currentPattern):
                    arr_content.append(currentFile2)
            return arr_content
        if content == 'albums_posts':
            arr_content = []
            for folder in folders_workers:
                currentDirectory1 = pathlib.Path(f"users_content/{folder}/instagram/albums_posts")
                for folder1 in os.listdir(currentDirectory1):
                    arr_content.append(pathlib.Path(f'users_content/{folder}/instagram/albums_posts/' + folder1))
            return arr_content
        if content == 'all':
            albums = []
            arr_content = []
            for folder in folders_workers:
                currentDirectory1 = pathlib.Path(f"users_content/{folder}/instagram/albums_posts")
                for folder1 in os.listdir(currentDirectory1):
                    albums.append(pathlib.Path(f'users_content/{folder}/instagram/albums_posts/' + folder1))
    
            for folder in folders_workers:
                currentDirectory1 = pathlib.Path(f"users_content/{folder}/instagram/photo_posts")
                currentDirectory2 = pathlib.Path(f"users_content/{folder}/instagram/video_posts")
                currentPattern = "*.*"
                for currentFile1 in currentDirectory1.glob(currentPattern):
                    arr_content.append(currentFile1)
                for currentFile2 in currentDirectory2.glob(currentPattern):
                    arr_content.append(currentFile2)
    
            for folder in folders_workers:
                currentDirectory1 = pathlib.Path(f"users_content/{folder}/instagram/video_posts/igtv")
                currentDirectory2 = pathlib.Path(f"users_content/{folder}/pinterest/video_posts/igtv")
                currentDirectory4 = pathlib.Path(f"users_content/{folder}/tiktok/video_posts/igtv")
                currentDirectory5 = pathlib.Path(f"users_content/{folder}/yt/video_posts/igtv")
                currentPattern = "*.mp4"
                for currentFile1 in currentDirectory1.glob(currentPattern):
                    arr_content.append(currentFile1)
                for currentFile2 in currentDirectory2.glob(currentPattern):
                    arr_content.append(currentFile2)
                for currentFile4 in currentDirectory4.glob(currentPattern):
                    arr_content.append(currentFile4)
                for currentFile5 in currentDirectory5.glob(currentPattern):
                    arr_content.append(currentFile5)
    
            for folder in folders_workers:
                currentDirectory1 = pathlib.Path(f"users_content/{folder}/instagram/video_posts/clips")
                currentDirectory2 = pathlib.Path(f"users_content/{folder}/pinterest/video_posts/clips")
                currentDirectory4 = pathlib.Path(f"users_content/{folder}/tiktok/video_posts/clips")
                currentDirectory5 = pathlib.Path(f"users_content/{folder}/yt/video_posts/clips")
                currentPattern = "*.mp4"
                for currentFile1 in currentDirectory1.glob(currentPattern):
                    arr_content.append(currentFile1)
                for currentFile2 in currentDirectory2.glob(currentPattern):
                    arr_content.append(currentFile2)
                for currentFile4 in currentDirectory4.glob(currentPattern):
                    arr_content.append(currentFile4)
                for currentFile5 in currentDirectory5.glob(currentPattern):
                    arr_content.append(currentFile5)
    
            for folder in folders_workers:
                currentDirectory1 = pathlib.Path(f"users_content/{folder}/instagram/storys/video")
                currentDirectory6 = pathlib.Path(f"users_content/{folder}/instagram/storys/photo")
                currentDirectory2 = pathlib.Path(f"users_content/{folder}/pinterest/storys/video")
                currentDirectory3 = pathlib.Path(f"users_content/{folder}/pinterest/storys/photo")
                currentDirectory4 = pathlib.Path(f"users_content/{folder}/tiktok/storys/video")
                currentDirectory5 = pathlib.Path(f"users_content/{folder}/yt/storys/video")
                currentPattern = "*.*"
                for currentFile1 in currentDirectory1.glob(currentPattern):
                    arr_content.append(currentFile1)
                for currentFile2 in currentDirectory2.glob(currentPattern):
                    arr_content.append(currentFile2)
                for currentFile3 in currentDirectory3.glob(currentPattern):
                    arr_content.append(currentFile3)
                for currentFile4 in currentDirectory4.glob(currentPattern):
                    arr_content.append(currentFile4)
                for currentFile5 in currentDirectory5.glob(currentPattern):
                    arr_content.append(currentFile5)
                for currentFile6 in currentDirectory6.glob(currentPattern):
                    arr_content.append(currentFile6)
    
            return albums, arr_content
    
    def create_album_media(self, path):
        """Создаёт media group для альбома"""
        media_group = []
        for file in os.listdir(path):
            if file.endswith('.mp4'):
                media_group.append(InputMediaVideo(open(str(path)+"/"+file, 'rb')))
            if file.endswith('.jpeg'):
                media_group.append(InputMediaPhoto(open(str(path)+"/"+file, 'rb')))
        return media_group
    
    def change_desc(self, message, old_message):
        """Изменяет описание контента (логика из OLD версии)"""
        active_menu = self.get_from_bd(message.chat.id, 'active_menu')
        active_content = self.get_active_content(message.chat.id)
        if ('albums_posts' in active_menu) or ('albums_posts' in active_content):
            messages = literal_eval(self.get_from_bd(message.chat.id, 'album_messages'))
            if len(messages) >= 1:
                for id in messages:
                    self.bot.delete_message(chat_id=message.chat.id, message_id=id)
        self.bot.delete_message(chat_id=message.chat.id, message_id=old_message)
        content_id = str(os.path.splitext(os.path.basename(self.get_active_content(message.chat.id)))[0])
        self.db.cursor.execute(f"UPDATE contents SET content_description = '{message.text}' WHERE media_pk = '{content_id}'")
        self.db.connection.commit()
        self.send_anket(message, active_menu)
    
    def send_anket(self, message, content_type):
        """Отправляет анкету для оценки контента (функция из OLD версии)"""
        if (content_type == 'storys'):
            content_list = self.construct(content_type)
            if len(content_list) != 0:
                content = content_list[0]
                desc, caption = self.db_get_content(content)
                self.bot.delete_message(message.chat.id, message.message_id)
                self.set_active_content(message.chat.id, content)
                if content.suffix == ".mp4":
                    video = open(content, 'rb')
                    self.bot.send_video(message.chat.id, video, caption=caption+desc, parse_mode= 'Markdown', reply_markup=self.tinder)
                    video.close()
                else:
                    photo = open(content, 'rb')
                    self.bot.send_photo(message.chat.id, photo, caption=caption+desc, parse_mode= 'Markdown', reply_markup=self.tinder)
                    photo.close()
            else:
                self.set_active_content(message.chat.id, "NO")
                self.bot.delete_message(message.chat.id, message.message_id)
                self.bot.send_message(chat_id=message.chat.id, text='Контент в данной категории отсутствует!', reply_markup=self.admin_back_mark)
        if (content_type == 'clips') or (content_type == 'igtv') or (content_type == 'other_posts'):
            content_list = self.construct(content_type)
            if len(content_list) != 0:
                content = content_list[0]
                desc, caption = self.db_get_content(content)
                self.bot.delete_message(message.chat.id, message.message_id)
                self.set_active_content(message.chat.id, content)
                if content.suffix == ".mp4":
                    video = open(content, 'rb')
                    msg = self.bot.send_video(message.chat.id, video, caption=caption + desc, parse_mode='Markdown',
                                       reply_markup=self.tinder_with_story)
                    video.close()
                    self.bot.register_next_step_handler(msg, self.change_desc, msg.id)
                else:
                    photo = open(content, 'rb')
                    msg = self.bot.send_photo(message.chat.id, photo, caption=caption + desc, parse_mode='Markdown',
                                       reply_markup=self.tinder_with_story)
                    photo.close()
                    self.bot.register_next_step_handler(msg, self.change_desc, msg.id)
            else:
                self.set_active_content(message.chat.id, "NO")
                self.bot.delete_message(message.chat.id, message.message_id)
                self.bot.send_message(chat_id=message.chat.id, text='Контент в данной категории отсутствует!',
                                     reply_markup=self.admin_back_mark)
        if content_type == 'albums_posts':
            albums_id = []
            albums_list = self.construct(content_type)
            if (len(albums_list) != 0):
                album = albums_list[0]
                desc, caption = self.db_get_content(album)
                media = self.create_album_media(album)
                self.bot.delete_message(message.chat.id, message.message_id)
                album_message = self.bot.send_media_group(message.chat.id, media=media)
                for message in album_message:
                    albums_id.append(message.id)
                self.set_to_bd(message.chat.id, 'album_messages', albums_id)
                msg = self.bot.send_message(message.chat.id, text=caption+desc, parse_mode= 'Markdown', reply_markup=self.tinder)
                self.set_active_content(message.chat.id, album)
                self.bot.register_next_step_handler(msg, self.change_desc, msg.id)
            else:
                self.set_active_content(message.chat.id, "NO")
                self.bot.delete_message(message.chat.id, message.message_id)
                self.bot.send_message(chat_id=message.chat.id, text='Контент в данной категории отсутствует!',
                                     reply_markup=self.admin_back_mark)
    
        if content_type == 'all':
            albums_list, content_list = self.construct(content_type)
            if (len(content_list) != 0):
                content = content_list[0]
                desc, caption = self.db_get_content(content)
                self.bot.delete_message(message.chat.id, message.message_id)
                self.set_active_content(message.chat.id, content)
                if content.suffix == ".mp4":
                    video = open(content, 'rb')
                    msg = self.bot.send_video(message.chat.id, video, caption = caption+desc, parse_mode= 'Markdown', reply_markup=self.tinder)
                    video.close()
                    if "сторис" in caption:
                        pass
                    else:
                        self.bot.register_next_step_handler(msg, self.change_desc, msg.id)
                else:
                    photo = open(content, 'rb')
                    msg = self.bot.send_photo(message.chat.id, photo, caption = caption+desc, parse_mode= 'Markdown', reply_markup=self.tinder)
                    photo.close()
                    if "сторис" in caption:
                        pass
                    else:
                        self.bot.register_next_step_handler(msg, self.change_desc, msg.id)
                return
            if (len(albums_list) != 0):
                albums_id = []
                album = albums_list[0]
                desc, caption = self.db_get_content(album)
                media = self.create_album_media(album)
                self.bot.delete_message(message.chat.id, message.message_id)
                album_message = self.bot.send_media_group(message.chat.id, media=media)
                for message in album_message:
                    albums_id.append(message.id)
                self.set_to_bd(message.chat.id, 'album_messages', albums_id)
                msg = self.bot.send_message(message.chat.id, text=caption+desc, parse_mode= 'Markdown', reply_markup=self.tinder)
                self.set_active_content(message.chat.id, album)
                self.bot.register_next_step_handler(msg, self.change_desc, msg.id)
                return
            else:
                self.set_active_content(message.chat.id, "NO")
                self.bot.delete_message(message.chat.id, message.message_id)
                self.bot.send_message(chat_id=message.chat.id, text='Контент в данной категории отсутствует!',
                                     reply_markup=self.admin_back_mark)
    
    def move(self, rate):
        """Перемещает файл в корневую папку"""
        path = pathlib.Path(rate)
        no_need = str(list(path.parents)[-4])
        no_need = no_need + os.sep
        path = str(path)
        path = path.replace(no_need, '')
        path2 = os.path.dirname(path) + os.sep
        shutil.move(rate, path2)
    
    def move_to_story(self, rate, story_path):
        """Перемещает контент в Stories"""
        path = pathlib.Path(rate)
        no_need = str(list(path.parents)[-4])
        no_need = no_need + os.sep
        path = str(path)
        new_path = os.path.join(story_path, os.path.basename(rate))
        shutil.move(rate, new_path)
    
    def get_active_id(self, rate):
        """Получает ID активного пользователя из пути"""
        path = pathlib.Path(rate)
        no_need = str(list(path.parents)[-3])
        active_id = no_need.replace(f"users_content{os.sep}", "")
        return active_id
    
    def get_count_content(self):
        """Получает количество непроверенного контента"""
        count_storys = len(self.construct('storys'))
        count_clips = len(self.construct('clips'))
        count_igtv = len(self.construct('igtv'))
        count_albums = len(self.construct('albums_posts'))
        count_other_posts = len(self.construct('other_posts'))
        total_count = count_storys+count_clips+count_igtv+count_albums+count_other_posts
        info = f"📁*Количество непроверенного контента:*\n📙_Сторис: {count_storys}\n📘Клипы: {count_clips}\n📗IGTV: {count_igtv}\n📕Обычные посты:_ {count_other_posts}\n📚Альбомные посты: {count_albums}\n*💾Всего:* {total_count}\n\nВыбери категорию:"
        return info
    
    # ========================================
    # Обработчики команд и сообщений
    # ========================================
    
    def _register_handlers(self):
        """Регистрирует все обработчики команд и callback'ов"""
        
        @self.bot.message_handler(commands=['start'])
        def start(message):
            if self.get_all_id(message.from_user.id):
                self.bot.send_message(message.chat.id, text=self.hello)
            else:
                self.db_add_user(user_id=message.from_user.id, user_name=message.from_user.first_name or "",
                                user_surname=message.from_user.last_name or "",
                                username=message.from_user.username or "")
                self.bot.send_message(message.chat.id, text=self.hello)
        
        @self.bot.message_handler(content_types=['text'])
        def link(message):
            text = message.text.strip()
            
            # Проверка команды входа в админку
            if text.lower() == 'admin' and self._is_admin(message.from_user.id):
                self.bot.send_message(message.chat.id, text="Админ-панель:", reply_markup=self.admin_menu)
                return
            
            # Здесь будет логика скачивания контента
            # (используем загрузчики из downloaders.py)
            from .downloaders import TikTokDownloader, YouTubeDownloader, InstagramDownloader
            
            if 'tiktok.com' in text:
                downloader = TikTokDownloader()
                success, msg, file_path = downloader.download(text, message.from_user.id)
                self.bot.send_message(message.chat.id, text=msg)
            elif 'youtube.com' in text:
                downloader = YouTubeDownloader()
                success, msg, file_path = downloader.download(text, message.from_user.id)
                self.bot.send_message(message.chat.id, text=msg)
            elif 'instagram.com' in text:
                downloader = InstagramDownloader()
                success, msg, file_path = downloader.download(text, message.from_user.id)
                self.bot.send_message(message.chat.id, text=msg)
            elif (text).startswith('@'):
                # Скачивание Instagram stories по username
                info = (text).split('-')
                if len(info) == 2:
                    # Здесь должна быть логика download_ig_storys
                    self.bot.send_message(message.chat.id, text="Функция скачивания по username временно недоступна")
                else:
                    self.bot.send_message(message.chat.id, text="❌Неверно указан запрос!\nВведите \\help и прочитайте инструкцию!")
            else:
                self.bot.send_message(message.chat.id, text="❌Неверная ссылка!")
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback(call):
            if not self._is_admin(call.from_user.id):
                self.bot.answer_callback_query(call.id, "❌ Доступ запрещён")
                return
            
            if call.message:
                if call.data == "back_admin":
                    self.bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
                    if "album" in str(self.get_active_content(call.message.chat.id)):
                        messages = literal_eval(self.get_from_bd(call.message.chat.id, 'album_messages'))
                        if len(messages) > 1:
                            for message in messages:
                                self.bot.delete_message(chat_id=call.message.chat.id, message_id=message)
                    self.bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
                    self.bot.send_message(chat_id=call.message.chat.id, text="Админ-панель:", reply_markup=self.admin_menu)
                    self.set_active_content(call.message.chat.id, "NO")
                    self.set_to_bd(call.message.chat.id, 'active_menu', 'menu')
                
                if call.data == "content_rate":
                    count = self.get_count_content()
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=count, parse_mode='Markdown', reply_markup=self.rate_content)
                
                if call.data == "story_view":
                    self.send_anket(call.message, 'storys')
                    self.set_to_bd(call.message.chat.id, 'active_menu', 'storys')
                
                if call.data == "reels_view":
                    self.send_anket(call.message, 'clips')
                    self.set_to_bd(call.message.chat.id, 'active_menu', 'clips')
                
                if call.data == 'igtv_view':
                    self.send_anket(call.message, 'igtv')
                    self.set_to_bd(call.message.chat.id, 'active_menu', 'igtv')
                
                if call.data == 'other_posts_view':
                    self.send_anket(call.message, 'other_posts')
                    self.set_to_bd(call.message.chat.id, 'active_menu', 'other_posts')
                
                if call.data == 'albums_posts_view':
                    self.send_anket(call.message, 'albums_posts')
                    self.set_to_bd(call.message.chat.id, 'active_menu', 'albums_posts')
                
                if call.data == 'all_view':
                    self.send_anket(call.message, 'all')
                    self.set_to_bd(call.message.chat.id, 'active_menu', 'all')
                
                if call.data == "yes":
                    self.bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
                    self.bot.answer_callback_query(callback_query_id=call.id, text='Принято')
                    rate = str(self.get_active_content(call.message.chat.id))
                    active_menu = self.get_from_bd(call.message.chat.id, 'active_menu')
                    active_id = self.get_active_id(rate)
                    id_media = str(os.path.splitext(os.path.basename(rate))[0])
                    result = self.db.cursor.execute(f"SELECT content_description FROM contents WHERE link_content = '{id_media}'").fetchone()
                    if result != None:
                        desc_db = result[0]
                    else:
                        desc_db = self.default_caption
                    if "album" in rate:
                        messages = literal_eval(self.get_from_bd(call.message.chat.id, 'album_messages'))
                        if len(messages) >= 1:
                            for message in messages:
                                self.bot.delete_message(chat_id=call.message.chat.id, message_id=message)
                        self.move(rate)
                        old_value = self.get_from_bd(active_id, "approved_content")
                        old_value = int(old_value) + 1
                        self.set_to_bd(active_id, "approved_content", old_value)
                        self.send_anket(call.message, active_menu)
                    else:
                        self.move(rate)
                        old_value = self.get_from_bd(active_id, "approved_content")
                        old_value = int(old_value) + 1
                        self.set_to_bd(active_id, "approved_content", old_value)
                        self.send_anket(call.message, active_menu)
                
                if call.data == 'no':
                    self.bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
                    self.bot.answer_callback_query(callback_query_id=call.id, text='Удалено!')
                    rate = str(self.get_active_content(call.message.chat.id))
                    active_menu = self.get_from_bd(call.message.chat.id, 'active_menu')
                    if "album" in rate:
                        messages = literal_eval(self.get_from_bd(call.message.chat.id, 'album_messages'))
                        if len(messages) >= 1:
                            for message in messages:
                                self.bot.delete_message(chat_id=call.message.chat.id, message_id=message)
                        shutil.rmtree(rate)
                    else:
                        os.remove(rate)
                    self.send_anket(call.message, active_menu)
                
                if call.data == 'to_story':
                    self.bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
                    self.bot.answer_callback_query(callback_query_id=call.id, text='Принято')
                    rate = str(self.get_active_content(call.message.chat.id))
                    active_menu = self.get_from_bd(call.message.chat.id, 'active_menu')
                    active_id = self.get_active_id(rate)
                    id_media = str(os.path.splitext(os.path.basename(rate))[0])
                    result = self.db.cursor.execute(f"SELECT content_description FROM contents WHERE link_content = '{id_media}'").fetchone()
                    if result != None:
                        desc_db = result[0]
                    else:
                        desc_db = self.default_caption
    
                    # Проверяем расширение файла
                    file_extension = os.path.splitext(rate)[1].lower()
    
                    # Если это видео
                    if file_extension in ['.mp4', '.mov', '.avi']:
                        story_path = "storys/video/"
                    # Если это фото
                    elif file_extension in ['.jpg', '.jpeg', '.png']:
                        story_path = "storys/photo/"
                    else:
                        self.bot.answer_callback_query(callback_query_id=call.id, text='Неподдерживаемый формат файла')
                        return
    
                    # Перемещаем в нужную папку
                    self.move_to_story(rate, story_path)
    
                    old_value = self.get_from_bd(active_id, "approved_content")
                    old_value = int(old_value) + 1
                    self.set_to_bd(active_id, "approved_content", old_value)
                    self.send_anket(call.message, active_menu)
                
                if call.data == "stat":
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Обновляю...",
                                              reply_markup=self.admin_menu)
                    msg = self.count_files()
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg, reply_markup=self.admin_menu)
    
                if call.data == "autopost":
                    if self.db.get_setting("autopost_status"):
                        status_autopost = "Включен"
                        menu_autopost = self.get_menu_autopost(True)
                    else:
                        status_autopost = "Выключен"
                        menu_autopost = self.get_menu_autopost(False)
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                              text="Статус автопостинга: " + status_autopost + "\n\n" + str(self.content_count()),
                                              reply_markup=menu_autopost)
                
                if call.data == "autopost_on_off":
                    if self.db.get_setting("autopost_status"):
                        status_autopost = "Выключен"
                        self.db.set_setting("autopost_status", 0)
                        menu_autopost = self.get_menu_autopost(False)
                        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                  text="Статус автопостинга: " + status_autopost + "\n\n" + str(self.content_count()),
                                                  reply_markup=menu_autopost)
                        self.loop.stop()
                    else:
                        status_autopost = "Включен"
                        self.db.set_setting("autopost_status", 1)
                        menu_autopost = self.get_menu_autopost(True)
                        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                  text="Статус автопостинга: " + status_autopost + "\n\n" + str(self.content_count()),
                                                  reply_markup=menu_autopost)
                        morning, day, evening = self.get_time()
                        self.loop.start(morning, day, evening)
    
                if call.data == "settings_autopost":
                    if self.db.get_setting("autopost_status"):
                        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                  text="Чтобы зайти в настройки нужно выключить автопостинг",
                                                  reply_markup=self.back_menu)
                    else:
                        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                  text="Выберите нужную категорию настроек:", reply_markup=self.menu_settings_autopost)
    
                if call.data == "timestamp_settings":
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Выберите фазу: ",
                                              reply_markup=self.menu_timestamp_autopost_settings)
    
                if call.data == "timestamp_morning":
                    msg = self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                    text="Утро:\nНапишите временные рамки:\nПример: 00:05:00-23:55:59\nСброс значений загруженного контента в 00:00:00 - это время не трогать!",
                                                    reply_markup=self.back_menu_settings)
                    self.bot.register_next_step_handler(msg, self.set_morning_timestamp)
    
                if call.data == "timestamp_day":
                    msg = self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                    text="День:\nНапишите временные рамки:\nПример: 00:05:00-23:55:59\nСброс значений загруженного контента в 00:00:00 - это время не трогать!",
                                                    reply_markup=self.back_menu_settings)
                    self.bot.register_next_step_handler(msg, self.set_day_timestamp)
    
                if call.data == "timestamp_evening":
                    msg = self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                    text="Вечер:\nНапишите временные рамки:\nПример: 00:05:00-23:55:59\nСброс значений загруженного контента в 00:00:00 - это время не трогать!",
                                                    reply_markup=self.back_menu_settings)
                    self.bot.register_next_step_handler(msg, self.set_evening_timestamp)
    
                if call.data == "content_settings":
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Выберите фазу: ",
                                              reply_markup=self.menu_content_autopost_settings)
    
                if call.data == "content_morning":
                    msg = self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                    text="Утро:\nНапишите в строгом порядке ключи контента:\nРасшифровка ключей: \nСВ - Сторис видео\nСФ - Сторис фото\nВП - Видео пост\nФП - Фото пост\nАП - Альбомный пост\nИТ - IGTV\nК - Клип\n\n Пример строки которую надо написать: \nСВ-СВ-СФ-ВП-ФП-АП-ИТ-К-К",
                                                    reply_markup=self.back_menu_settings)
                    self.bot.register_next_step_handler(msg, self.set_morning_content)
    
                if call.data == "content_day":
                    msg = self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                    text="День:\nНапишите в строгом порядке ключи контента:\nРасшифровка ключей: \nСВ - Сторис видео\nСФ - Сторис фото\nВП - Видео пост\nФП - Фото пост\nАП - Альбомный пост\nИТ - IGTV\nК - Клип\n\n Пример строки которую надо написать: \nСВ-СВ-СФ-ВП-ФП-АП-ИТ-К-К",
                                                    reply_markup=self.back_menu_settings)
                    self.bot.register_next_step_handler(msg, self.set_day_content)
    
                if call.data == "content_evening":
                    msg = self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                    text="Вечер:\nНапишите в строгом порядке ключи контента:\nРасшифровка ключей: \nСВ - Сторис видео\nСФ - Сторис фото\nВП - Видео пост\nФП - Фото пост\nАП - Альбомный пост\nИТ - IGTV\nК - Клип\n\n Пример строки которую надо написать: \nСВ-СВ-СФ-ВП-ФП-АП-ИТ-К-К",
                                                    reply_markup=self.back_menu_settings)
                    self.bot.register_next_step_handler(msg, self.set_evening_content)
    
                if call.data == "back_menu_settings":
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                              text="Выберите нужную категорию настроек:", reply_markup=self.menu_settings_autopost)
    
                if call.data == "menu":
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                              text='Нажми "Обновить" чтобы обновить статистику', reply_markup=self.admin_menu)
    
    def time_reset(self):
        """Сброс статистики в полночь"""
        self.db.set_setting("uploaded_video_story", 0)
        self.db.set_setting("uploaded_photo_story", 0)
        self.db.set_setting("uploaded_video_posts", 0)
        self.db.set_setting("uploaded_photo_posts", 0)
        self.db.set_setting("uploaded_album_posts", 0)
        self.db.set_setting("uploaded_igtv", 0)
        self.db.set_setting("uploaded_clips", 0)
        self.db.set_setting("current_position_content", "0-0")
        print("Произведен сброс значений загруженного контента")
    
    def mainloop(self):
        """Основной цикл бота"""
        while True:
            try:
                self.bot.infinity_polling()
            except:
                time.sleep(5)
    
    def resettime(self):
        """Планировщик сброса статистики"""
        schedule.every().day.at(Config.DAILY_RESET_TIME).do(self.time_reset)
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def run(self):
        """Запускает бота"""
        print("🤖 Запуск Telegram бота...")
        
        # Создаём необходимые директории
        Config.create_directories()
        
        # Выключаем автопостинг при старте
        self.db.set_setting("autopost_status", 0)
        
        # Запускаем потоки
        t1 = threading.Thread(target=self.mainloop)
        t2 = threading.Thread(target=self.resettime)
        t1.start()
        t2.start()


if __name__ == "__main__":
    print("✅ Модуль bot.py загружен успешно!")
