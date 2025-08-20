#!/usr/bin/env python3
"""
Скрипт для проверки переменных окружения
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def check_telegram_vars():
    """Проверяет переменные окружения для Telegram"""
    print("🔍 Проверка переменных окружения для Telegram")
    print("=" * 50)
    
    # Проверяем обязательные переменные
    required_vars = {
        'TELEGRAM_API_ID': 'API ID приложения',
        'TELEGRAM_API_HASH': 'API Hash приложения', 
        'TELEGRAM_PHONE': 'Номер телефона аккаунта'
    }
    
    all_good = True
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            if var_name == 'TELEGRAM_API_HASH':
                # Скрываем хеш для безопасности
                display_value = value[:10] + '...' + value[-10:] if len(value) > 20 else '***'
            else:
                display_value = value
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"❌ {var_name}: НЕ УСТАНОВЛЕН")
            all_good = False
    
    print()
    
    # Проверяем опциональные переменные
    optional_vars = {
        'LAWYER_CLIENT_ENABLED': 'Включение клиента юриста',
        'BOT_TOKEN': 'Токен бота',
        'OPENROUTER_API_KEY': 'API ключ OpenRouter'
    }
    
    for var_name, description in optional_vars.items():
        value = os.getenv(var_name)
        if value:
            if 'KEY' in var_name or 'TOKEN' in var_name:
                display_value = value[:10] + '...' + value[-10:] if len(value) > 20 else '***'
            else:
                display_value = value
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"⚠️  {var_name}: НЕ УСТАНОВЛЕН (опционально)")
    
    print()
    
    if all_good:
        print("✅ Все обязательные переменные установлены!")
        print("🚀 Можно запускать бота: python main.py")
    else:
        print("❌ Не все обязательные переменные установлены")
        print("📝 Создайте файл .env и заполните обязательные переменные")
        print("📖 См. SETUP_INSTRUCTIONS.md для подробных инструкций")
    
    return all_good

def show_env_template():
    """Показывает шаблон .env файла"""
    print("\n📝 Шаблон файла .env:")
    print("=" * 50)
    print("""# Основные настройки бота
BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Настройки для входа в аккаунт юриста
TELEGRAM_API_ID=ваш_api_id_здесь
TELEGRAM_API_HASH=ваш_api_hash_здесь
TELEGRAM_PHONE=+7XXXXXXXXXX

# Включение клиента юриста
LAWYER_CLIENT_ENABLED=true

# ID юриста для проверки кодовых слов
LAWYER_TELEGRAM_ID=ваш_telegram_id_здесь

# Настройки ЮKassa
YOOKASSA_SHOP_ID=your_shop_id_here
YOOKASSA_SECRET_KEY=your_secret_key_here

# Настройки базы данных
DATABASE_URL=postgresql://username:password@localhost:5432/database_name""")

if __name__ == "__main__":
    print("🔍 Проверка настроек Telegram аккаунта")
    print("=" * 50)
    
    # Проверяем переменные
    is_ready = check_telegram_vars()
    
    if not is_ready:
        show_env_template()
        print("\n💡 Для получения API ID и API Hash:")
        print("1. Перейдите на https://my.telegram.org/")
        print("2. Войдите в аккаунт @narhipovd")
        print("3. Создайте новое приложение")
        print("4. Скопируйте api_id и api_hash")
