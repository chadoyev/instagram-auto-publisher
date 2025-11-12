import json
import pathlib
import shutil
import threading
import time
import schedule
import telebot
from PIL.Image import Image
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
import loopbot
from instagrapi import Client

loop = loopbot.StartLoop()
ip_host = ''
token = ""
bot = telebot.TeleBot(token)
tg1 = 
tg2 = 
cl = Client(json.load(open('authorize.json')))

conn = sqlite3.connect('db.db', check_same_thread=False)
cursor = conn.cursor()

name_pablik = "Подписывайся на ..." #дефолтное описание для контента

subscribe = types.InlineKeyboardMarkup()
subscribe.row_width = 1
admin_menu = types.InlineKeyboardMarkup()
admin_menu.row_width = 1
rate_content = types.InlineKeyboardMarkup()
rate_content.row_width = 1
tinder = types.InlineKeyboardMarkup()
tinder.row_width = 2
admin_back_mark = types.InlineKeyboardMarkup()
admin_back_mark.row_width = 1
statistics_menu = types.InlineKeyboardMarkup()
statistics_menu.row_width = 1
tinder_with_story = types.InlineKeyboardMarkup()
tinder_with_story.row_width = 2
upload = types.InlineKeyboardMarkup()
upload.row_width = 1
back_menu = types.InlineKeyboardMarkup()
back_menu.row_width = 1
menu_settings_autopost = types.InlineKeyboardMarkup()
menu_settings_autopost.row_width = 1
menu_timestamp_autopost_settings = types.InlineKeyboardMarkup()
menu_timestamp_autopost_settings.row_width = 1
menu_content_autopost_settings = types.InlineKeyboardMarkup()
menu_content_autopost_settings.row_width = 1
back_menu_settings = types.InlineKeyboardMarkup()
back_menu_settings.row_width = 1

content_view = types.InlineKeyboardButton("Оценивать контент!", callback_data='content_rate')
story_view = types.InlineKeyboardButton("Смотреть истории!", callback_data='story_view')
reels_view = types.InlineKeyboardButton("Смотреть клипы!", callback_data='reels_view')
igtv_view = types.InlineKeyboardButton("Смотреть IGTV", callback_data='igtv_view')
albums_posts_view = types.InlineKeyboardButton("Смотреть альбомные посты!", callback_data='albums_posts_view')
other_posts_view = types.InlineKeyboardButton("Смотреть обычные посты!", callback_data='other_posts_view')
all_view = types.InlineKeyboardButton("Смотреть все подряд!", callback_data='all_view')
yes = types.InlineKeyboardButton("✅", callback_data='yes')
no = types.InlineKeyboardButton("❌", callback_data='no')
story_add = types.InlineKeyboardButton("В сторис", callback_data='to_story')
back_admin = types.InlineKeyboardButton("Вернуться в меню!",callback_data='back_admin')
button_stat = types.InlineKeyboardButton("Обновить статистику", callback_data='stat')
button_autopost = types.InlineKeyboardButton("Автопостинг", callback_data='autopost')
button_settings_autopost = types.InlineKeyboardButton("Настройки автопостинга", callback_data='settings_autopost')
button_autopost_on_off = types.InlineKeyboardButton("Включить автопостинг", callback_data='autopost_on_off')
button_menu = types.InlineKeyboardButton("В меню", callback_data="menu")
button_timestamp_settings_autopost = types.InlineKeyboardButton("Настройка временных промежутков",
                                                                callback_data='timestamp_settings')
button_timestamp_morning = types.InlineKeyboardButton("Временные промежутки для утра",
                                                      callback_data="timestamp_morning")
button_timestamp_day = types.InlineKeyboardButton("Временные промежутки для дня", callback_data="timestamp_day")
button_timestamp_evening = types.InlineKeyboardButton("Временные промежутки для вечера",
                                                      callback_data="timestamp_evening")
button_content_settings_autopost = types.InlineKeyboardButton("Настройка контента",
                                                              callback_data='content_settings')
button_content_morning = types.InlineKeyboardButton("Задать контент для утра",
                                                    callback_data="content_morning")
button_content_day = types.InlineKeyboardButton("Задать контент для дня", callback_data="content_day")
button_content_evening = types.InlineKeyboardButton("Задать контент для вечера",
                                                    callback_data="content_evening")
button_back_menu_settings = types.InlineKeyboardButton("Назад меню настроек", callback_data="back_menu_settings")


admin_menu.add(content_view, button_stat, button_autopost)
rate_content.add(story_view, reels_view, igtv_view, other_posts_view, albums_posts_view, all_view, back_admin)
tinder.add(yes, no, back_admin)
tinder_with_story.add(yes, no)
tinder_with_story.row_wight = 1
tinder_with_story.add(story_add)
tinder_with_story.row_wight = 1
tinder_with_story.add(back_admin)
admin_back_mark.add(back_admin)
back_menu.add(button_menu)
menu_settings_autopost.add(button_timestamp_settings_autopost, button_content_settings_autopost, button_menu)
menu_timestamp_autopost_settings.add(button_timestamp_morning, button_timestamp_day, button_timestamp_evening,
                                     button_back_menu_settings)
menu_content_autopost_settings.add(button_content_morning, button_content_day, button_content_evening,
                                   button_back_menu_settings)
back_menu_settings.add(button_back_menu_settings)


def convert_webp_to_jpeg(story_pk):
    for con in os.listdir("storys/photo"):
        if con.endswith(".webp"):
            im = Image.open("storys/photo/" + con).convert("RGB")
            im.save("storys/photo/" + str(story_pk) + ".jpg", "jpeg")
            os.remove("storys/photo/" + con)  # конвертирование формата (ГОТОВО)

def convert_webp_to_jpeg_u(con):
    if con.endswith(".webp"):
        fi = os.path.splitext(con)[0]
        im = Image.open("photo_posts/" + con).convert("RGB")
        im.save("photo_posts/" + str(fi) + ".jpg", "jpeg")
        os.remove("photo_posts/" + con)
        return str(fi+".jpg")
    else:
        return con

# функции постера
def media_pk_cut(file, ask):
    if ask == True:
        ppp = file.count('_')
        file = os.path.splitext(file)[0]
        file = (file.split('_')[ppp])
    try:
        baza = "SELECT media_description FROM media_descriptions WHERE media_pk = {}".format(file)
        result = cursor.execute(baza).fetchone()
        return (result[0])
    except:
        return (" ")  # достать описание с БД(ГОТОВО)

def count_files():
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

def set_morning_timestamp(message):
    set_to_bd_settings("morning_time", message.text)
    bot.send_message(message.chat.id, text="Временной промежуток для утра добавлен!")
    bot.send_message(chat_id=message.chat.id, text="Выберите нужную категорию настроек:",
                     reply_markup=menu_settings_autopost)

def set_day_timestamp(message):
    set_to_bd_settings("day_time", message.text)
    bot.send_message(message.chat.id, text="Временной промежуток для дня добавлен!")
    bot.send_message(chat_id=message.chat.id, text="Выберите нужную категорию настроек:",
                     reply_markup=menu_settings_autopost)

