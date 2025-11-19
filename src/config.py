"""
Конфигурация приложения
======================

Загружает и управляет всеми настройками из переменных окружения (.env файл).
Обеспечивает безопасное хранение токенов и ключей API.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()


class Config:
    """Централизованное хранилище конфигурации приложения"""
    
    # ========================================
    # Instagram настройки
    # ========================================
    INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")
    INSTAGRAM_SESSION_FILE: str = os.getenv("INSTAGRAM_SESSION_FILE", "authorize.json")
    
    # ========================================
    # Telegram Bot настройки
    # ========================================
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_ID_1: Optional[int] = int(os.getenv("TELEGRAM_ADMIN_ID_1", "0")) or None
    TELEGRAM_ADMIN_ID_2: Optional[int] = int(os.getenv("TELEGRAM_ADMIN_ID_2", "0")) or None
    
    @classmethod
    def get_admin_ids(cls) -> list[int]:
        """Возвращает список ID администраторов (фильтрует пустые значения)"""
        return [admin_id for admin_id in [cls.TELEGRAM_ADMIN_ID_1, cls.TELEGRAM_ADMIN_ID_2] if admin_id]
    
    # ========================================
    # API ключи
    # ========================================
    HIKER_API_KEY: str = os.getenv("HIKER_API_KEY", "")
    TIKTOK_API_HOST: str = os.getenv("TIKTOK_API_HOST", "")
    
    # ========================================
    # Контент настройки
    # ========================================
    DEFAULT_CAPTION: str = os.getenv("DEFAULT_CAPTION", "Подписывайся на ...")
    WATERMARK_LOGO_PATH: str = os.getenv("WATERMARK_LOGO_PATH", "logo.png")
    
    # ========================================
    # Расписание
    # ========================================
    DAILY_RESET_TIME: str = os.getenv("DAILY_RESET_TIME", "20:00")
    MORNING_TIME_RANGE: str = os.getenv("MORNING_TIME_RANGE", "08:00:00-12:00:00")
    DAY_TIME_RANGE: str = os.getenv("DAY_TIME_RANGE", "12:00:00-18:00:00")
    EVENING_TIME_RANGE: str = os.getenv("EVENING_TIME_RANGE", "18:00:00-23:00:00")
    
    # Контент по умолчанию для каждого периода дня
    MORNING_CONTENT: str = os.getenv("MORNING_CONTENT", "СВ-СФ-ФП")
    DAY_CONTENT: str = os.getenv("DAY_CONTENT", "ВП-К-ФП")
    EVENING_CONTENT: str = os.getenv("EVENING_CONTENT", "СВ-АП-К")
    
    # ========================================
    # База данных
    # ========================================
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "db.db")
    
    # ========================================
    # Пути к директориям
    # ========================================
    CONTENT_BASE_DIR: str = os.getenv("CONTENT_BASE_DIR", "users_content")
    STORIES_VIDEO_DIR: str = os.getenv("STORIES_VIDEO_DIR", "storys/video")
    STORIES_PHOTO_DIR: str = os.getenv("STORIES_PHOTO_DIR", "storys/photo")
    POSTS_VIDEO_DIR: str = os.getenv("POSTS_VIDEO_DIR", "video_posts")
    POSTS_PHOTO_DIR: str = os.getenv("POSTS_PHOTO_DIR", "photo_posts")
    ALBUMS_DIR: str = os.getenv("ALBUMS_DIR", "albums_posts")
    IGTV_DIR: str = os.getenv("IGTV_DIR", "video_posts/igtv")
    CLIPS_DIR: str = os.getenv("CLIPS_DIR", "video_posts/clips")
    
    @classmethod
    def validate(cls) -> bool:
        """
        Проверяет наличие всех критических настроек
        
        Returns:
            bool: True если все критические настройки присутствуют
        
        Raises:
            ValueError: Если отсутствуют критические настройки
        """
        errors = []
        
        # Проверка Instagram credentials
        if not cls.INSTAGRAM_USERNAME:
            errors.append("INSTAGRAM_USERNAME не установлен")
        if not cls.INSTAGRAM_PASSWORD:
            errors.append("INSTAGRAM_PASSWORD не установлен")
            
        # Проверка Telegram токена
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN не установлен")
            
        # Проверка ID администраторов
        if not cls.get_admin_ids():
            errors.append("Не установлен ни один TELEGRAM_ADMIN_ID")
            
        if errors:
            error_msg = "Отсутствуют критические настройки:\n" + "\n".join(f"- {e}" for e in errors)
            raise ValueError(error_msg)
            
        return True
    
    @classmethod
    def create_directories(cls) -> None:
        """Создаёт все необходимые директории для контента"""
        directories = [
            cls.CONTENT_BASE_DIR,
            cls.STORIES_VIDEO_DIR,
            cls.STORIES_PHOTO_DIR,
            cls.POSTS_VIDEO_DIR,
            cls.POSTS_PHOTO_DIR,
            cls.ALBUMS_DIR,
            cls.IGTV_DIR,
            cls.CLIPS_DIR,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


# Константы для типов контента (используются в расписании)
CONTENT_TYPES = {
    "СВ": "story_video",      # Сторис видео
    "СФ": "story_photo",      # Сторис фото
    "ВП": "video_post",       # Видео пост
    "ФП": "photo_post",       # Фото пост
    "АП": "album_post",       # Альбомный пост
    "ИТ": "igtv",             # IGTV
    "К": "clip",              # Клип (Reels)
}

# Обратный словарь
CONTENT_TYPES_REVERSE = {v: k for k, v in CONTENT_TYPES.items()}


def get_config() -> Config:
    """
    Получает экземпляр конфигурации и валидирует его
    
    Returns:
        Config: Валидированная конфигурация
    """
    Config.validate()
    return Config


if __name__ == "__main__":
    # Тест конфигурации
    try:
        config = get_config()
        print("✅ Конфигурация успешно загружена и валидирована!")
        print(f"Instagram пользователь: {config.INSTAGRAM_USERNAME}")
        print(f"Администраторы: {config.get_admin_ids()}")
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")

