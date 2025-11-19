"""
Скрипт первоначальной настройки Instagram
==========================================

Помогает создать файл сессии Instagram (authorize.json)
"""

import json
import os
from instagrapi import Client


def setup_instagram():
    """Первоначальная настройка Instagram аккаунта"""
    
    print("=" * 60)
    print("  Instagram Auto Publisher - Настройка Instagram")
    print("=" * 60)
    
    print("\nЭтот скрипт поможет создать файл сессии Instagram.")
    print("Файл сессии позволяет боту работать без повторной авторизации.\n")
    
    # Проверяем наличие существующей сессии
    if os.path.exists('authorize.json'):
        print("⚠️ Файл authorize.json уже существует!")
        response = input("Хотите создать новый? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("❌ Операция отменена")
            return
        
        # Создаём бэкап старого файла
        backup_name = 'authorize_backup.json'
        os.rename('authorize.json', backup_name)
        print(f"✅ Старый файл сохранён как {backup_name}")
    
    # Запрашиваем данные для входа
    print("\n📝 Введите данные для входа в Instagram:")
    username = input("Логин: ").strip()
    password = input("Пароль: ").strip()
    
    if not username or not password:
        print("❌ Логин и пароль не могут быть пустыми!")
        return
    
    print("\n⏳ Попытка авторизации...")
    
    try:
        # Создаём клиент и логинимся
        client = Client()
        client.login(username, password)
        
        print("✅ Успешная авторизация!")
        
        # Сохраняем сессию
        settings = client.get_settings()
        
        with open('authorize.json', 'w') as f:
            json.dump(settings, f, indent=2)
        
        print("✅ Файл сессии создан: authorize.json")
        
        # Получаем информацию об аккаунте
        user_info = client.account_info()
        print(f"\n📊 Информация об аккаунте:")
        print(f"   Username: @{user_info.username}")
        print(f"   Full Name: {user_info.full_name}")
        print(f"   Followers: {user_info.follower_count}")
        print(f"   Following: {user_info.following_count}")
        print(f"   Posts: {user_info.media_count}")
        
        print("\n" + "=" * 60)
        print("✅ Настройка завершена успешно!")
        print("=" * 60)
        print("\n💡 Теперь вы можете запустить основное приложение:")
        print("   python app.py")
        print("\n   или через Docker:")
        print("   docker-compose up -d")
        
    except Exception as e:
        print(f"\n❌ Ошибка при авторизации: {e}")
        print("\n💡 Возможные причины:")
        print("   - Неверный логин или пароль")
        print("   - Включена двухфакторная аутентификация (отключите её)")
        print("   - Instagram заблокировал попытку входа")
        print("   - Проблемы с интернет-соединением")
        
        if os.path.exists('authorize.json'):
            os.remove('authorize.json')


if __name__ == "__main__":
    try:
        setup_instagram()
    except KeyboardInterrupt:
        print("\n\n⏸️ Операция прервана пользователем")
    except Exception as e:
        print(f"\n❌ Непредвиденная ошибка: {e}")