def set_evening_timestamp(message):
    set_to_bd_settings("evening_time", message.text)
    bot.send_message(message.chat.id, text="Временной промежуток для вечера добавлен!")
    bot.send_message(chat_id=message.chat.id, text="Выберите нужную категорию настроек:",
                     reply_markup=menu_settings_autopost)

def set_morning_content(message):
    set_to_bd_settings("morning_content", message.text)
    bot.send_message(message.chat.id, text="Контент для утра добавлен!")
    bot.send_message(chat_id=message.chat.id, text="Выберите нужную категорию настроек:",
                     reply_markup=menu_settings_autopost)

def set_day_content(message):
    set_to_bd_settings("day_content", message.text)
    bot.send_message(message.chat.id, text="Контент для дня добавлен!")
    bot.send_message(chat_id=message.chat.id, text="Выберите нужную категорию настроек:",
                     reply_markup=menu_settings_autopost)

def set_evening_content(message):
    set_to_bd_settings("evening_content", message.text)
    bot.send_message(message.chat.id, text="Контент для вечера добавлен!")
    bot.send_message(chat_id=message.chat.id, text="Выберите нужную категорию настроек:",
                     reply_markup=menu_settings_autopost)

def content_count():
    morning_content = get_from_bd_settings("morning_content")
    day_content = get_from_bd_settings("day_content")
    evening_content = get_from_bd_settings("evening_content")
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
    story_video_u = get_from_bd_settings("uploaded_video_story")
    story_photo_u = get_from_bd_settings("uploaded_photo_story")
    post_video_u = get_from_bd_settings("uploaded_video_posts")
    post_photo_u = get_from_bd_settings("uploaded_photo_posts")
    post_album_u = get_from_bd_settings("uploaded_album_posts")
    igtv_u = get_from_bd_settings("uploaded_igtv")
    clips_u = get_from_bd_settings("uploaded_clips")
    current_position_content = get_from_bd_settings("current_position_content")
    morning_time = get_from_bd_settings("morning_time")
    day_time = get_from_bd_settings("day_time")
    evening_time = get_from_bd_settings("evening_time")
    info = "Временные рамки:\nУтро: {}\nДень: {}\nВечер: {}\n\nЗагружено сегодня:\nВидео сторис: {}/{}\nФото сторис: {}/{}\nВидео постов: {}/{}\nФото поста: {}/{}\nАльбомных постов: {}/{}\nIGTV: {}/{}\nКлипов: {}/{}\n\nРасшифровка ключей: \nСВ - Сторис видео\nСФ - Сторис фото\nВП - Видео пост\nФП - Фото пост\nАП - Альбомный пост\nИТ - IGTV\nК - Клип\n\nУтренний контент: {}\nДневной контент: {}\nВечерний контент: {}\nТекущая позиция автопоста: {}".format(
        morning_time, day_time, evening_time, story_video_u, story_video, story_photo_u, story_photo, post_video_u, post_video, post_photo_u, post_photo,
        post_album_u, post_album, igtv_u, igtv, clips_u, clips, morning_content, day_content, evening_content, current_position_content)
    return info

def get_menu_autopost(status):
    if status:
        autopost_menu = types.InlineKeyboardMarkup()
        autopost_menu.row_width = 1
        button_autopost_on_off = types.InlineKeyboardButton("Выключить автопостинг", callback_data='autopost_on_off')
        autopost_menu.add(button_autopost_on_off, button_settings_autopost, button_menu)
        return autopost_menu
    else:
        autopost_menu = types.InlineKeyboardMarkup()
        autopost_menu.row_width = 1
        button_autopost_on_off = types.InlineKeyboardButton("Включить автопостинг", callback_data='autopost_on_off')
        autopost_menu.add(button_autopost_on_off, button_settings_autopost, button_menu)
        return autopost_menu

def get_time():
    morning = get_from_bd_settings("morning_time").split("-")
    day = get_from_bd_settings("day_time").split("-")
    evening = get_from_bd_settings("evening_time").split("-")
    return morning, day, evening

def set_active_content(id, content):
    cursor.execute('UPDATE users SET active_content = ? WHERE user_id = ?',(str(content), id,))
    conn.commit()

def get_active_content(id):
    cursor.execute("SELECT active_content FROM users WHERE user_id = {}".format(id))
    return cursor.fetchone()[0]

def get_from_bd(id, column):
    cursor.execute("SELECT {} FROM users WHERE user_id = {}".format(column,id))
    return cursor.fetchone()[0]

def set_to_bd(id, column, value):
    cursor.execute('UPDATE users SET {} = ? WHERE user_id = ?'.format(column), (str(value), id,))
    conn.commit()

def set_to_bd_settings(column, value):
    print(column)
    cursor.execute('UPDATE settings SET "{}"=?'.format(column.replace('"', '""')),
                   (value,))
    conn.commit()

def get_from_bd_settings(column):
    baza = "SELECT {} FROM settings".format(column)
    result = cursor.execute(baza).fetchone()
    return (result[0])

def get_all_id(user_id):
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    for row in rows:
        if user_id in row:
            return True
    return False

def db_add_user(user_id: int, user_name: str, user_surname: str, username: str):
    cursor.execute('INSERT INTO users (user_id, user_name, user_surname, username) VALUES (?, ?, ?, ?)',
                   (user_id, user_name, user_surname, username))
    conn.commit()

def db_add_content(user_id: int, link_content: str, media_pk: int, content_description: str):
    cursor.execute('INSERT INTO contents (user_id, link_content, media_pk, content_description) VALUES (?, ?, ?, ?)',
                   (user_id, link_content, media_pk, content_description))
    conn.commit()

def db_get_content(file):
    caption = ""
    content_id = str(os.path.splitext(os.path.basename(file))[0])
    cursor.execute(f"SELECT content_description FROM contents WHERE link_content = '{content_id}'")
    desc = cursor.fetchone()
    if desc != None:
        desc = "\n\n*Описание:*\n`{}`".format(desc[0])
    else:
        desc = "\n\n_Описание отсутствует!_"
    path = pathlib.WindowsPath(file)
    dlina = len(list(path.parents))
    no_need1 = str(list(path.parents)[-dlina])
    no_need2 = str(list(path.parents)[-dlina + 1])
    content_type = no_need1.replace(no_need2 + "\\", "")
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


