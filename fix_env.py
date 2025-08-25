#!/usr/bin/env python3
"""
Скрипт для проверки и исправления .env файла
"""

import os
import re
from dotenv import load_dotenv

def check_env_file():
    """Проверяет .env файл на корректность"""
    print("🔍 Проверка .env файла...")
    
    # Загружаем .env файл
    load_dotenv()
    
    # Список обязательных переменных
    required_vars = {
        'BOT_TOKEN': 'Токен Telegram бота',
        'OPENROUTER_API_KEY': 'Ключ API OpenRouter',
        'TELEGRAM_API_ID': 'API ID Telegram',
        'TELEGRAM_API_HASH': 'API Hash Telegram',
        'TELEGRAM_PHONE': 'Номер телефона',
        'LAWYER_TELEGRAM_ID': 'ID юриста в Telegram',
        'YOOKASSA_SHOP_ID': 'ID магазина ЮKassa',
        'YOOKASSA_SECRET_KEY': 'Секретный ключ ЮKassa'
    }
    
    # Список переменных базы данных
    db_vars = {
        'DATABASE_URL': 'URL базы данных',
        'PGHOST': 'Хост PostgreSQL',
        'PGDATABASE': 'Имя базы данных',
        'PGUSER': 'Пользователь PostgreSQL',
        'PGPASSWORD': 'Пароль PostgreSQL'
    }
    
    issues = []
    warnings = []
    
    # Проверяем обязательные переменные
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value or value.startswith('your_') or value == '0':
            issues.append(f"❌ {var}: {description} - не настроено или использует значение по умолчанию")
        elif var == 'LAWYER_TELEGRAM_ID' and not value.isdigit():
            issues.append(f"❌ {var}: {description} - должно быть числом, получено: {value}")
        else:
            print(f"✅ {var}: {description} - настроено")
    
    # Проверяем переменные базы данных
    database_url = os.getenv('DATABASE_URL')
    if database_url and (database_url.startswith('postgresql://') or database_url.startswith('your_')):
        if database_url.startswith('your_'):
            issues.append(f"❌ DATABASE_URL: использует значение по умолчанию")
        else:
            print(f"✅ DATABASE_URL: настроено")
    else:
        # Проверяем отдельные переменные PostgreSQL
        pg_host = os.getenv('PGHOST')
        pg_db = os.getenv('PGDATABASE')
        pg_user = os.getenv('PGUSER')
        pg_pass = os.getenv('PGPASSWORD')
        
        if not all([pg_host, pg_db, pg_user, pg_pass]):
            issues.append(f"❌ Переменные PostgreSQL: не все настроены")
        else:
            print(f"✅ Переменные PostgreSQL: настроены")
    
    # Проверяем LAWYER_CLIENT_ENABLED
    lawyer_enabled = os.getenv('LAWYER_CLIENT_ENABLED', 'false').lower()
    if lawyer_enabled not in ['true', 'false']:
        warnings.append(f"⚠️ LAWYER_CLIENT_ENABLED: должно быть 'true' или 'false', получено: {lawyer_enabled}")
    else:
        print(f"✅ LAWYER_CLIENT_ENABLED: {lawyer_enabled}")
    
    # Выводим результаты
    print("\n" + "="*50)
    
    if issues:
        print("❌ Найдены проблемы:")
        for issue in issues:
            print(f"  {issue}")
        print("\n🔧 Для исправления выполните:")
        print("  nano .env")
        print("  # И замените все 'your_*' на реальные значения")
    else:
        print("✅ Все обязательные переменные настроены корректно!")
    
    if warnings:
        print("\n⚠️ Предупреждения:")
        for warning in warnings:
            print(f"  {warning}")
    
    return len(issues) == 0

def create_env_template():
    """Создает шаблон .env файла"""
    template = """# Основные настройки бота
BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Настройки для входа в аккаунт юриста
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+7XXXXXXXXXX

# Включение клиента юриста
LAWYER_CLIENT_ENABLED=true

# ID юриста для проверки кодовых слов (должно быть числом)
LAWYER_TELEGRAM_ID=123456789

# Настройки ЮKassa
YOOKASSA_SHOP_ID=your_shop_id_here
YOOKASSA_SECRET_KEY=your_secret_key_here

# Настройки базы данных (выберите один способ)
# Способ 1: DATABASE_URL (рекомендуется)
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Способ 2: Отдельные переменные окружения
# PGHOST=localhost
# PGDATABASE=legal_bot
# PGUSER=legal_bot_user
# PGPASSWORD=your_password
# PGSSLMODE=require
# PGCHANNELBINDING=prefer
"""
    
    with open('.env.template', 'w', encoding='utf-8') as f:
        f.write(template)
    
    print("📝 Создан шаблон .env.template")
    print("💡 Скопируйте его в .env и заполните реальными значениями")

if __name__ == "__main__":
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("📝 Создаем шаблон...")
        create_env_template()
        print("\n🔧 Следующие шаги:")
        print("1. cp .env.template .env")
        print("2. nano .env")
        print("3. Заполните все значения")
        print("4. python fix_env.py")
    else:
        is_valid = check_env_file()
        if not is_valid:
            print("\n💡 Для создания шаблона выполните:")
            print("  python fix_env.py --template")
