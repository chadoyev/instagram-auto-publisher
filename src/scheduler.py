"""
Планировщик автопостинга
========================

Улучшенная система автоматической публикации контента по расписанию.
"""

import time
import random
import math
import threading
from datetime import datetime, date, time as dt_time, timedelta
from typing import Dict, Callable, Optional

from .config import Config, CONTENT_TYPES
from .database import get_database
from .uploaders import InstagramUploader


class ContentScheduler:
    """Планировщик для автоматической публикации контента"""
    
    def __init__(self, uploader: InstagramUploader):
        """
        Инициализация планировщика
        
        Args:
            uploader: Экземпляр InstagramUploader для публикации
        """
        self.uploader = uploader
        self.db = get_database()
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        
        # Маппинг типов контента на функции загрузки
        self.upload_functions: Dict[str, Callable] = {
            "СВ": self.uploader.upload_story_video,   # Сторис видео
            "СФ": self.uploader.upload_story_photo,   # Сторис фото
            "ВП": self.uploader.upload_video_post,    # Видео пост
            "ФП": self.uploader.upload_photo_post,    # Фото пост
            "АП": self.uploader.upload_album_post,    # Альбомный пост
            "ИТ": self.uploader.upload_igtv,          # IGTV
            "К": self.uploader.upload_clip,           # Клип (Reels)
        }
        
        # Маппинг типов контента на поля счётчиков в БД
        self.content_counters = {
            "СВ": "uploaded_video_story",
            "СФ": "uploaded_photo_story",
            "ВП": "uploaded_video_posts",
            "ФП": "uploaded_photo_posts",
            "АП": "uploaded_album_posts",
            "ИТ": "uploaded_igtv",
            "К": "uploaded_clips",
        }
        
        print("✅ Планировщик инициализирован")
    
    def _parse_time_range(self, time_range: str) -> tuple[dt_time, dt_time]:
        """
        Парсит временной диапазон из строки
        
        Args:
            time_range: Строка вида "HH:MM:SS-HH:MM:SS"
        
        Returns:
            tuple: (время_начала, время_конца)
        """
        start_str, end_str = time_range.split('-')
        start_time = datetime.strptime(start_str.strip(), "%H:%M:%S").time()
        end_time = datetime.strptime(end_str.strip(), "%H:%M:%S").time()
        return start_time, end_time
    
    def _calculate_interval(self, start_time: dt_time, end_time: dt_time, 
                           content_count: int) -> int:
        """
        Вычисляет интервал между публикациями
        
        Args:
            start_time: Время начала периода
            end_time: Время окончания периода
            content_count: Количество контента для публикации
        
        Returns:
            int: Интервал в секундах
        """
        # Вычисляем разницу во времени в минутах
        time_diff = (datetime.combine(date.min, end_time) - 
                    datetime.combine(date.min, start_time)).total_seconds() / 60
        
        # Вычисляем средний интервал
        if content_count == 0:
            return 0
        
        avg_interval_minutes = time_diff / content_count
        return int(avg_interval_minutes * 60)  # Конвертируем в секунды
    
    def _get_random_interval(self, base_interval: int) -> int:
        """
        Добавляет случайность к интервалу для более естественного поведения
        
        Args:
            base_interval: Базовый интервал в секундах
        
        Returns:
            int: Интервал с случайным отклонением
        """
        # Добавляем случайное отклонение ±20 секунд
        min_interval = max(base_interval - 20, 60)  # Минимум 1 минута
        return random.randint(min_interval, base_interval)
    
    def _post_content_sequence(self, phase_name: str, start_time: dt_time, 
                               end_time: dt_time) -> None:
        """
        Публикует последовательность контента для определённой фазы дня
        
        Args:
            phase_name: Название фазы (morning_content, day_content, evening_content)
            start_time: Время начала фазы
            end_time: Время окончания фазы
        """
        # Получаем последовательность контента из БД
        content_sequence = self.db.get_setting(phase_name)
        content_types = content_sequence.split('-')
        
        # Вычисляем интервал между публикациями
        interval = self._calculate_interval(start_time, end_time, len(content_types))
        
        # Получаем текущую позицию (для продолжения после перезапуска)
        current_position_str = self.db.get_setting("current_position_content")
        current_phase, current_index = current_position_str.split('-')
        
        # Определяем с какой позиции начинать
        phase_key = phase_name.replace('_content', '')  # morning, day, evening
        
        if current_phase == "0":
            start_index = 0
        elif current_phase == phase_key:
            start_index = int(current_index)
        else:
            start_index = 0
        
        print(f"\n📅 Начинаю публикацию для фазы: {phase_key}")
        print(f"📝 Последовательность: {content_sequence}")
        print(f"⏱️ Интервал между публикациями: ~{interval // 60} мин")
        
        # Публикуем контент
        for i in range(start_index, len(content_types)):
            if not self.is_running:
                print("⚠️ Планировщик остановлен")
                return
            
            content_type = content_types[i]
            
            # Проверяем наличие контента этого типа
            if content_type in self.upload_functions:
                print(f"\n📤 Публикую {content_type} ({i + 1}/{len(content_types)})...")
                
                try:
                    # Публикуем
                    upload_func = self.upload_functions[content_type]
                    success = upload_func()
                    
                    if success:
                        # Увеличиваем счётчик
                        counter_field = self.content_counters[content_type]
                        self.db.increment_setting(counter_field)
                        
                        # Обновляем позицию
                        self.db.set_setting(
                            "current_position_content",
                            f"{phase_key}-{i + 1}"
                        )
                        
                        print(f"✅ Успешно опубликовано: {content_type}")
                    else:
                        print(f"⚠️ Не удалось опубликовать {content_type} (возможно нет контента)")
                    
                except Exception as e:
                    print(f"❌ Ошибка при публикации {content_type}: {e}")
            
            # Ждём до следующей публикации (кроме последней)
            if i < len(content_types) - 1:
                sleep_time = self._get_random_interval(interval)
                print(f"⏳ Жду {sleep_time // 60} мин до следующей публикации...")
                time.sleep(sleep_time)
        
        # Помечаем фазу как завершённую
        self.db.set_setting(f"{phase_key}_process", True)
        print(f"✅ Фаза {phase_key} завершена")
    
    def _should_post_phase(self, current_time: dt_time, start_time: dt_time, 
                          end_time: dt_time, phase_name: str) -> bool:
        """
        Проверяет, нужно ли публиковать контент для данной фазы
        
        Args:
            current_time: Текущее время
            start_time: Время начала фазы
            end_time: Время окончания фазы
            phase_name: Название фазы (morning, day, evening)
        
        Returns:
            bool: True если нужно публиковать
        """
        # Проверяем, находимся ли мы в временном диапазоне
        if not (start_time <= current_time < end_time):
            return False
        
        # Проверяем, не была ли фаза уже выполнена
        process_field = f"{phase_name}_process"
        is_completed = self.db.get_setting(process_field)
        
        return not is_completed
    
    def _reset_daily_processes(self) -> None:
        """Сбрасывает флаги завершения фаз"""
        self.db.set_setting("morning_process", False)
        self.db.set_setting("day_process", False)
        self.db.set_setting("evening_process", False)
        print("🔄 Флаги фаз сброшены")
    
    def _run_loop(self, morning_range: str, day_range: str, evening_range: str) -> None:
        """
        Основной цикл планировщика
        
        Args:
            morning_range: Временной диапазон для утра
            day_range: Временной диапазон для дня
            evening_range: Временной диапазон для вечера
        """
        # Парсим временные диапазоны
        morning_start, morning_end = self._parse_time_range(morning_range)
        day_start, day_end = self._parse_time_range(day_range)
        evening_start, evening_end = self._parse_time_range(evening_range)
        
        print("⏰ Планировщик запущен!")
        print(f"🌅 Утро: {morning_range}")
        print(f"☀️ День: {day_range}")
        print(f"🌙 Вечер: {evening_range}")
        
        last_reset_date = datetime.now().date()
        
        while self.is_running:
            try:
                current_time = datetime.now().time()
                current_date = datetime.now().date()
                
                # Сброс флагов в полночь
                if current_date > last_reset_date:
                    self._reset_daily_processes()
                    last_reset_date = current_date
                
                # Проверяем утреннюю фазу
                if self._should_post_phase(current_time, morning_start, morning_end, "morning"):
                    self._post_content_sequence("morning_content", morning_start, morning_end)
                
                # Проверяем дневную фазу
                elif self._should_post_phase(current_time, day_start, day_end, "day"):
                    self._post_content_sequence("day_content", day_start, day_end)
                
                # Проверяем вечернюю фазу
                elif self._should_post_phase(current_time, evening_start, evening_end, "evening"):
                    self._post_content_sequence("evening_content", evening_start, evening_end)
                
                # Если все фазы завершены, ждём следующего дня
                morning_done = self.db.get_setting("morning_process")
                day_done = self.db.get_setting("day_process")
                evening_done = self.db.get_setting("evening_process")
                
                if morning_done and day_done and evening_done:
                    # Сбрасываем флаги для следующего дня
                    self._reset_daily_processes()
                
                # Пауза перед следующей проверкой
                time.sleep(60)  # Проверяем каждую минуту
                
            except Exception as e:
                print(f"❌ Ошибка в цикле планировщика: {e}")
                time.sleep(60)
    
    def start(self, morning_range: Optional[str] = None, 
             day_range: Optional[str] = None,
             evening_range: Optional[str] = None) -> None:
        """
        Запускает планировщик
        
        Args:
            morning_range: Временной диапазон для утра (из БД если не указан)
            day_range: Временной диапазон для дня (из БД если не указан)
            evening_range: Временной диапазон для вечера (из БД если не указан)
        """
        if self.is_running:
            print("⚠️ Планировщик уже запущен")
            return
        
        # Получаем временные диапазоны из БД если не переданы
        morning_range = morning_range or self.db.get_setting("morning_time")
        day_range = day_range or self.db.get_setting("day_time")
        evening_range = evening_range or self.db.get_setting("evening_time")
        
        # Запускаем в отдельном потоке
        self.is_running = True
        self.thread = threading.Thread(
            target=self._run_loop,
            args=(morning_range, day_range, evening_range),
            daemon=True
        )
        self.thread.start()
    
    def stop(self) -> None:
        """Останавливает планировщик"""
        if not self.is_running:
            print("⚠️ Планировщик не запущен")
            return
        
        print("🛑 Останавливаю планировщик...")
        self.is_running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        print("✅ Планировщик остановлен")
    
    def is_active(self) -> bool:
        """Проверяет, активен ли планировщик"""
        return self.is_running


if __name__ == "__main__":
    print("✅ Модуль scheduler.py загружен успешно!")