def tiktok_download(url, message):
    Path(f'users_content/{message.chat.id}/tiktok/storys/video').mkdir(parents=True, exist_ok=True)
    Path(f'users_content/{message.chat.id}/tiktok/video_posts/clips').mkdir(parents=True, exist_ok=True)
    Path(f'users_content/{message.chat.id}/tiktok/video_posts/igtv').mkdir(parents=True, exist_ok=True)
    mess = bot.send_message(message.chat.id, text='Скачиваю...')
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.66'
    }
    tiktok_api_link = f'http://{ip_host}/api/hybrid/video_data?url={url}'
    res = requests.get(tiktok_api_link, headers=headers).text
    result = json.loads(res)
    video_id = result["data"]["aweme_id"]
    nowm = result["data"]["video"]["play_addr"]["url_list"][0]
    author = result["data"]["author"]["nickname"]
    desc = result["data"]["desc"]
    if desc == "":
        desc = name_pablik + "\n\n" + "Автор(ТТ): " + author
    else:
        desc = desc + "\n\n" + "Автор(ТТ): " + author
    if os.path.exists(f'users_content/{message.chat.id}/tiktok/storys/video/' + f'{video_id}.mp4'):
        video_1 = open(f'users_content/{message.chat.id}/tiktok/storys/video/' + f'{video_id}.mp4', 'rb')
        bot.delete_message(mess.chat.id, mess.message_id)
        bot.send_video(message.chat.id, video_1, caption=desc)
        video_1.close()
        return
    elif os.path.exists(f'users_content/{message.chat.id}/tiktok/video_posts/clips/' + f'{video_id}.mp4'):
        video_1 = open(f'users_content/{message.chat.id}/tiktok/video_posts/clips/' + f'{video_id}.mp4', 'rb')
        bot.delete_message(mess.chat.id, mess.message_id)
        bot.send_video(message.chat.id, video_1, caption=desc)
        video_1.close()
        return
    elif os.path.exists(f'users_content/{message.chat.id}/tiktok/video_posts/igtv/' + f'{video_id}.mp4'):
        video_1 = open(f'users_content/{message.chat.id}/tiktok/video_posts/igtv/' + f'{video_id}.mp4' + ".mp4", 'rb')
        bot.delete_message(mess.chat.id, mess.message_id)
        bot.send_video(message.chat.id, video_1, caption=desc)
        video_1.close()
        return
    else:
        resp = requests.get(nowm, stream=True)
        video = open(r'{}.mp4'.format(video_id), "wb")
        video.write(resp.content)
        video.close()
        video_1 = open(r'{}.mp4'.format(video_id), 'rb')
        bot.delete_message(mess.chat.id, mess.message_id)
        bot.send_video(message.chat.id, video_1, caption=desc)
        video_1.close()
        clip = VideoFileClip("{}.mp4".format(video_id))
        video_duration = clip.duration
        clip.close()
        if video_duration < 15:
            shutil.move("{}.mp4".format(video_id), f'users_content/{message.chat.id}/tiktok/storys/video/')
        if video_duration > 15 and video_duration < 60:
            shutil.move("{}.mp4".format(video_id), f'users_content/{message.chat.id}/tiktok/video_posts/clips/')
        if video_duration > 60:
            shutil.move("{}.mp4".format(video_id), f'users_content/{message.chat.id}/tiktok/video_posts/igtv/')
        try:
            db_add_content(user_id=message.chat.id, link_content=video_id, media_pk= video_id, content_description=desc)
            old_value = get_from_bd(message.chat.id, "tiktok_loaded")
            old_value = int(old_value) + 1
            set_to_bd(message.chat.id, "tiktok_loaded", old_value)
        except sqlite3.IntegrityError:
            if get_from_bd(message.chat.id, 'worker'):
                bot.send_message(message.chat.id, text='Такой контент уже был загружен!')
        print("Скачал тикток видос: "+str(url))

def youtube_download(url, message):
    try:
        Path(f'users_content/{message.chat.id}/yt/storys/video').mkdir(parents=True, exist_ok=True)
        Path(f'users_content/{message.chat.id}/yt/video_posts/clips').mkdir(parents=True, exist_ok=True)
        Path(f'users_content/{message.chat.id}/yt/video_posts/igtv').mkdir(parents=True, exist_ok=True)
        mess = bot.send_message(message.chat.id, text='Скачиваю...')
        yt = YouTube(url)
        title = yt.title
        author = yt.author
        print(title)
        print(author)
        if title == "":
            title = name_pablik+ "\n\n"+"Автор(YТ): " + author
        else:
            title = title + "\n\n" + "Автор(YТ): " + author
        video_id = yt.video_id
        if os.path.exists(f'users_content/{message.chat.id}/yt/storys/video/'+f'{video_id}.mp4'):
            video_1 = open(video_id + ".mp4", 'rb')
            bot.delete_message(mess.chat.id, mess.message_id)
            bot.send_video(message.chat.id, video_1, caption=title)
            video_1.close()
            return
        elif os.path.exists(f'users_content/{message.chat.id}/yt/video_posts/clips/'+f'{video_id}.mp4'):
            video_1 = open(video_id + ".mp4", 'rb')
            bot.delete_message(mess.chat.id, mess.message_id)
            bot.send_video(message.chat.id, video_1, caption=title)
            video_1.close()
            return
        elif os.path.exists(f'users_content/{message.chat.id}/yt/video_posts/igtv/'+f'{video_id}.mp4'):
            video_1 = open(video_id + ".mp4", 'rb')
            bot.delete_message(mess.chat.id, mess.message_id)
            bot.send_video(message.chat.id, video_1, caption=title)
            video_1.close()
            return
        else:
            stream = yt.streams.get_highest_resolution()
            stream.download("", video_id+".mp4")
            clip = VideoFileClip("{}.mp4".format(video_id))
            video_duration = clip.duration
            clip.close()
            video_1 = open(video_id + ".mp4", 'rb')
            bot.delete_message(mess.chat.id, mess.message_id)
            if video_duration > 0 and video_duration < 240:
                bot.send_video(message.chat.id, video_1, caption=title)
            else:
                bot.send_message(message.chat.id, text = "Не удалось скачать, видео слишком длинное!")
            video_1.close()
            if video_duration < 15:
                shutil.move("{}.mp4".format(video_id), f'users_content/{message.chat.id}/yt/storys/video/')
            if video_duration > 15 and video_duration < 60:
                shutil.move("{}.mp4".format(video_id), f'users_content/{message.chat.id}/yt/video_posts/clips/')
            if video_duration > 60 and video_duration < 240:
                shutil.move("{}.mp4".format(video_id), f'users_content/{message.chat.id}/yt/video_posts/igtv/')
            if video_duration > 240:
                os.remove("{}.mp4".format(video_id))
            try:
                db_add_content(user_id=message.chat.id, link_content=str(video_id), media_pk = video_id, content_description=title)
                old_value = get_from_bd(message.chat.id, "yt_loaded")
                old_value = int(old_value) + 1
                set_to_bd(message.chat.id, "yt_loaded", old_value)
            except sqlite3.IntegrityError:
                if get_from_bd(message.chat.id, 'worker'):
                    bot.send_message(message.chat.id, text='Такой контент уже был загружен!')
            print("Скачал YT видос: " + str(url))
    except Exception as e:
        print("Ошибка при скачивании YТ видео: " + str(e))
        bot.send_message(message.chat.id, text="Произошла ошибка при скачивании! Попробуйте позже...")

def create_album_media(path):
    media_group = []
    for file in os.listdir(path):
        if file.endswith('.mp4'):
            media_group.append(InputMediaVideo(open(str(path)+"/"+file,
                       'rb')))
        if file.endswith('.jpeg'):
            media_group.append(InputMediaPhoto(open(str(path)+"/"+file,
                       'rb')))
    return media_group

