"""
Загрузчики контента
==================

Модуль для скачивания контента из TikTok, Instagram и YouTube.
"""

import os
import json
import requests
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import quote
from pytubefix import YouTube
from moviepy.editor import VideoFileClip
import shutil

from .config import Config
from .database import get_database
from .utils import ensure_directory


class ContentDownloader:
    """Базовый класс для загрузчиков контента"""
    
    def __init__(self):
        self.db = get_database()
        self.default_caption = Config.DEFAULT_CAPTION
    
    def _determine_video_category(self, duration: float) -> str:
        """
        Определяет категорию видео по длительности
        
        Args:
            duration: Длительность видео в секундах
        
        Returns:
            str: Категория ('story', 'clip', 'igtv')
        """
        if duration < 15:
            return 'story'
        elif duration < 60:
            return 'clip'
        else:
            return 'igtv'
    
    def _save_content_to_db(self, user_id: int, link: str, media_pk: str, 
                           description: str) -> bool:
        """
        Сохраняет информацию о контенте в БД
        
        Returns:
            bool: True если сохранено успешно, False если дубликат
        """
        return self.db.add_content(user_id, link, media_pk, description)


class TikTokDownloader(ContentDownloader):
    """Загрузчик контента из TikTok"""
    
    def __init__(self):
        super().__init__()
        self.api_host = Config.TIKTOK_API_HOST
    
    def download(self, url: str, user_id: int) -> Tuple[bool, str, Optional[str]]:
        """
        Скачивает видео из TikTok
        
        Args:
            url: URL TikTok видео
            user_id: ID пользователя Telegram
        
        Returns:
            Tuple[bool, str, Optional[str]]: (успех, сообщение, путь к файлу)
        """
        try:
            # Создаём директории
            base_path = f'{Config.CONTENT_BASE_DIR}/{user_id}/tiktok'
            ensure_directory(f'{base_path}/storys/video')
            ensure_directory(f'{base_path}/video_posts/clips')
            ensure_directory(f'{base_path}/video_posts/igtv')
            
            # Запрос к API TikTok
            api_url = f'http://{self.api_host}/api/hybrid/video_data?url={url}'
            headers = {
                'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36'
            }
            
            response = requests.get(api_url, headers=headers, timeout=30)
            result = response.json()
            
            # Извлекаем данные
            video_id = result["data"]["aweme_id"]
            video_url = result["data"]["video"]["play_addr"]["url_list"][0]
            author = result["data"]["author"]["nickname"]
            desc = result["data"]["desc"]
            
            # Формируем описание (логика из OLD версии)
            if desc == "":
                desc = self.default_caption + "\n\n" + "Автор(ТТ): " + author
            else:
                desc = desc + "\n\n" + "Автор(ТТ): " + author
            
            # Проверяем существование файла
            for category in ['storys/video', 'video_posts/clips', 'video_posts/igtv']:
                existing_file = f'{base_path}/{category}/{video_id}.mp4'
                if os.path.exists(existing_file):
                    return True, "Видео уже было загружено ранее", existing_file
            
            # Скачиваем видео
            video_response = requests.get(video_url, stream=True, timeout=60)
            temp_file = f'{video_id}.mp4'
            
            with open(temp_file, 'wb') as video_file:
                video_file.write(video_response.content)
            
            # Определяем длительность и перемещаем в нужную папку
            with VideoFileClip(temp_file) as clip:
                duration = clip.duration
            
            category = self._determine_video_category(duration)
            
            if category == 'story':
                final_path = f'{base_path}/storys/video/{video_id}.mp4'
            elif category == 'clip':
                final_path = f'{base_path}/video_posts/clips/{video_id}.mp4'
            else:  # igtv
                final_path = f'{base_path}/video_posts/igtv/{video_id}.mp4'
            
            shutil.move(temp_file, final_path)
            
            # Сохраняем в БД
            is_new = self._save_content_to_db(user_id, url, video_id, desc)
            
            if is_new:
                # Обновляем статистику пользователя
                old_value = self.db.get_user_field(user_id, "tiktok_loaded") or 0
                self.db.set_user_field(user_id, "tiktok_loaded", int(old_value) + 1)
            
            return True, f"✅ TikTok видео успешно загружено!\n\n{desc}", final_path
            
        except Exception as e:
            return False, f"❌ Ошибка при загрузке TikTok видео: {str(e)}", None


