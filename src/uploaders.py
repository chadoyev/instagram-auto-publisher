"""
Публикаторы контента в Instagram
================================

Модуль для загрузки контента в Instagram: stories, posts, reels, IGTV, альбомы.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Optional, List
from multiprocessing import Process
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip
from PIL import Image
from instagrapi import Client

from .config import Config
from .database import get_database
from .utils import (
    get_oldest_file, 
    remove_file_safely, 
    remove_files_by_pattern,
    extract_media_pk_from_filename
)


class InstagramUploader:
    """Класс для публикации контента в Instagram"""
    
    def __init__(self, client: Client):
        """
        Инициализация публикатора
        
        Args:
            client: Аутентифицированный клиент instagrapi
        """
        self.client = client
        self.db = get_database()
        self.watermark_path = Config.WATERMARK_LOGO_PATH
        self.default_caption = Config.DEFAULT_CAPTION
    
    def _add_watermark(self, video_path: str) -> tuple[str, str]:
        """
        Добавляет водяной знак на видео
        
        Args:
            video_path: Путь к видео файлу
        
        Returns:
            tuple: (путь к видео с водяным знаком, путь к оригиналу)
        """
        directory = os.path.dirname(video_path)
        filename = os.path.basename(video_path)
        
        # Создаём временную копию
        copy_path = os.path.join(directory, f"copy_{filename}")
        shutil.copyfile(video_path, copy_path)
        time.sleep(0.5)
        
        # Путь для файла с водяным знаком
        watermarked_path = os.path.join(directory, f"with_wm_{filename}")
        
        try:
            # Загружаем видео и аудио
            video = VideoFileClip(copy_path)
            
            # Проверяем наличие аудио
            if video.audio:
                audio = video.audio
            else:
                audio = None
            
            # Загружаем логотип (если существует)
            if os.path.exists(self.watermark_path):
                logo = (ImageClip(self.watermark_path)
                       .set_duration(video.duration)
                       .resize(height=150)
                       .margin(opacity=0.1)
                       .set_position((0.75, 0.8), relative=True))
                
                # Накладываем водяной знак
                final = CompositeVideoClip([video, logo])
            else:
                # Если логотипа нет, используем оригинальное видео
                final = video
            
            # Добавляем аудио обратно
            if audio:
                final = final.set_audio(audio)
            
            # Сохраняем
            final.write_videofile(watermarked_path, codec='libx264', audio_codec='aac')
            
            # Закрываем клипы
            video.close()
            if audio:
                audio.close()
            
            # Удаляем временную копию
            os.remove(copy_path)
            
            return watermarked_path, video_path
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении водяного знака: {e}")
            # В случае ошибки возвращаем оригинал
            if os.path.exists(copy_path):
                os.remove(copy_path)
            return video_path, video_path
    
    def _get_media_description(self, filename: str) -> str:
        """
        Получает описание медиа из базы данных
        
        Args:
            filename: Имя файла
        
        Returns:
            str: Описание или пробел если не найдено
        """
        media_pk = extract_media_pk_from_filename(filename)
        
        # Пробуем найти в новой таблице contents
        description = self.db.get_content_description(media_pk)
        
        # Если не найдено, пробуем старую таблицу
        if not description:
            description = self.db.get_media_description(media_pk)
        
        return description or self.default_caption
    
    def _cleanup_files(self, *file_paths: str, max_attempts: int = 10) -> None:
        """
        Очищает временные файлы
        
        Args:
            file_paths: Пути к файлам для удаления
            max_attempts: Максимальное количество попыток
        """
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                remove_file_safely(file_path, max_attempts)
    
    # ========================================
    # Stories
    # ========================================
    
    def upload_story_video(self) -> bool:
        """Загружает видео story"""
        try:
            directory = Config.STORIES_VIDEO_DIR
            filename = get_oldest_file(directory)
            
            if not filename:
                print("⚠️ Нет видео для stories")
                return False
            
            file_path = os.path.join(directory, filename)
            
            # Добавляем водяной знак
            watermarked_path, original_path = self._add_watermark(file_path)
            
            # Загружаем в Instagram (в отдельном процессе для стабильности)
            upload_process = Process(
                target=self.client.video_upload_to_story,
                args=(watermarked_path,)
            )
            upload_process.start()
            upload_process.join()
            
            print(f"✅ Загружена видео история: {filename}")
            
            # Очищаем файлы
            self._cleanup_files(watermarked_path, original_path)
            remove_files_by_pattern(directory, f"with_wm_{filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке видео story: {e}")
            return False
    
    def upload_story_photo(self) -> bool:
        """Загружает фото story"""
        try:
            directory = Config.STORIES_PHOTO_DIR
            filename = get_oldest_file(directory)
            
            if not filename:
                print("⚠️ Нет фото для stories")
                return False
            
            file_path = os.path.join(directory, filename)
            
            # Загружаем в Instagram
            self.client.photo_upload_to_story(file_path)
            
            print(f"✅ Загружена фото история: {filename}")
            
            # Удаляем файл
            self._cleanup_files(file_path)
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке фото story: {e}")
            return False
    
    # ========================================
    # Posts
    # ========================================
    
    def upload_photo_post(self) -> bool:
        """Загружает фото пост"""
        try:
            directory = Config.POSTS_PHOTO_DIR
            filename = get_oldest_file(directory)
            
            if not filename:
                print("⚠️ Нет фото постов")
                return False
            
            file_path = os.path.join(directory, filename)
            
            # Получаем описание
            caption = self._get_media_description(filename)
            
            # Конвертируем WEBP в JPEG если нужно
            if filename.endswith('.webp'):
                with Image.open(file_path) as img:
                    rgb_img = img.convert('RGB')
                    new_path = file_path.replace('.webp', '.jpg')
                    rgb_img.save(new_path, 'JPEG')
                
                os.remove(file_path)
                file_path = new_path
                filename = os.path.basename(new_path)
            
            # Загружаем
            self.client.photo_upload(file_path, caption)
            
            print(f"✅ Загружен фото пост: {filename}")
            
            # Удаляем файл
            self._cleanup_files(file_path)
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке фото поста: {e}")
            return False
    
    def upload_video_post(self) -> bool:
        """Загружает видео пост"""
        try:
            directory = Config.POSTS_VIDEO_DIR
            filename = get_oldest_file(directory)
            
            if not filename or not filename.endswith('.mp4'):
                print("⚠️ Нет видео постов")
                return False
            
            file_path = os.path.join(directory, filename)
            
            # Получаем описание
            caption = self._get_media_description(filename)
            
            # Добавляем водяной знак
            watermarked_path, original_path = self._add_watermark(file_path)
            
            # Загружаем
            upload_process = Process(
                target=self.client.video_upload,
                args=(watermarked_path, caption)
            )
            upload_process.start()
            upload_process.join()
            
            print(f"✅ Загружен видео пост: {filename}")
            
            # Очищаем
            self._cleanup_files(watermarked_path, original_path)
            remove_files_by_pattern(directory, f"with_wm_{filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке видео поста: {e}")
            return False
    
    # ========================================
    # Albums
    # ========================================
    
    def upload_album_post(self) -> bool:
        """Загружает альбомный пост"""
        try:
            albums_dir = Config.ALBUMS_DIR
            albums = [d for d in os.listdir(albums_dir) 
                     if os.path.isdir(os.path.join(albums_dir, d))]
            
            if not albums:
                print("⚠️ Нет альбомных постов")
                return False
            
            # Берём первый альбом
            album_name = albums[0]
            album_path = os.path.join(albums_dir, album_name)
            
            # Получаем описание
            caption = self._get_media_description(album_name)
            
            # Собираем пути к файлам
            files = []
            for file in os.listdir(album_path):
                files.append(os.path.join(album_path, file))
            
            # Загружаем альбом
            upload_process = Process(
                target=self.client.album_upload,
                args=(files, caption)
            )
            upload_process.start()
            upload_process.join()
            
            print(f"✅ Загружен альбомный пост: {album_name}")
            
            # Удаляем директорию альбома
            shutil.rmtree(album_path)
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке альбома: {e}")
            return False
    
    # ========================================
    # IGTV
    # ========================================
    
    def upload_igtv(self) -> bool:
        """Загружает IGTV видео"""
        try:
            directory = Config.IGTV_DIR
            filename = get_oldest_file(directory)
            
            if not filename:
                print("⚠️ Нет IGTV видео")
                return False
            
            file_path = os.path.join(directory, filename)
            
            # Получаем описание
            caption = self._get_media_description(filename)
            if not caption or caption.strip() == "":
                caption = self.default_caption
            
            # Добавляем водяной знак
            watermarked_path, original_path = self._add_watermark(file_path)
            
            # Загружаем
            upload_process = Process(
                target=self.client.igtv_upload,
                args=(watermarked_path, caption, " ")
            )
            upload_process.start()
            upload_process.join()
            
            print(f"✅ Загружено IGTV: {filename}")
            
            # Очищаем
            self._cleanup_files(watermarked_path, original_path)
            remove_files_by_pattern(directory, f"with_wm_{filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке IGTV: {e}")
            return False
    
    # ========================================
    # Reels (Clips)
    # ========================================
    
    def upload_clip(self) -> bool:
        """Загружает клип (Reels)"""
        try:
            directory = Config.CLIPS_DIR
            filename = get_oldest_file(directory)
            
            if not filename:
                print("⚠️ Нет клипов")
                return False
            
            file_path = os.path.join(directory, filename)
            
            # Получаем описание
            caption = self._get_media_description(filename)
            
            # Добавляем водяной знак
            watermarked_path, original_path = self._add_watermark(file_path)
            
            # Загружаем
            upload_process = Process(
                target=self.client.clip_upload,
                args=(watermarked_path, caption)
            )
            upload_process.start()
            upload_process.join()
            
            print(f"✅ Загружен клип: {filename}")
            
            # Очищаем
            self._cleanup_files(watermarked_path, original_path)
            remove_files_by_pattern(directory, f"with_wm_{filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке клипа: {e}")
            return False


def create_instagram_client() -> Client:
    """
    Создаёт и аутентифицирует Instagram клиент
    
    Returns:
        Client: Аутентифицированный клиент
    """
    import json
    
    session_file = Config.INSTAGRAM_SESSION_FILE
    
    # Пробуем загрузить существующую сессию
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            client = Client(session_data)
            print("✅ Instagram сессия загружена из файла")
            return client
        except Exception as e:
            print(f"⚠️ Не удалось загрузить сессию: {e}")
    
    # Если сессии нет или она не работает, логинимся
    client = Client()
    client.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
    
    # Сохраняем сессию
    with open(session_file, 'w') as f:
        json.dump(client.get_settings(), f, indent=2)
    
    print("✅ Успешная аутентификация в Instagram")
    return client


if __name__ == "__main__":
    print("✅ Модуль uploaders.py загружен успешно!")

