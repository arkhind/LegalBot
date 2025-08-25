# 🚀 Деплой проекта с GitHub на сервер

## 📋 Подготовка

### 1. Убедитесь, что у вас есть:
- Доступ к серверу (SSH)
- URL репозитория на GitHub
- Все необходимые токены и ключи API

### 2. Подготовьте переменные окружения
Создайте файл `.env` с вашими настройками (см. `env.example`)

## 🖥️ Настройка сервера

### 1. Подключение к серверу
```bash
ssh username@your-server-ip
```

### 2. Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Установка необходимых пакетов
```bash
# Python и инструменты разработки
sudo apt install python3 python3-pip python3-venv git curl -y

# PostgreSQL (если используется)
sudo apt install postgresql postgresql-contrib -y

# Дополнительные инструменты
sudo apt install htop nano screen -y
```

## 📥 Клонирование с GitHub

### 1. Создание директории проекта
```bash
mkdir -p /home/username/projects
cd /home/username/projects
```

### 2. Клонирование репозитория
```bash
# Замените на ваш URL репозитория
git clone https://github.com/your-username/LegalBot.git
cd LegalBot
```

### 3. Проверка клонирования
```bash
ls -la
cat README.md
```

## ⚙️ Настройка проекта

### 1. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Установка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Создание файла конфигурации
```bash
# Копируем пример конфигурации
cp env.example .env

# Редактируем конфигурацию
nano .env
```

### 4. Настройка .env файла
```env
# Основные настройки бота
BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Настройки для входа в аккаунт юриста
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+7XXXXXXXXXX

# Включение клиента юриста
LAWYER_CLIENT_ENABLED=true

# ID юриста для проверки кодовых слов
LAWYER_TELEGRAM_ID=your_lawyer_telegram_id_here

# Настройки ЮKassa
YOOKASSA_SHOP_ID=your_shop_id_here
YOOKASSA_SECRET_KEY=your_secret_key_here

# Настройки базы данных (выберите один способ)
# Способ 1: DATABASE_URL (рекомендуется)
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Способ 2: Отдельные переменные
# PGHOST=localhost
# PGDATABASE=legal_bot
# PGUSER=legal_bot_user
# PGPASSWORD=your_password
# PGSSLMODE=require
# PGCHANNELBINDING=prefer
```

## 🗄️ Настройка базы данных (если используется)

### 1. Создание базы данных PostgreSQL
```bash
# Подключение к PostgreSQL
sudo -u postgres psql

# Создание базы данных и пользователя
CREATE DATABASE legal_bot;
CREATE USER legal_bot_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE legal_bot TO legal_bot_user;
\q
```

### 2. Тестирование подключения к базе данных
```bash
# Активируем виртуальное окружение
source venv/bin/activate

# Тестируем подключение
python test_database.py
```

## 🧪 Тестирование

### 1. Проверка конфигурации
```bash
# Проверяем переменные окружения
python check_env.py
```

### 2. Тестовый запуск
```bash
# Запускаем бота в тестовом режиме
python main.py
```

### 3. Проверка логов
```bash
# В другом терминале
tail -f bot.log
```

## 🚀 Настройка автозапуска

### 1. Создание systemd сервиса
```bash
sudo nano /etc/systemd/system/legal-bot.service
```

### 2. Содержимое сервиса
```ini
[Unit]
Description=Legal Bot Telegram
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=username
Group=username
WorkingDirectory=/home/username/projects/LegalBot
Environment=PATH=/home/username/projects/LegalBot/venv/bin
ExecStart=/home/username/projects/LegalBot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Переменные окружения
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### 3. Активация сервиса
```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable legal-bot

# Запуск сервиса
sudo systemctl start legal-bot

# Проверка статуса
sudo systemctl status legal-bot
```

## 📊 Мониторинг и управление

### 1. Просмотр логов
```bash
# Логи systemd
sudo journalctl -u legal-bot -f

# Логи приложения
tail -f /home/username/projects/LegalBot/bot.log
```

### 2. Управление сервисом
```bash
# Остановить бота
sudo systemctl stop legal-bot