def instagram_download(url, message):
    caption = ''
    try:
        Path(f'users_content/{message.chat.id}/instagram/storys/video').mkdir(parents=True, exist_ok=True)
        Path(f'users_content/{message.chat.id}/instagram/storys/photo').mkdir(parents=True, exist_ok=True)
        Path(f'users_content/{message.chat.id}/instagram/video_posts/igtv').mkdir(parents=True, exist_ok=True)
        Path(f'users_content/{message.chat.id}/instagram/video_posts/clips').mkdir(parents=True, exist_ok=True)
        Path(f'users_content/{message.chat.id}/instagram/photo_posts').mkdir(parents=True, exist_ok=True)
        Path(f'users_content/{message.chat.id}/instagram/albums_posts').mkdir(parents=True, exist_ok=True)
        mess = bot.send_message(message.chat.id, text='Скачиваю...')
        if "stories" in url:
            a = "https://api.hikerapi.com/v1/story/by/url?url={}&access_key=API_KEY".format(
                quote(url))
            response = requests.get(url=a)
            result = json.loads(response.text)
            media_type = result["media_type"]
            pk = result["pk"]
            if media_type == 2:
                if os.path.exists(f'users_content/{message.chat.id}/instagram/storys/video/' + r'{}.mp4'.format(pk)):
                    video_1 = open(f'users_content/{message.chat.id}/instagram/storys/video/' + r'{}.mp4'.format(pk),
                                   'rb')
                    bot.delete_message(mess.chat.id, mess.message_id)
                    bot.send_video(message.chat.id, video_1)
                    video_1.close()
                    return
                else:
                    b = "https://api.hikerapi.com/v1/story/download?id={}&access_key=API_KEY".format(
                        result["id"])
                    response = requests.get(url=b)
                    video = open(f'users_content/{message.chat.id}/instagram/storys/video/'+r'{}.mp4'.format(pk), "wb")
                    video.write(response.content)
                    video.close()
                    video_1 = open(f'users_content/{message.chat.id}/instagram/storys/video/' + r'{}.mp4'.format(pk), 'rb')
                    bot.delete_message(mess.chat.id, mess.message_id)
                    bot.send_video(message.chat.id, video_1)
                    video_1.close()
                    caption = name_pablik
            if media_type == 1:
                if os.path.exists(f'users_content/{message.chat.id}/instagram/storys/photo/' + r'{}.jpeg'.format(pk)):
                    photo_1 = open(f'users_content/{message.chat.id}/instagram/storys/photo/' + r'{}.jpeg'.format(pk),
                                   'rb')
                    bot.delete_message(mess.chat.id, mess.message_id)
                    bot.send_photo(message.chat.id, photo_1)
                    photo_1.close()
                    return
                else:
                    b = "https://api.hikerapi.com/v1/story/download?id={}&access_key=API_KEY".format(
                        result["id"])
                    response = requests.get(url=b)
                    photo = open(f'users_content/{message.chat.id}/instagram/storys/photo/' + r'{}.jpeg'.format(pk), "wb")
                    photo.write(response.content)
                    photo.close()
                    photo_1 = open(f'users_content/{message.chat.id}/instagram/storys/photo/'+r'{}.jpeg'.format(pk), 'rb')
                    bot.delete_message(mess.chat.id, mess.message_id)
                    bot.send_photo(message.chat.id, photo_1)
                    photo_1.close()
                    caption = name_pablik
            print("Скачал инста-сторис: " + str(url))
        else:
            a = "https://api.hikerapi.com/v1/media/by/url?url={}&access_key=API_KEY".format(
                quote(url))
            response = requests.get(url=a)
            result = json.loads(response.text)
            media_type = result["media_type"]
            product_type = result["product_type"]
            pk = result["pk"]
            caption = result["caption_text"]
            if caption == "":
                caption = name_pablik
            if media_type == 2:
                video_url = result["video_url"]
                if product_type == "feed":  # скачивание постов с обычным видео
                    if os.path.exists(f'users_content/{message.chat.id}/instagram/video_posts/' + r'{}.mp4'.format(pk)):
                        video_1 = open(f'users_content/{message.chat.id}/instagram/video_posts/' + r'{}.mp4'.format(pk),
                                       'rb')
                        bot.delete_message(mess.chat.id, mess.message_id)
                        bot.send_video(message.chat.id, video_1, caption=caption)
                        video_1.close()
                        return
                    else:
                        response = requests.get(url=video_url)
                        video = open(f'users_content/{message.chat.id}/instagram/video_posts/' + r'{}.mp4'.format(pk),
                                     "wb")
                        video.write(response.content)
                        video.close()
                        video_1 = open(f'users_content/{message.chat.id}/instagram/video_posts/'+r'{}.mp4'.format(pk), 'rb')
                        bot.delete_message(mess.chat.id, mess.message_id)
                        bot.send_video(message.chat.id, video_1, caption=caption)
                        video_1.close()
                if product_type == "igtv":  # скачивание постов с видео igtv
                    if os.path.exists(f'users_content/{message.chat.id}/instagram/video_posts/igtv/' + r'{}.mp4'.format(pk)):
                        video_1 = open(
                            f'users_content/{message.chat.id}/instagram/video_posts/igtv/' + r'{}.mp4'.format(pk),
                            'rb')
                        bot.delete_message(mess.chat.id, mess.message_id)
                        bot.send_video(message.chat.id, video_1, caption=caption)
                        video_1.close()
                        return
                    else:
                        response = requests.get(url=video_url)
                        video = open(f'users_content/{message.chat.id}/instagram/video_posts/igtv/' + r'{}.mp4'.format(pk),
                                     "wb")
                        video.write(response.content)
                        video.close()
                        video_1 = open(f'users_content/{message.chat.id}/instagram/video_posts/igtv/' + r'{}.mp4'.format(pk),
                                       'rb')
                        bot.delete_message(mess.chat.id, mess.message_id)
                        bot.send_video(message.chat.id, video_1, caption=caption)
                        video_1.close()
                if product_type == "clips":  # скачивание клипов
                    if os.path.exists(f'users_content/{message.chat.id}/instagram/video_posts/clips/' + r'{}.mp4'.format(pk)):
                        video_1 = open(
                            f'users_content/{message.chat.id}/instagram/video_posts/clips/' + r'{}.mp4'.format(pk),
                            'rb')
                        bot.delete_message(mess.chat.id, mess.message_id)
                        bot.send_video(message.chat.id, video_1, caption=caption)
                        video_1.close()
                        return
                    else:
                        response = requests.get(url=video_url)
                        video = open(f'users_content/{message.chat.id}/instagram/video_posts/clips/' + r'{}.mp4'.format(pk),
                                     "wb")
                        video.write(response.content)
                        video.close()
                        video_1 = open(f'users_content/{message.chat.id}/instagram/video_posts/clips/' + r'{}.mp4'.format(pk),
                                       'rb')
                        bot.delete_message(mess.chat.id, mess.message_id)
                        bot.send_video(message.chat.id, video_1, caption=caption)
                        video_1.close()
            if media_type == 1:  # скачивание постов с фоткой
                if os.path.exists(f'users_content/{message.chat.id}/instagram/photo_posts/' + r'{}.jpeg'.format(pk)):
                    photo_1 = open(f'users_content/{message.chat.id}/instagram/photo_posts/' + r'{}.jpeg'.format(pk),
                                   'rb')
                    bot.delete_message(mess.chat.id, mess.message_id)
                    bot.send_photo(message.chat.id, photo_1, caption=caption)
                    photo_1.close()
                    return
                else:
                    image_url = result["thumbnail_url"]
                    response = requests.get(url=image_url)
                    photo = open(f'users_content/{message.chat.id}/instagram/photo_posts/' + r'{}.jpeg'.format(pk), "wb")
                    photo.write(response.content)
                    photo.close()
                    photo_1 = open(f'users_content/{message.chat.id}/instagram/photo_posts/' + r'{}.jpeg'.format(pk), 'rb')
                    bot.delete_message(mess.chat.id, mess.message_id)
                    bot.send_photo(message.chat.id, photo_1, caption=caption)
                    photo_1.close()
            if media_type == 8:  # скачивание постов с нескольками фото
                if os.path.exists(f'users_content/{message.chat.id}/instagram/albums_posts/' + str(pk)):
                    media = create_album_media(f'users_content/{message.chat.id}/instagram/albums_posts/{pk}/')
                    bot.delete_message(mess.chat.id, mess.message_id)
                    bot.send_media_group(message.chat.id, media=media)
                    return
                else:
                    Path(f'users_content/{message.chat.id}/instagram/albums_posts/' + str(pk)).mkdir(parents=True, exist_ok=True)
                    resources = result["resources"]
                    for index, source in enumerate(resources):
                        pk_post = index
                        video_url = source["video_url"]
                        photo_url = source["thumbnail_url"]
                        media_type_i = source["media_type"]
                        if media_type_i == 2:
                            response = requests.get(url=video_url)
                            video = open(f'users_content/{message.chat.id}/instagram/albums_posts/{pk}/' + r'{}.mp4'.format(pk_post),
                                         "wb")
                            video.write(response.content)
                            video.close()
                        if media_type_i == 1:
                            response = requests.get(url=photo_url)
                            photo = open(f'users_content/{message.chat.id}/instagram/albums_posts/{pk}/' + r'{}.jpeg'.format(pk_post),
                                         "wb")
                            photo.write(response.content)
                            photo.close()
                    media = create_album_media(f'users_content/{message.chat.id}/instagram/albums_posts/{pk}/')
                    bot.delete_message(mess.chat.id, mess.message_id)
                    bot.send_media_group(message.chat.id, media = media)
            print("Скачал инста-пост: " + str(url))
        try:
            db_add_content(user_id=message.chat.id, link_content=url, media_pk=pk,  content_description=caption)
            old_value = get_from_bd(message.chat.id, "instagram_loaded")
            old_value = int(old_value) + 1
            set_to_bd(message.chat.id, "instagram_loaded", old_value)
        except sqlite3.IntegrityError:
            if get_from_bd(message.chat.id, 'worker'):
                bot.send_message(message.chat.id, text='Такой контент уже был загружен!')
    except Exception as e:
        print("Ошибка при скачивании Инстаграм контента: " + str(e))
        bot.send_message(message.chat.id, text="Произошла ошибка при скачивании! Попробуйте позже...")