class YouTubeDownloader(ContentDownloader):
    """Загрузчик контента из YouTube"""
    
    def download(self, url: str, user_id: int) -> Tuple[bool, str, Optional[str]]:
        """
        Скачивает видео из YouTube
        
        Args:
            url: URL YouTube видео
            user_id: ID пользователя Telegram
        
        Returns:
            Tuple[bool, str, Optional[str]]: (успех, сообщение, путь к файлу)
        """
        try:
            # Создаём директории
            base_path = f'{Config.CONTENT_BASE_DIR}/{user_id}/yt'
            ensure_directory(f'{base_path}/storys/video')
            ensure_directory(f'{base_path}/video_posts/clips')
            ensure_directory(f'{base_path}/video_posts/igtv')
            
            # Получаем информацию о видео
            yt = YouTube(url)
            video_id = yt.video_id
            title = yt.title or ""
            author = yt.author
            
            # Формируем описание (логика из OLD версии)
            if title == "":
                description = self.default_caption + "\n\n" + "Автор(YT): " + author
            else:
                description = title + "\n\n" + "Автор(YT): " + author
            
            # Проверяем существование файла
            for category in ['storys/video', 'video_posts/clips', 'video_posts/igtv']:
                existing_file = f'{base_path}/{category}/{video_id}.mp4'
                if os.path.exists(existing_file):
                    return True, "Видео уже было загружено ранее", existing_file
            
            # Скачиваем видео
            stream = yt.streams.get_highest_resolution()
            temp_file = f'{video_id}.mp4'
            stream.download("", filename=temp_file)
            
            # Получаем длительность
            with VideoFileClip(temp_file) as clip:
                duration = clip.duration
            
            # Проверяем максимальную длительность (4 минуты)
            if duration > 240:
                os.remove(temp_file)
                return False, "❌ Видео слишком длинное (макс. 4 минуты)", None
            
            # Определяем категорию и перемещаем
            category = self._determine_video_category(duration)
            
            if category == 'story':
                final_path = f'{base_path}/storys/video/{video_id}.mp4'
            elif category == 'clip':
                final_path = f'{base_path}/video_posts/clips/{video_id}.mp4'
            else:  # igtv
                final_path = f'{base_path}/video_posts/igtv/{video_id}.mp4'
            
            shutil.move(temp_file, final_path)
            
            # Сохраняем в БД
            is_new = self._save_content_to_db(user_id, video_id, video_id, description)
            
            if is_new:
                old_value = self.db.get_user_field(user_id, "yt_loaded") or 0
                self.db.set_user_field(user_id, "yt_loaded", int(old_value) + 1)
            
            return True, f"✅ YouTube видео успешно загружено!\n\n{description}", final_path
            
        except Exception as e:
            return False, f"❌ Ошибка при загрузке YouTube видео: {str(e)}", None


