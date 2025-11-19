"""
Вспомогательные утилиты
======================

Общие функции для работы с файлами, путями и медиа.
"""

import os
import pathlib
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image


def convert_webp_to_jpeg(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Конвертирует WEBP изображение в JPEG
    
    Args:
        input_path: Путь к исходному WEBP файлу
        output_path: Путь для сохранения JPEG (опционально)
    
    Returns:
        str: Путь к созданному JPEG файлу
    """
    if not input_path.endswith(".webp"):
        return input_path
    
    # Определяем путь для выходного файла
    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + ".jpg"
    
    # Конвертируем
    with Image.open(input_path) as img:
        rgb_img = img.convert("RGB")
        rgb_img.save(output_path, "JPEG")
    
    # Удаляем исходный WEBP файл
    try:
        os.remove(input_path)
    except OSError:
        pass
    
    return output_path


def get_oldest_file(directory: str) -> Optional[str]:
    """
    Находит самый старый файл в директории
    
    Args:
        directory: Путь к директории
    
    Returns:
        str: Имя самого старого файла или None если директория пуста
    """
    if not os.path.exists(directory):
        return None
    
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    if not files:
        return None
    
    files_with_path = [os.path.join(directory, f) for f in files]
    oldest_file = min(files_with_path, key=os.path.getctime)
    
    return os.path.basename(oldest_file)


def count_files_in_directory(directory: str, extension: Optional[str] = None) -> int:
    """
    Подсчитывает количество файлов в директории
    
    Args:
        directory: Путь к директории
        extension: Фильтр по расширению (например, '.mp4')
    
    Returns:
        int: Количество файлов
    """
    if not os.path.exists(directory):
        return 0
    
    files = os.listdir(directory)
    
    if extension:
        files = [f for f in files if f.endswith(extension)]
    
    return len(files)


def remove_file_safely(file_path: str, max_attempts: int = 10) -> bool:
    """
    Безопасно удаляет файл с несколькими попытками
    
    Args:
        file_path: Путь к файлу
        max_attempts: Максимальное количество попыток
    
    Returns:
        bool: True если файл удалён успешно
    """
    import time
    
    for _ in range(max_attempts):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except OSError:
            time.sleep(0.1)
    
    return False


def remove_files_by_pattern(directory: str, pattern: str) -> int:
    """
    Удаляет файлы по паттерну в имени
    
    Args:
        directory: Путь к директории
        pattern: Паттерн для поиска в имени файла
    
    Returns:
        int: Количество удалённых файлов
    """
    if not os.path.exists(directory):
        return 0
    
    removed_count = 0
    for filename in os.listdir(directory):
        if pattern in filename:
            file_path = os.path.join(directory, filename)
            if remove_file_safely(file_path):
                removed_count += 1
    
    return removed_count


def ensure_directory(directory: str) -> None:
    """
    Создаёт директорию если она не существует
    
    Args:
        directory: Путь к директории
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """
    Получает расширение файла в нижнем регистре
    
    Args:
        filename: Имя файла
    
    Returns:
        str: Расширение файла (включая точку)
    """
    return os.path.splitext(filename)[1].lower()


def is_video_file(filename: str) -> bool:
    """Проверяет, является ли файл видео"""
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}
    return get_file_extension(filename) in video_extensions


def is_image_file(filename: str) -> bool:
    """Проверяет, является ли файл изображением"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
    return get_file_extension(filename) in image_extensions


def extract_media_pk_from_filename(filename: str) -> str:
    """
    Извлекает media PK из имени файла
    
    Args:
        filename: Имя файла (может содержать underscores)
    
    Returns:
        str: Извлечённый PK
    """
    # Удаляем расширение
    name_without_ext = os.path.splitext(filename)[0]
    
    # Если есть underscores, берём последнюю часть
    if '_' in name_without_ext:
        parts = name_without_ext.split('_')
        return parts[-1]
    
    return name_without_ext


def get_content_type_from_path(file_path: str) -> str:
    """
    Определяет тип контента по пути к файлу
    
    Args:
        file_path: Полный путь к файлу
    
    Returns:
        str: Тип контента (story, clip, igtv, post, album)
    """
    path = pathlib.Path(file_path)
    
    # Проверяем родительские директории
    parts = path.parts
    
    if 'storys' in parts or 'story' in parts:
        return 'story'
    elif 'clips' in parts:
        return 'clip'
    elif 'igtv' in parts:
        return 'igtv'
    elif 'albums' in parts or 'albums_posts' in parts:
        return 'album'
    else:
        return 'post'


def format_file_size(size_bytes: int) -> str:
    """
    Форматирует размер файла в человекочитаемый вид
    
    Args:
        size_bytes: Размер в байтах
    
    Returns:
        str: Отформатированный размер (например, "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """
    Очищает имя файла от недопустимых символов
    
    Args:
        filename: Исходное имя файла
    
    Returns:
        str: Очищенное имя файла
    """
    # Удаляем или заменяем недопустимые символы
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    return filename


if __name__ == "__main__":
    # Тестирование утилит
    print("✅ Модуль utils.py загружен успешно!")