hello = "👋Привет!\n🤖Я умею скачивать контент из соц сетей:\n✅Instagram\n✅TikTok(без водянного знака)\n✅YouTube Shorts\n\n🔗Ты можешь отправить мне ссылку с желаемым контентом, который ты хочешь скачать!"

def change_desc(message, old_message):
    active_menu = get_from_bd(message.chat.id, 'active_menu')
    active_content = get_active_content(message.chat.id)
    if ('albums_posts' in active_menu) or ('albums_posts' in active_content):
        messages = literal_eval(get_from_bd(message.chat.id, 'album_messages'))
        if len(messages) >= 1:
            for id in messages:
                bot.delete_message(chat_id=message.chat.id, message_id=id)
    bot.delete_message(chat_id=message.chat.id, message_id=old_message)
    content_id = str(os.path.splitext(os.path.basename(get_active_content(message.chat.id)))[0])
    cursor.execute(f"UPDATE contents SET content_description = '{message.text}' WHERE link_content = '{content_id}'")
    conn.commit()
    send_anket(message, active_menu)

def construct(content):
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

def send_anket(message, content_type):
    if (content_type == 'storys'):
        content_list = construct(content_type)
        if len(content_list) != 0:
            content = content_list[0]
            desc, caption = db_get_content(content)
            bot.delete_message(message.chat.id, message.message_id)
            set_active_content(message.chat.id, content)
            if content.suffix == ".mp4":
                video = open(content, 'rb')
                bot.send_video(message.chat.id, video, caption=caption+desc, parse_mode= 'Markdown', reply_markup=tinder)
                video.close()
            else:
                photo = open(content, 'rb')
                bot.send_photo(message.chat.id, photo, caption=caption+desc, parse_mode= 'Markdown', reply_markup=tinder)
                photo.close()
        else:
            set_active_content(message.chat.id, "NO")
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(chat_id=message.chat.id, text='Контент в данной категории отсутствует!', reply_markup=admin_back_mark)
    if (content_type == 'clips') or (content_type == 'igtv') or (content_type == 'other_posts'):
        content_list = construct(content_type)
        if len(content_list) != 0:
            content = content_list[0]
            desc, caption = db_get_content(content)
            bot.delete_message(message.chat.id, message.message_id)
            set_active_content(message.chat.id, content)
            if content.suffix == ".mp4":
                video = open(content, 'rb')
                msg = bot.send_video(message.chat.id, video, caption=caption + desc, parse_mode='Markdown',
                               reply_markup=tinder_with_story)
                video.close()
                bot.register_next_step_handler(msg, change_desc, msg.id)
            else:
                photo = open(content, 'rb')
                msg = bot.send_photo(message.chat.id, photo, caption=caption + desc, parse_mode='Markdown',
                               reply_markup=tinder_with_story)
                photo.close()
                bot.register_next_step_handler(msg, change_desc, msg.id)
        else:
            set_active_content(message.chat.id, "NO")
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(chat_id=message.chat.id, text='Контент в данной категории отсутствует!',
                             reply_markup=admin_back_mark)
    if content_type == 'albums_posts':
        albums_id = []
        albums_list = construct(content_type)
        if (len(albums_list) != 0):
            album = albums_list[0]
            desc, caption = db_get_content(album)
            media = create_album_media(album)
            bot.delete_message(message.chat.id, message.message_id)
            album_message = bot.send_media_group(message.chat.id, media=media)
            for message in album_message:
                albums_id.append(message.id)
            set_to_bd(message.chat.id, 'album_messages', albums_id)
            msg = bot.send_message(message.chat.id, text=caption+desc, parse_mode= 'Markdown', reply_markup=tinder)
            set_active_content(message.chat.id, album)
            bot.register_next_step_handler(msg, change_desc, msg.id)
        else:
            set_active_content(message.chat.id, "NO")
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(chat_id=message.chat.id, text='Контент в данной категории отсутствует!',
                             reply_markup=admin_back_mark)

    if content_type == 'all':
        albums_list, content_list = construct(content_type)
        if (len(content_list) != 0):
            content = content_list[0]
            desc, caption = db_get_content(content)
            bot.delete_message(message.chat.id, message.message_id)
            set_active_content(message.chat.id, content)
            if content.suffix == ".mp4":
                video = open(content, 'rb')
                msg = bot.send_video(message.chat.id, video, caption = caption+desc, parse_mode= 'Markdown', reply_markup=tinder)
                video.close()
                if "сторис" in caption:
                    pass
                else:
                    bot.register_next_step_handler(msg, change_desc, msg.id)
            else:
                photo = open(content, 'rb')
                msg = bot.send_photo(message.chat.id, photo, caption = caption+desc, parse_mode= 'Markdown', reply_markup=tinder)
                photo.close()
                if "сторис" in caption:
                    pass
                else:
                    bot.register_next_step_handler(msg, change_desc, msg.id)
            return
        if (len(albums_list) != 0):
            albums_id = []
            album = albums_list[0]
            desc, caption = db_get_content(album)
            media = create_album_media(album)
            bot.delete_message(message.chat.id, message.message_id)
            album_message = bot.send_media_group(message.chat.id, media=media)
            for message in album_message:
                albums_id.append(message.id)
            set_to_bd(message.chat.id, 'album_messages', albums_id)
            msg = bot.send_message(message.chat.id, text=caption+desc, parse_mode= 'Markdown', reply_markup=tinder)
            set_active_content(message.chat.id, album)
            bot.register_next_step_handler(msg, change_desc, msg.id)
            return
        else:
            set_active_content(message.chat.id, "NO")
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(chat_id=message.chat.id, text='Контент в данной категории отсутствует!',
                             reply_markup=admin_back_mark)

