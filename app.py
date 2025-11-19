"""
Instagram Auto Publisher - Точка входа
=======================================

Главный файл для запуска приложения.
"""

import sys
import threading
import schedule
import time
from pathlib import Path

# Добавляем путь к src в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.database import get_database
from src.bot import InstagramBot


def reset_daily_stats():
    """Сбрасывает ежедневную статистику"""
    db = get_database()
    db.reset_daily_stats()


def run_scheduler():
    """Запускает планировщик сброса статистики"""
    reset_time = Config.DAILY_RESET_TIME
    schedule.every().day.at(reset_time).do(reset_daily_stats)
    
    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    """Главная функция запуска приложения"""
    print("=" * 60)
    print("  Instagram Auto Publisher v2.0")
    print("  Автоматизированная система управления Instagram контентом")
    print("=" * 60)
    
    try:
        # Валидируем конфигурацию
        print("\n🔍 Проверка конфигурации...")
        Config.validate()
        print("✅ Конфигурация валидна")
        
        # Создаём необходимые директории
        print("\n📁 Создание директорий...")
        Config.create_directories()
        print("✅ Директории готовы")
        
        # Инициализируем базу данных
        print("\n💾 Инициализация базы данных...")
        db = get_database()
        print(f"✅ База данных подключена: {db.db_path}")
        
        # Отключаем автопостинг при старте
        db.set_setting("autopost_status", False)
        
        # Запускаем планировщик сброса статистики в отдельном потоке
        print(f"\n⏰ Настройка ежедневного сброса статистики ({Config.DAILY_RESET_TIME})...")
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print("✅ Планировщик запущен")
        
        # Создаём и запускаем бота
        print("\n🤖 Инициализация Telegram бота...")
        bot = InstagramBot()
        
        print("\n" + "=" * 60)
        print("✅ Система успешно запущена!")
        print("📱 Telegram бот готов к работе")
        print("=" * 60)
        print("\n💡 Для остановки нажмите Ctrl+C\n")
        
        # Запускаем бота (бесконечный цикл)
        bot.run()
        
    except ValueError as e:
        print(f"\n❌ Ошибка конфигурации: {e}")
        print("\n💡 Убедитесь, что:")
        print("   1. Создан файл .env")
        print("   2. Все необходимые переменные установлены")
        print("   3. См. env.example.txt для примера")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⏸️ Получен сигнал остановки...")
        print("👋 Завершение работы. До свидания!")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