# Перезапустить бота
sudo systemctl restart legal-bot

# Проверить статус
sudo systemctl status legal-bot
```

### 3. Мониторинг ресурсов
```bash
# Использование памяти и CPU
htop

# Дисковое пространство
df -h

# Процессы Python
ps aux | grep python
```

## 🔄 Обновление с GitHub

### 1. Автоматическое обновление
```bash
# Переходим в директорию проекта
cd /home/username/projects/LegalBot

# Останавливаем сервис
sudo systemctl stop legal-bot

# Получаем обновления
git pull origin main

# Обновляем зависимости (если изменились)
source venv/bin/activate
pip install -r requirements.txt

# Запускаем сервис
sudo systemctl start legal-bot
```

### 2. Скрипт для автоматического обновления
```bash
# Создаем скрипт обновления
nano update_bot.sh
```

Содержимое `update_bot.sh`:
```bash
#!/bin/bash
echo "🔄 Обновление LegalBot..."

cd /home/username/projects/LegalBot

# Останавливаем бота
sudo systemctl stop legal-bot

# Получаем обновления
git pull origin main

# Обновляем зависимости
source venv/bin/activate
pip install -r requirements.txt

# Запускаем бота
sudo systemctl start legal-bot

echo "✅ Обновление завершено!"
sudo systemctl status legal-bot
```

```bash
# Делаем скрипт исполняемым
chmod +x update_bot.sh
```

## 🔒 Безопасность

### 1. Настройка файрвола
```bash
# Установка UFW
sudo apt install ufw -y

# Настройка правил
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Включение файрвола
sudo ufw enable
```

### 2. Защита файлов
```bash
# Устанавливаем правильные права
chmod 600 .env
chmod 700 /home/username/projects/LegalBot
```

### 3. Регулярные обновления
```bash
# Создаем задачу для автоматических обновлений
crontab -e

# Добавляем строку для ежедневного обновления системы
0 2 * * * sudo apt update && sudo apt upgrade -y
```

## 🆘 Устранение проблем

### 1. Бот не запускается
```bash
# Проверяем логи
sudo journalctl -u legal-bot -f

# Проверяем права доступа
ls -la /home/username/projects/LegalBot/

# Проверяем виртуальное окружение
source venv/bin/activate
python --version
```

### 2. Проблемы с базой данных
```bash
# Тестируем подключение
python test_database.py

# Проверяем статус PostgreSQL
sudo systemctl status postgresql
```

### 3. Проблемы с Git
```bash
# Проверяем статус репозитория
git status

# Сбрасываем изменения (если нужно)
git reset --hard HEAD
git pull origin main
```

### 4. Проблемы с правами
```bash
# Исправляем права владельца
sudo chown -R username:username /home/username/projects/LegalBot

# Исправляем права файлов
chmod 600 .env
chmod +x main.py
```

## 📞 Полезные команды

### Быстрые проверки
```bash
# Статус всех сервисов
sudo systemctl status legal-bot postgresql

# Последние логи
sudo journalctl -u legal-bot -n 50

# Использование диска
du -sh /home/username/projects/LegalBot

# Проверка процессов
ps aux | grep -E "(python|legal-bot)"
```

### Резервное копирование
```bash
# Создание бэкапа
tar -czf legal_bot_backup_$(date +%Y%m%d).tar.gz /home/username/projects/LegalBot

# Восстановление из бэкапа
tar -xzf legal_bot_backup_20241201.tar.gz -C /
```

## 🎯 Чек-лист деплоя

- [ ] Сервер настроен и обновлен
- [ ] Git установлен и настроен
- [ ] Репозиторий склонирован
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] .env файл настроен
- [ ] База данных настроена (если используется)
- [ ] Тестовый запуск прошел успешно
- [ ] Systemd сервис создан и активирован
- [ ] Автозапуск работает
- [ ] Логи проверены
- [ ] Безопасность настроена

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u legal-bot -f`
2. Убедитесь в корректности .env файла
3. Проверьте подключение к интернету
4. Обратитесь в поддержку с логами ошибок
