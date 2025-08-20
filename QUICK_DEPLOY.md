# 🚀 Быстрая загрузка проекта на сервер

## 📦 Шаг 1: Подготовка архива (уже готово)

Архив `legal_bot.tar.gz` (42KB) уже создан и готов к загрузке.

## 📤 Шаг 2: Загрузка на сервер

### Вариант A: Через SCP (рекомендуется)
```bash
# Замените на ваши данные
scp legal_bot.tar.gz username@your-server-ip:/home/username/legal_bot/
```

### Вариант B: Через SFTP
```bash
# Подключитесь к серверу
sftp username@your-server-ip

# Загрузите файл
put legal_bot.tar.gz /home/username/legal_bot/
```

### Вариант C: Через веб-интерфейс
1. Зайдите в панель управления сервером
2. Найдите файловый менеджер
3. Загрузите `legal_bot.tar.gz`

## 🖥️ Шаг 3: Настройка сервера

### Подключение к серверу
```bash
ssh username@your-server-ip
```

### Установка Python (если не установлен)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

### Создание директории и распаковка
```bash
mkdir -p /home/username/legal_bot
cd /home/username/legal_bot
tar -xzf legal_bot.tar.gz
```

### Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate
```

### Установка зависимостей
```bash
pip install -r requirements.txt
```

## ⚙️ Шаг 4: Настройка конфигурации

### Создание .env файла
```bash
nano .env
```

### Содержимое .env (замените на ваши данные):
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

# Настройки базы данных (если используется)
PGHOST=localhost
PGDATABASE=legal_bot
PGUSER=legal_bot_user
PGPASSWORD=your_password_here
PGSSLMODE=require
PGCHANNELBINDING=prefer
```

## 🚀 Шаг 5: Запуск бота

### Тестовый запуск
```bash
python main.py
```

### Запуск в фоне
```bash
nohup python main.py > bot.log 2>&1 &
```

### Проверка работы
```bash
tail -f bot.log
```

## 🔧 Шаг 6: Настройка автозапуска (опционально)

### Создание systemd сервиса
```bash
sudo nano /etc/systemd/system/legal-bot.service
```

### Содержимое сервиса:
```ini
[Unit]
Description=Legal Bot Telegram
After=network.target

[Service]
Type=simple
User=username
WorkingDirectory=/home/username/legal_bot
Environment=PATH=/home/username/legal_bot/venv/bin
ExecStart=/home/username/legal_bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Активация сервиса
```bash
sudo systemctl daemon-reload
sudo systemctl enable legal-bot
sudo systemctl start legal-bot
sudo systemctl status legal-bot
```

## 📋 Проверка работы

1. **Проверьте логи**: `tail -f bot.log`
2. **Проверьте бота**: отправьте `/start` в Telegram
3. **Проверьте статус**: `sudo systemctl status legal-bot`

## 🆘 Устранение проблем

### Бот не запускается
```bash
# Проверьте логи
tail -f bot.log

# Проверьте .env файл
cat .env

# Проверьте зависимости
pip list
```

### Проблемы с правами
```bash
# Установите правильные права
chmod 600 .env
chmod +x main.py
```

### Проблемы с базой данных
```bash
# Проверьте подключение
python -c "from database import Database; db = Database(); print('DB OK')"
```

## 📞 Поддержка

При проблемах:
- Проверьте логи: `tail -f bot.log`
- Убедитесь в корректности .env файла
- Проверьте подключение к интернету
- Обратитесь в поддержку: @narhipovd
