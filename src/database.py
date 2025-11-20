"""
Работа с базой данных
====================

Обеспечивает безопасную работу с SQLite базой данных.
Использует параметризованные запросы для защиты от SQL-инъекций.
"""

import sqlite3
from typing import Optional, Any, List, Tuple
from pathlib import Path
import threading
from contextlib import contextmanager

from .config import Config


class Database:
    """Класс для работы с SQLite базой данных"""
    
    def __init__(self, db_path: str = None):
        """
        Инициализация подключения к базе данных
        
        Args:
            db_path: Путь к файлу базы данных (по умолчанию из конфигурации)
        """
        self.db_path = db_path or Config.DATABASE_PATH
        self._local = threading.local()
        self._ensure_tables()
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Получить thread-safe соединение с БД"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row  # Доступ к столбцам по имени
        return self._local.conn
    
    @property
    def cursor(self) -> sqlite3.Cursor:
        """Получить курсор для текущего соединения"""
        return self.connection.cursor()
    
    def _ensure_tables(self) -> None:
        """Создаёт необходимые таблицы если они не существуют"""
        # Таблица пользователей (структура из OLD версии)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                user_name TEXT,
                user_surname TEXT,
                username TEXT,
                active_content TEXT DEFAULT 'NO',
                active_menu TEXT DEFAULT 'menu',
                album_messages TEXT DEFAULT '[]',
                tiktok_loaded INTEGER DEFAULT 0,
                yt_loaded INTEGER DEFAULT 0,
                instagram_loaded INTEGER DEFAULT 0,
                approved_content INTEGER DEFAULT 0
            )
        """)
        
        # Таблица контента (структура из OLD версии)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS contents (
                user_id INTEGER,
                link_content TEXT UNIQUE,
                media_pk TEXT,
                content_description TEXT
            )
        """)
        
        # Таблица описаний медиа (из OLD версии для совместимости)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS media_descriptions (
                media_pk TEXT PRIMARY KEY,
                media_description TEXT
            )
        """)
        
        # Таблица настроек (структура из OLD версии)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                autopost_status INTEGER DEFAULT 0,
                morning_time TEXT DEFAULT '08:00:00-12:00:00',
                day_time TEXT DEFAULT '12:00:00-18:00:00',
                evening_time TEXT DEFAULT '18:00:00-23:00:00',
                morning_content TEXT DEFAULT 'СВ-СФ-ФП',
                day_content TEXT DEFAULT 'ВП-К-ФП',
                evening_content TEXT DEFAULT 'СВ-АП-К',
                uploaded_video_story INTEGER DEFAULT 0,
                uploaded_photo_story INTEGER DEFAULT 0,
                uploaded_video_posts INTEGER DEFAULT 0,
                uploaded_photo_posts INTEGER DEFAULT 0,
                uploaded_album_posts INTEGER DEFAULT 0,
                uploaded_igtv INTEGER DEFAULT 0,
                uploaded_clips INTEGER DEFAULT 0,
                current_position_content TEXT DEFAULT '0-0',
                morning_process INTEGER DEFAULT 0,
                day_process INTEGER DEFAULT 0,
                evening_process INTEGER DEFAULT 0
            )
        """)
        
        # Вставляем начальные настройки если их нет
        cursor = self.cursor
        cursor.execute("SELECT COUNT(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""INSERT INTO settings (
                autopost_status, morning_time, day_time, evening_time,
                morning_content, day_content, evening_content,
                uploaded_video_story, uploaded_photo_story, uploaded_video_posts,
                uploaded_photo_posts, uploaded_album_posts, uploaded_igtv,
                uploaded_clips, current_position_content,
                morning_process, day_process, evening_process
            ) VALUES (0, '08:00:00-12:00:00', '12:00:00-18:00:00', '18:00:00-23:00:00',
                     'СВ-СФ-ФП', 'ВП-К-ФП', 'СВ-АП-К',
                     0, 0, 0, 0, 0, 0, 0, '0-0', 0, 0, 0)""")
        
        self.connection.commit()
    
    # ========================================
    # Методы для работы с пользователями
    # ========================================
    
    def user_exists(self, user_id: int) -> bool:
        """Проверяет существование пользователя"""
        result = self.cursor.execute(
            "SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return result[0] > 0
    
    def add_user(self, user_id: int, user_name: str, user_surname: str, username: str) -> None:
        """Добавляет нового пользователя"""
        try:
            self.cursor.execute(
                """INSERT INTO users (user_id, user_name, user_surname, username) 
                   VALUES (?, ?, ?, ?)""",
                (user_id, user_name, user_surname, username)
            )
            self.connection.commit()
        except sqlite3.IntegrityError:
            # Пользователь уже существует
            pass
    
    def get_user_field(self, user_id: int, field: str) -> Any:
        """Получает значение поля пользователя"""
        result = self.cursor.execute(
            f"SELECT {field} FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return result[0] if result else None
    
    def set_user_field(self, user_id: int, field: str, value: Any) -> None:
        """Устанавливает значение поля пользователя"""
        self.cursor.execute(
            f"UPDATE users SET {field} = ? WHERE user_id = ?",
            (str(value), user_id)
        )
        self.connection.commit()
    
    def get_user_state(self, user_id: int, state_key: str) -> Optional[str]:
        """Получает временное состояние пользователя"""
        result = self.cursor.execute(
            f"SELECT {state_key} FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return result[0] if result else None
    
    def set_user_state(self, user_id: int, state_key: str, state_value: Optional[str]) -> None:
        """Устанавливает временное состояние пользователя"""
        self.cursor.execute(
            f"UPDATE users SET {state_key} = ? WHERE user_id = ?",
            (state_value, user_id)
        )
        self.connection.commit()
    
    # ========================================
    # Методы для работы с контентом
    # ========================================
    
    def add_content(self, user_id: int, link_content: str, media_pk: str, 
                    content_description: str) -> bool:
        """
        Добавляет контент в базу
        
        Returns:
            bool: True если добавлено успешно, False если уже существует
        """
        try:
            self.cursor.execute(
                """INSERT INTO contents (user_id, link_content, media_pk, content_description) 
                   VALUES (?, ?, ?, ?)""",
                (user_id, link_content, media_pk, content_description)
            )
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            # Контент уже существует
            return False
    
    def get_content_description(self, link_content: str) -> Optional[str]:
        """Получает описание контента по ссылке"""
        result = self.cursor.execute(
            "SELECT content_description FROM contents WHERE link_content = ?",
            (link_content,)
        ).fetchone()
        return result[0] if result else None
    
    def update_content_description(self, link_content: str, description: str) -> None:
        """Обновляет описание контента"""
        self.cursor.execute(
            "UPDATE contents SET content_description = ? WHERE link_content = ?",
            (description, link_content)
        )
        self.connection.commit()
    
    # ========================================
    # Методы для работы с настройками
    # ========================================
    
    def get_setting(self, field: str) -> Any:
        """Получает значение настройки"""
        result = self.cursor.execute(
            f"SELECT {field} FROM settings"
        ).fetchone()
        return result[0] if result else None
    
    def set_setting(self, field: str, value: Any) -> None:
        """Устанавливает значение настройки"""
        self.cursor.execute(
            f'UPDATE settings SET "{field}" = ?',
            (value,)
        )
        self.connection.commit()
    
    def increment_setting(self, field: str) -> None:
        """Увеличивает числовое значение настройки на 1"""
        current = self.get_setting(field)
        self.set_setting(field, int(current) + 1)
    
    def reset_daily_stats(self) -> None:
        """Сбрасывает ежедневную статистику загрузок"""
        stats_fields = [
            'uploaded_video_story',
            'uploaded_photo_story',
            'uploaded_video_posts',
            'uploaded_photo_posts',
            'uploaded_album_posts',
            'uploaded_igtv',
            'uploaded_clips'
        ]
        
        for field in stats_fields:
            self.set_setting(field, 0)
        
        self.set_setting('current_position_content', '0-0')
        print("✅ Произведен сброс значений загруженного контента")
    
    # ========================================
    # Методы для совместимости со старым кодом
    # ========================================
    
    def get_media_description(self, media_pk: str) -> str:
        """Получает описание медиа по PK (старая таблица)"""
        result = self.cursor.execute(
            "SELECT media_description FROM media_descriptions WHERE media_pk = ?",
            (media_pk,)
        ).fetchone()
        return result[0] if result else " "
    
    def close(self) -> None:
        """Закрывает соединение с базой данных"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()


# Singleton экземпляр базы данных
_db_instance: Optional[Database] = None


def get_database() -> Database:
    """
    Получить singleton экземпляр базы данных
    
    Returns:
        Database: Экземпляр базы данных
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


if __name__ == "__main__":
    # Тестирование базы данных
    db = get_database()
    print("✅ База данных успешно инициализирована!")
    print(f"Путь к БД: {db.db_path}")