class InstagramDownloader(ContentDownloader):
    """Загрузчик контента из Instagram"""
    
    def __init__(self):
        super().__init__()
        self.api_key = Config.HIKER_API_KEY
    
    def download(self, url: str, user_id: int) -> Tuple[bool, str, Optional[str]]:
        """
        Скачивает контент из Instagram
        
        Args:
            url: URL Instagram поста/stories
            user_id: ID пользователя Telegram
        
        Returns:
            Tuple[bool, str, Optional[str]]: (успех, сообщение, путь к файлу)
        """
        try:
            # Создаём директории
            base_path = f'{Config.CONTENT_BASE_DIR}/{user_id}/instagram'
            ensure_directory(f'{base_path}/storys/video')
            ensure_directory(f'{base_path}/storys/photo')
            ensure_directory(f'{base_path}/video_posts/igtv')
            ensure_directory(f'{base_path}/video_posts/clips')
            ensure_directory(f'{base_path}/photo_posts')
            ensure_directory(f'{base_path}/albums_posts')
            
            # Определяем тип контента (stories или post)
            is_story = "stories" in url
            
            if is_story:
                return self._download_story(url, user_id, base_path)
            else:
                return self._download_post(url, user_id, base_path)
                
        except Exception as e:
            return False, f"❌ Ошибка при загрузке Instagram контента: {str(e)}", None
    
    def _download_story(self, url: str, user_id: int, base_path: str) -> Tuple[bool, str, Optional[str]]:
        """Скачивает Instagram story"""
        api_url = f"https://api.hikerapi.com/v1/story/by/url?url={quote(url)}&access_key={self.api_key}"
        response = requests.get(api_url, timeout=30)
        result = response.json()
        
        media_type = result["media_type"]
        pk = result["pk"]
        
        # Видео story
        if media_type == 2:
            file_path = f'{base_path}/storys/video/{pk}.mp4'
            
            if os.path.exists(file_path):
                return True, "История уже была загружена", file_path
            
            download_url = f"https://api.hikerapi.com/v1/story/download?id={result['id']}&access_key={self.api_key}"
            video_response = requests.get(download_url, timeout=60)
            
            with open(file_path, 'wb') as f:
                f.write(video_response.content)
        
        # Фото story
        else:  # media_type == 1
            file_path = f'{base_path}/storys/photo/{pk}.jpeg'
            
            if os.path.exists(file_path):
                return True, "История уже была загружена", file_path
            
            download_url = f"https://api.hikerapi.com/v1/story/download?id={result['id']}&access_key={self.api_key}"
            photo_response = requests.get(download_url, timeout=60)
            
            with open(file_path, 'wb') as f:
                f.write(photo_response.content)
        
        # Сохраняем в БД
        self._save_content_to_db(user_id, url, str(pk), self.default_caption)
        
        old_value = self.db.get_user_field(user_id, "instagram_loaded") or 0
        self.db.set_user_field(user_id, "instagram_loaded", int(old_value) + 1)
        
        return True, f"✅ Instagram story успешно загружена!", file_path
    
    def _download_post(self, url: str, user_id: int, base_path: str) -> Tuple[bool, str, Optional[str]]:
        """Скачивает Instagram post"""
        api_url = f"https://api.hikerapi.com/v1/media/by/url?url={quote(url)}&access_key={self.api_key}"
        response = requests.get(api_url, timeout=30)
        result = response.json()
        
        media_type = result["media_type"]
        product_type = result.get("product_type", "feed")
        pk = result["pk"]
        caption = result.get("caption_text", "") or self.default_caption
        author = result['user']['username']
        if not caption:
            caption = f"{self.default_caption}\n\nАвтор(IG): {author}"
        else:
            caption = f"{caption}\n\nАвтор(IG): {author}"
        
        # Видео пост
        if media_type == 2:
            video_url = result["video_url"]
            
            if product_type == "clips":
                file_path = f'{base_path}/video_posts/clips/{pk}.mp4'
            elif product_type == "igtv":
                file_path = f'{base_path}/video_posts/igtv/{pk}.mp4'
            else:
                file_path = f'{base_path}/video_posts/{pk}.mp4'
            
            if os.path.exists(file_path):
                return True, "Пост уже был загружен", file_path
            
            video_response = requests.get(video_url, timeout=60)
            with open(file_path, 'wb') as f:
                f.write(video_response.content)
        
        # Фото пост
        elif media_type == 1:
            file_path = f'{base_path}/photo_posts/{pk}.jpeg'
            
            if os.path.exists(file_path):
                return True, "Пост уже был загружен", file_path
            
            image_url = result["thumbnail_url"]
            photo_response = requests.get(image_url, timeout=60)
            
            with open(file_path, 'wb') as f:
                f.write(photo_response.content)
        
        # Альбом
        elif media_type == 8:
            album_dir = f'{base_path}/albums_posts/{pk}'
            
            if os.path.exists(album_dir):
                return True, "Альбом уже был загружен", album_dir
            
            ensure_directory(album_dir)
            resources = result["resources"]
            
            for index, source in enumerate(resources):
                media_type_i = source["media_type"]
                
                if media_type_i == 2:  # Видео
                    video_url = source["video_url"]
                    file_path = f'{album_dir}/{index}.mp4'
                    video_response = requests.get(video_url, timeout=60)
                    with open(file_path, 'wb') as f:
                        f.write(video_response.content)
                
                elif media_type_i == 1:  # Фото
                    photo_url = source["thumbnail_url"]
                    file_path = f'{album_dir}/{index}.jpeg'
                    photo_response = requests.get(photo_url, timeout=60)
                    with open(file_path, 'wb') as f:
                        f.write(photo_response.content)
            
            file_path = album_dir
        
        # Сохраняем в БД
        is_new = self._save_content_to_db(user_id, url, str(pk), caption)
        
        if is_new:
            old_value = self.db.get_user_field(user_id, "instagram_loaded") or 0
            self.db.set_user_field(user_id, "instagram_loaded", int(old_value) + 1)
        
        return True, f"✅ Instagram пост успешно загружен!\n\n{caption[:100]}...", file_path


# Фабрика загрузчиков
def get_downloader(url: str) -> Optional[ContentDownloader]:
    """
    Возвращает подходящий загрузчик для URL
    
    Args:
        url: URL контента
    
    Returns:
        ContentDownloader или None если платформа не поддерживается
    """
    if 'tiktok.com' in url:
        return TikTokDownloader()
    elif 'youtube.com' in url or 'youtu.be' in url:
        return YouTubeDownloader()
    elif 'instagram.com' in url:
        return InstagramDownloader()
    else:
        return None


if __name__ == "__main__":
    print("✅ Модуль downloaders.py загружен успешно!")