def move(rate):
    path = pathlib.WindowsPath(rate)
    no_need = str(list(path.parents)[-4])
    no_need = no_need + '\\'
    path = str(path)
    path = path.replace(no_need, '')
    path2 = os.path.dirname(path) + '\\'
    shutil.move(rate, path2)

def move_to_story(rate, story_path):
    path = pathlib.WindowsPath(rate)
    no_need = str(list(path.parents)[-4])
    no_need = no_need + '\\'
    path = str(path)
    new_path = os.path.join(story_path, os.path.basename(rate))
    shutil.move(rate, new_path)

def get_active_id(rate):
    path = pathlib.WindowsPath(rate)
    no_need = str(list(path.parents)[-3])
    active_id = no_need.replace("users_content\\", "")
    return active_id

def get_count_content():
    count_storys = len(construct('storys'))
    count_clips = len(construct('clips'))
    count_igtv = len(construct('igtv'))
    count_albums = len(construct('albums_posts'))
    count_other_posts = len(construct('other_posts'))
    total_count = count_storys+count_clips+count_igtv+count_albums+count_other_posts
    info = f"📁*Количество непроверенного контента:*\n📙_Сторис: {count_storys}\n📘Клипы: {count_clips}\n📗IGTV: {count_igtv}\n📕Обычные посты:_ {count_other_posts}\n📚Альбомные посты: {count_albums}\n*💾Всего:* {total_count}\n\nВыбери категорию:"
    return info

def download_ig_storys(message, username, story_id):
    Path(f'users_content/{message.chat.id}/instagram/storys/video').mkdir(parents=True, exist_ok=True)
    Path(f'users_content/{message.chat.id}/instagram/storys/photo').mkdir(parents=True, exist_ok=True)
    mess = bot.send_message(message.chat.id, text='Скачиваю...')
    try:
        a = "https://api.hikerapi.com/v1/user/stories/by/username?username={}&amount=0&access_key=API_KEY".format(
            quote(username))
        response = requests.get(url=a)
        result = json.loads(response.text)
        try:
            is_private = result[0]['user']['is_private']
            if is_private:
                return False
        except:
            return False
        if story_id.isdigit():
            if int(story_id) > len(result):
                return False
            else:#Скачиваем определенную сторис по юзернейму!
                story_id = int(story_id) - 1
                media_type = result[story_id]["media_type"]
                pk = result[story_id]["pk"]
                if media_type == 2:
                    url = result[story_id]['video_url']
                    if os.path.exists(f'users_content/{message.chat.id}/instagram/storys/video/' + r'{}.mp4'.format(pk)):
                        video_1 = open(f'users_content/{message.chat.id}/instagram/storys/video/' + r'{}.mp4'.format(pk),
                                       'rb')
                        bot.delete_message(mess.chat.id, mess.message_id)
                        bot.send_video(message.chat.id, video_1)
                        video_1.close()
                    else:
                        response = requests.get(url=url)
                        video = open(f'users_content/{message.chat.id}/instagram/storys/video/' + r'{}.mp4'.format(pk),
                                     "wb")
                        video.write(response.content)
                        video.close()
                        video_1 = open(f'users_content/{message.chat.id}/instagram/storys/video/' + r'{}.mp4'.format(pk),
                                       'rb')
                        bot.delete_message(mess.chat.id, mess.message_id)
                        bot.send_video(message.chat.id, video_1)
                        video_1.close()
                if media_type == 1:
                    url = result[story_id]['thumbnail_url']
                    if os.path.exists(f'users_content/{message.chat.id}/instagram/storys/photo/' + r'{}.jpeg'.format(pk)):
                        photo_1 = open(f'users_content/{message.chat.id}/instagram/storys/photo/' + r'{}.jpeg'.format(pk),
                                       'rb')
                        bot.delete_message(mess.chat.id, mess.message_id)
                        bot.send_photo(message.chat.id, photo_1)
                        photo_1.close()
                    else:
                        response = requests.get(url=url)
                        photo = open(f'users_content/{message.chat.id}/instagram/storys/photo/' + r'{}.jpeg'.format(pk),
                                     "wb")
                        photo.write(response.content)
                        photo.close()
                        photo_1 = open(f'users_content/{message.chat.id}/instagram/storys/photo/' + r'{}.jpeg'.format(pk),
                                       'rb')
                        bot.delete_message(mess.chat.id, mess.message_id)
                        bot.send_photo(message.chat.id, photo_1)
                        photo_1.close()
                try:
                    db_add_content(user_id=message.chat.id, link_content=str(pk), media_pk=pk, content_description=name_pablik)
                    old_value = get_from_bd(message.chat.id, "instagram_loaded")
                    old_value = int(old_value) + 1
                    set_to_bd(message.chat.id, "instagram_loaded", old_value)
                except sqlite3.IntegrityError:
                    if get_from_bd(message.chat.id, 'worker'):
                        bot.send_message(message.chat.id, text='Такой контент уже был загружен!')
        else:#Скачиваем все сторисы по юзернейму
            bot.delete_message(mess.chat.id, mess.message_id)
            for res in result:
                media_type = res["media_type"]
                pk = res["pk"]
                if media_type == 2:
                    url = res['video_url']
                    if os.path.exists(f'users_content/{message.chat.id}/instagram/storys/video/' + r'{}.mp4'.format(pk)):
                        video_1 = open(f'users_content/{message.chat.id}/instagram/storys/video/' + r'{}.mp4'.format(pk),
                                       'rb')
                        bot.send_video(message.chat.id, video_1)
                        video_1.close()
                    else:
                        response = requests.get(url=url)
                        video = open(f'users_content/{message.chat.id}/instagram/storys/video/' + r'{}.mp4'.format(pk),
                                     "wb")
                        video.write(response.content)
                        video.close()
                        video_1 = open(f'users_content/{message.chat.id}/instagram/storys/video/' + r'{}.mp4'.format(pk),
                                       'rb')
                        bot.send_video(message.chat.id, video_1)
                        video_1.close()
                        try:
                            db_add_content(user_id=message.chat.id, link_content=str(pk), media_pk=pk, content_description=name_pablik)
                            old_value = get_from_bd(message.chat.id, "instagram_loaded")
                            old_value = int(old_value) + 1
                            set_to_bd(message.chat.id, "instagram_loaded", old_value)
                        except sqlite3.IntegrityError:
                            if get_from_bd(message.chat.id, 'worker'):
                                bot.send_message(message.chat.id, text='Такой контент уже был загружен!')
                if media_type == 1:
                    url = res['thumbnail_url']
                    if os.path.exists(f'users_content/{message.chat.id}/instagram/storys/photo/' + r'{}.jpeg'.format(pk)):
                        photo_1 = open(f'users_content/{message.chat.id}/instagram/storys/photo/' + r'{}.jpeg'.format(pk),
                                       'rb')
                        bot.send_photo(message.chat.id, photo_1)
                        photo_1.close()
                    else:
                        response = requests.get(url=url)
                        photo = open(f'users_content/{message.chat.id}/instagram/storys/photo/' + r'{}.jpeg'.format(pk),
                                     "wb")
                        photo.write(response.content)
                        photo.close()
                        photo_1 = open(f'users_content/{message.chat.id}/instagram/storys/photo/' + r'{}.jpeg'.format(pk),
                                       'rb')
                        bot.send_photo(message.chat.id, photo_1)
                        photo_1.close()
                        try:
                            db_add_content(user_id=message.chat.id, link_content=str(pk), media_pk=pk, content_description=name_pablik)
                            old_value = get_from_bd(message.chat.id, "instagram_loaded")
                            old_value = int(old_value) + 1
                            set_to_bd(message.chat.id, "instagram_loaded", old_value)
                        except sqlite3.IntegrityError:
                            if get_from_bd(message.chat.id, 'worker'):
                                bot.send_message(message.chat.id, text='Такой контент уже был загружен!')
    except Exception as e:
        print("Ошибка при скачивании инста сторис по запросу: " + str(e))
        bot.send_message(message.chat.id,
                         text="Произошла ошибка при скачивании! Попробуйте позже...")

