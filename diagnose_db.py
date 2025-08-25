#!/usr/bin/env python3
"""
Скрипт для диагностики проблем с базой данных
"""

import os
import psycopg2
import time
from dotenv import load_dotenv
from loguru import logger

def test_connection():
    """Тестирует подключение к базе данных"""
    print("🔍 Тестирование подключения к базе данных...")
    
    load_dotenv()
    
    # Проверяем переменные окружения
    database_url = os.getenv('DATABASE_URL')
    pghost = os.getenv('PGHOST')
    pgdatabase = os.getenv('PGDATABASE')
    pguser = os.getenv('PGUSER')
    pgpassword = os.getenv('PGPASSWORD')
    
    print(f"📋 Переменные окружения:")
    print(f"   DATABASE_URL: {'Настроен' if database_url else 'Не настроен'}")
    print(f"   PGHOST: {pghost or 'Не настроен'}")
    print(f"   PGDATABASE: {pgdatabase or 'Не настроен'}")
    print(f"   PGUSER: {pguser or 'Не настроен'}")
    print(f"   PGPASSWORD: {'Настроен' if pgpassword else 'Не настроен'}")
    
    # Тестируем подключение
    connection = None
    try:
        if database_url:
            print("🔌 Подключение через DATABASE_URL...")
            connection = psycopg2.connect(
                database_url,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
                connect_timeout=10
            )
        else:
            print("🔌 Подключение через отдельные переменные...")
            connection = psycopg2.connect(
                host=pghost,
                database=pgdatabase,
                user=pguser,
                password=pgpassword,
                sslmode=os.getenv('PGSSLMODE'),
                channel_binding=os.getenv('PGCHANNELBINDING'),
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
                connect_timeout=10
            )
        
        print("✅ Подключение успешно установлено")
        
        # Тестируем простой запрос
        cursor = connection.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"📊 Версия PostgreSQL: {version[0]}")
        
        # Проверяем активные соединения
        cursor.execute("""
            SELECT count(*) as active_connections 
            FROM pg_stat_activity 
            WHERE state = 'active'
        """)
        active_connections = cursor.fetchone()[0]
        print(f"🔗 Активные соединения: {active_connections}")
        
        # Проверяем максимальное количество соединений
        cursor.execute("SHOW max_connections")
        max_connections = cursor.fetchone()[0]
        print(f"📈 Максимальное количество соединений: {max_connections}")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    finally:
        if connection:
            connection.close()

def test_retry_connection():
    """Тестирует retry логику подключения"""
    print("\n🔄 Тестирование retry логики...")
    
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    pghost = os.getenv('PGHOST')
    pgdatabase = os.getenv('PGDATABASE')
    pguser = os.getenv('PGUSER')
    pgpassword = os.getenv('PGPASSWORD')
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            print(f"   Попытка {attempt + 1}/{max_retries}...")
            
            if database_url:
                connection = psycopg2.connect(
                    database_url,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=5,
                    connect_timeout=10
                )
            else:
                connection = psycopg2.connect(
                    host=pghost,
                    database=pgdatabase,
                    user=pguser,
                    password=pgpassword,
                    sslmode=os.getenv('PGSSLMODE'),
                    channel_binding=os.getenv('PGCHANNELBINDING'),
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=5,
                    connect_timeout=10
                )
            
            print("   ✅ Подключение успешно")
            connection.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Попытка {attempt + 1} не удалась: {e}")
            if attempt < max_retries - 1:
                print(f"   ⏳ Ожидание {retry_delay} секунд...")
                time.sleep(retry_delay)
            else:
                print("   💥 Все попытки исчерпаны")
                return False

def check_postgresql_status():
    """Проверяет статус PostgreSQL"""
    print("\n🗄️  Проверка статуса PostgreSQL...")
    
    try:
        import subprocess
        result = subprocess.run(['systemctl', 'status', 'postgresql'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PostgreSQL запущен")
            return True
        else:
            print("❌ PostgreSQL не запущен")
            print("💡 Для запуска выполните: sudo systemctl start postgresql")
            return False
            
    except Exception as e:
        print(f"⚠️  Не удалось проверить статус PostgreSQL: {e}")
        return False

def check_network_connectivity():
    """Проверяет сетевое подключение"""
    print("\n🌐 Проверка сетевого подключения...")
    
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    pghost = os.getenv('PGHOST', 'localhost')
    
    if database_url:
        # Извлекаем хост из DATABASE_URL
        if '://' in database_url:
            host = database_url.split('://')[1].split('/')[0].split('@')[-1].split(':')[0]
        else:
            host = 'localhost'
    else:
        host = pghost
    
    print(f"🔍 Проверка подключения к {host}...")
    
    try:
        import subprocess
        result = subprocess.run(['ping', '-c', '3', host], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Хост {host} доступен")
            return True
        else:
            print(f"❌ Хост {host} недоступен")
            return False
            
    except Exception as e:
        print(f"⚠️  Не удалось проверить подключение: {e}")
        return False

def main():
    """Основная функция диагностики"""
    print("🔧 Диагностика проблем с базой данных")
    print("=" * 50)
    
    # Проверяем статус PostgreSQL
    postgresql_ok = check_postgresql_status()
    
    # Проверяем сетевое подключение
    network_ok = check_network_connectivity()
    
    # Тестируем подключение
    connection_ok = test_connection()
    
    # Тестируем retry логику
    retry_ok = test_retry_connection()
    
    print("\n" + "=" * 50)
    print("📊 Результаты диагностики:")
    print(f"   PostgreSQL: {'✅' if postgresql_ok else '❌'}")
    print(f"   Сеть: {'✅' if network_ok else '❌'}")
    print(f"   Подключение: {'✅' if connection_ok else '❌'}")
    print(f"   Retry логика: {'✅' if retry_ok else '❌'}")
    
    if not postgresql_ok:
        print("\n🔧 Рекомендации:")
        print("   sudo systemctl start postgresql")
        print("   sudo systemctl enable postgresql")
    
    if not connection_ok:
        print("\n🔧 Рекомендации:")
        print("   1. Проверьте .env файл")
        print("   2. Убедитесь, что база данных создана")
        print("   3. Проверьте права доступа пользователя")
        print("   4. Проверьте настройки PostgreSQL")
    
    if connection_ok and not retry_ok:
        print("\n⚠️  Подключение работает, но retry логика нестабильна")
        print("   Это может указывать на проблемы с сетью или настройками")

if __name__ == "__main__":
    main()
