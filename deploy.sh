#!/bin/bash
# Скрипт для деплоя проекта на сервер

echo "🚀 Начинаем деплой проекта..."

# Создаем архив проекта (исключаем ненужные файлы)
echo "📦 Создаем архив проекта..."
tar -czf legal_bot.tar.gz \
    --exclude='*.log' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.env' \
    --exclude='*.session' \
    --exclude='*.txt' \
    --exclude='veretenov_session.txt' \
    --exclude='lawyer_data.json' \
    --exclude='.git' \
    --exclude='.DS_Store' \
    .

echo "✅ Архив создан: legal_bot.tar.gz"
echo ""
echo "📋 Следующие шаги:"
echo "1. Загрузите архив на сервер:"
echo "   scp legal_bot.tar.gz user@your-server:/path/to/project/"
echo ""
echo "2. Подключитесь к серверу:"
echo "   ssh user@your-server"
echo ""
echo "3. Распакуйте архив:"
echo "   cd /path/to/project/"
echo "   tar -xzf legal_bot.tar.gz"
echo ""
echo "4. Создайте .env файл с настройками"
echo "5. Установите зависимости: pip install -r requirements.txt"
echo "6. Запустите бота: python main.py"