@bot.message_handler(commands=['start'])
def start(message):
    if get_all_id(message.from_user.id):
        bot.send_message(message.chat.id, text=hello)
    else:
        db_add_user(user_id=message.from_user.id, user_name=message.from_user.first_name,
                    user_surname=message.from_user.last_name,
                    username=message.from_user.username)
        bot.send_message(message.chat.id, text=hello)

@bot.message_handler(content_types=['text'])
def link(message):
    if 'tiktok.com' in message.text:
        tiktok_download(message.text, message)
    elif 'youtube.com' in message.text:
        youtube_download(message.text, message)
    elif 'instagram.com' in message.text:
        instagram_download(message.text, message)
    elif (message.text).startswith('@'):
        info = (message.text).split('-')
        if len(info) == 2:
            result = download_ig_storys(message, info[0].replace("@", ""), info[1])
            if result == False:
                bot.send_message(message.chat.id, text = "Произошла ощибка, возможные  причины:\nВы неверно указали номер истории, её не существует!\nАккаунт закрыт!\nАккаунт не имеет активных историй!")
        else:
            bot.send_message(message.chat.id, text="❌Неверно указан запрос!\nВведите \\help и прочитайте инструкцию!")
    elif ('sliska' in (message.text).lower()) and (message.chat.id == tg1 or tg2):
        bot.send_message(message.chat.id, text="Админ-панель:", reply_markup=admin_menu)
    else:
        bot.send_message(message.chat.id, text="❌Неверная ссылка!")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message:
        if call.data == "back_admin":
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
            if "album" in str(get_active_content(call.message.chat.id)):
                messages = literal_eval(get_from_bd(call.message.chat.id, 'album_messages'))
                if len(messages) > 1:
                    for message in messages:
                        bot.delete_message(chat_id=call.message.chat.id, message_id=message)
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
            bot.send_message(chat_id=call.message.chat.id, text="Админ-панель:", reply_markup=admin_menu)
            set_active_content(call.message.chat.id, "NO")
            set_to_bd(call.message.chat.id, 'active_menu', 'menu')
        if call.data == "content_rate":
            count = get_count_content()
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=count, parse_mode='Markdown', reply_markup=rate_content)
        if call.data == "story_view":
            send_anket(call.message, 'storys')
            set_to_bd(call.message.chat.id, 'active_menu', 'storys')
        if call.data == "reels_view":
            send_anket(call.message, 'clips')
            set_to_bd(call.message.chat.id, 'active_menu', 'clips')
        if call.data == 'igtv_view':
            send_anket(call.message, 'igtv')
            set_to_bd(call.message.chat.id, 'active_menu', 'igtv')
        if call.data == 'other_posts_view':
            send_anket(call.message, 'other_posts')
            set_to_bd(call.message.chat.id, 'active_menu', 'other_posts')
        if call.data == 'albums_posts_view':
            send_anket(call.message, 'albums_posts')
            set_to_bd(call.message.chat.id, 'active_menu', 'albums_posts')
        if call.data == 'all_view':
            send_anket(call.message, 'all')
            set_to_bd(call.message.chat.id, 'active_menu', 'all')
        if call.data == "yes":
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
            bot.answer_callback_query(callback_query_id=call.id, text='Принято')
            rate = str(get_active_content(call.message.chat.id))
            active_menu = get_from_bd(call.message.chat.id, 'active_menu')
            active_id = get_active_id(rate)
            id_media = str(os.path.splitext(os.path.basename(rate))[0])
            cursor.execute(f"SELECT content_description FROM contents WHERE link_content = '{id_media}'")
            desc_db = cursor.fetchone()
            if desc_db != None:
                desc_db = desc_db[0]
            else:
                desc_db = name_pablik
            if "album" in rate:
                messages = literal_eval(get_from_bd(call.message.chat.id, 'album_messages'))
                if len(messages) >= 1:
                    for message in messages:
                        bot.delete_message(chat_id=call.message.chat.id, message_id=message)
                move(rate)
                old_value = get_from_bd(active_id, "approved_content")
                old_value = int(old_value) + 1
                set_to_bd(active_id, "approved_content", old_value)
                send_anket(call.message, active_menu)
            else:
                move(rate)
                old_value = get_from_bd(active_id, "approved_content")
                old_value = int(old_value) + 1
                set_to_bd(active_id, "approved_content", old_value)
                send_anket(call.message, active_menu)
        if call.data == 'no':
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
            bot.answer_callback_query(callback_query_id=call.id, text='Удалено!')
            rate = str(get_active_content(call.message.chat.id))
            active_menu = get_from_bd(call.message.chat.id, 'active_menu')
            if "album" in rate:
                messages = literal_eval(get_from_bd(call.message.chat.id, 'album_messages'))
                if len(messages) >= 1:
                    for message in messages:
                        bot.delete_message(chat_id=call.message.chat.id, message_id=message)
                shutil.rmtree(rate)
            else:
                os.remove(rate)
            send_anket(call.message, active_menu)
        if call.data == 'to_story':
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
            bot.answer_callback_query(callback_query_id=call.id, text='Принято')
            rate = str(get_active_content(call.message.chat.id))
            active_menu = get_from_bd(call.message.chat.id, 'active_menu')
            active_id = get_active_id(rate)
            id_media = str(os.path.splitext(os.path.basename(rate))[0])
            cursor.execute(f"SELECT content_description FROM contents WHERE link_content = '{id_media}'")
            desc_db = cursor.fetchone()
            if desc_db != None:
                desc_db = desc_db[0]
            else:
                desc_db = name_pablik

            # Проверяем расширение файла
            file_extension = os.path.splitext(rate)[1].lower()

            # Если это видео
            if file_extension in ['.mp4', '.mov', '.avi']:  # расширения видео
                story_path = "storys/video/"
            # Если это фото
            elif file_extension in ['.jpg', '.jpeg', '.png']:  # расширения фото
                story_path = "storys/photo/"
            else:
                bot.answer_callback_query(callback_query_id=call.id, text='Неподдерживаемый формат файла')
                return

            # Перемещаем в нужную папку
            move_to_story(rate, story_path)

            old_value = get_from_bd(active_id, "approved_content")
            old_value = int(old_value) + 1
            set_to_bd(active_id, "approved_content", old_value)
            send_anket(call.message, active_menu)
        if call.data == "stat":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Обновляю...",
                                  reply_markup=admin_menu)
            msg = count_files()
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg, reply_markup=admin_menu)

        if call.data == "autopost":
            if get_from_bd_settings("autopost_status"):
                status_autopost = "Включен"
                menu_autopost = get_menu_autopost(True)
            else:
                status_autopost = "Выключен"
                menu_autopost = get_menu_autopost(False)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text="Статус автопостинга: " + status_autopost + "\n\n" + str(content_count()),
                                  reply_markup=menu_autopost)
        if call.data == "autopost_on_off":
            if get_from_bd_settings("autopost_status"):
                status_autopost = "Выключен"
                set_to_bd_settings("autopost_status", False)
                menu_autopost = get_menu_autopost(False)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                      text="Статус автопостинга: " + status_autopost + "\n\n" + str(content_count()),
                                      reply_markup=menu_autopost)
                loop.stop()
            else:
                status_autopost = "Включен"
                set_to_bd_settings("autopost_status", True)
                menu_autopost = get_menu_autopost(True)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                      text="Статус автопостинга: " + status_autopost + "\n\n" + str(content_count()),
                                      reply_markup=menu_autopost)
                morning, day, evening = get_time()
                loop.start(morning, day, evening)

        if call.data == "settings_autopost":
            if get_from_bd_settings("autopost_status"):
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                      text="Чтобы зайти в настройки нужно выключить автопостинг",
                                      reply_markup=back_menu)
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                      text="Выберите нужную категорию настроек:", reply_markup=menu_settings_autopost)

        if call.data == "timestamp_settings":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Выберите фазу: ",
                                  reply_markup=menu_timestamp_autopost_settings)

        if call.data == "timestamp_morning":
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text="Утро:\nНапишите временные рамки:\nПример: 00:05:00-23:55:59\nСброс значений загруженного контента в 00:00:00 - это время не трогать!",
                                        reply_markup=back_menu_settings)
            bot.register_next_step_handler(msg, set_morning_timestamp)

        if call.data == "timestamp_day":
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text="День:\nНапишите временные рамки:\nПример: 00:05:00-23:55:59\nСброс значений загруженного контента в 00:00:00 - это время не трогать!",
                                        reply_markup=back_menu_settings)
            bot.register_next_step_handler(msg, set_day_timestamp)

        if call.data == "timestamp_evening":
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text="Вечер:\nНапишите временные рамки:\nПример: 00:05:00-23:55:59\nСброс значений загруженного контента в 00:00:00 - это время не трогать!",
                                        reply_markup=back_menu_settings)
            bot.register_next_step_handler(msg, set_evening_timestamp)

        if call.data == "content_settings":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Выберите фазу: ",
                                  reply_markup=menu_content_autopost_settings)

        if call.data == "content_morning":
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text="Утро:\nНапишите в строгом порядке ключи контента:\nРасшифровка ключей: \nСВ - Сторис видео\nСФ - Сторис фото\nВП - Видео пост\nФП - Фото пост\nАП - Альбомный пост\nИТ - IGTV\nК - Клип\n\n Пример строки которую надо написать: \nСВ-СВ-СФ-ВП-ФП-АП-ИТ-К-К",
                                        reply_markup=back_menu_settings)
            bot.register_next_step_handler(msg, set_morning_content)

        if call.data == "content_day":
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text="День:\nНапишите в строгом порядке ключи контента:\nРасшифровка ключей: \nСВ - Сторис видео\nСФ - Сторис фото\nВП - Видео пост\nФП - Фото пост\nАП - Альбомный пост\nИТ - IGTV\nК - Клип\n\n Пример строки которую надо написать: \nСВ-СВ-СФ-ВП-ФП-АП-ИТ-К-К",
                                        reply_markup=back_menu_settings)
            bot.register_next_step_handler(msg, set_day_content)

        if call.data == "content_evening":
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text="Вечер:\nНапишите в строгом порядке ключи контента:\nРасшифровка ключей: \nСВ - Сторис видео\nСФ - Сторис фото\nВП - Видео пост\nФП - Фото пост\nАП - Альбомный пост\nИТ - IGTV\nК - Клип\n\n Пример строки которую надо написать: \nСВ-СВ-СФ-ВП-ФП-АП-ИТ-К-К",
                                        reply_markup=back_menu_settings)
            bot.register_next_step_handler(msg, set_evening_content)

        if call.data == "back_menu_settings":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text="Выберите нужную категорию настроек:", reply_markup=menu_settings_autopost)

        if call.data == "menu":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text='Нажми "Обновить" чтобы обновить статистику', reply_markup=admin_menu)

def time_reset():
    set_to_bd_settings("uploaded_video_story", 0)
    set_to_bd_settings("uploaded_photo_story", 0)
    set_to_bd_settings("uploaded_video_posts", 0)
    set_to_bd_settings("uploaded_photo_posts", 0)
    set_to_bd_settings("uploaded_album_posts", 0)
    set_to_bd_settings("uploaded_igtv", 0)
    set_to_bd_settings("uploaded_clips", 0)
    set_to_bd_settings("current_position_content", "0-0")
    print("Произведен сброс значений загруженного контента")

def mainloop():
    while True:
        try:
            bot.infinity_polling()
        except:
            time.sleep(5)

def resettime():
    schedule.every().day.at("20:00").do(time_reset)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    set_to_bd_settings("autopost_status", False)
    t1 = threading.Thread(target=mainloop)
    t2 = threading.Thread(target=resettime)
    t1.start()
    t2.start()