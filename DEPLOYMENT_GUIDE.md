# Руководство по деплою проекта на сервер

## 📋 Подготовка к деплою

### 1. Локальная подготовка

```bash
# Создаем архив проекта
chmod +x deploy.sh
./deploy.sh
```

### 2. Необходимые файлы для сервера

- `legal_bot.tar.gz` - архив проекта
- `.env` - файл с переменными окружения (создать отдельно)

## 🖥️ Настройка сервера

### 1. Подключение к серверу

```bash
ssh user@your-server-ip
```

### 2. Установка Python и зависимостей

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Python 3.9+
sudo apt install python3 python3-pip python3-venv -y

# Устанавливаем PostgreSQL (если нужна база данных)
sudo apt install postgresql postgresql-contrib -y
```

### 3. Создание директории проекта

```bash
mkdir -p /home/user/legal_bot
cd /home/user/legal_bot
```

## 📦 Загрузка проекта

### 1. Загрузка архива

```bash
# С локального компьютера
scp legal_bot.tar.gz user@your-server-ip:/home/user/legal_bot/
```

### 2. Распаковка проекта

```bash
cd /home/user/legal_bot
tar -xzf legal_bot.tar.gz
```

### 3. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Установка зависимостей

```bash
pip install -r requirements.txt
```

## ⚙️ Настройка конфигурации

### 1. Создание .env файла

```bash
nano .env
```

Содержимое .env:
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

# Настройки базы данных
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

### 2. Настройка базы данных (если используется)

```bash
# Создание базы данных
sudo -u postgres createdb legal_bot_db

# Создание пользователя
sudo -u postgres createuser legal_bot_user

# Установка пароля
sudo -u postgres psql -c "ALTER USER legal_bot_user PASSWORD 'your_password';"

# Предоставление прав
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE legal_bot_db TO legal_bot_user;"
```

## 🚀 Запуск бота

### 1. Тестовый запуск

```bash
# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем бота
python main.py
```

### 2. Настройка автозапуска с systemd

Создаем сервис:
```bash
sudo nano /etc/systemd/system/legal-bot.service
```

Содержимое сервиса:
```ini
[Unit]
Description=Legal Bot Telegram
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/user/legal_bot
Environment=PATH=/home/user/legal_bot/venv/bin
ExecStart=/home/user/legal_bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активируем сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable legal-bot
sudo systemctl start legal-bot
```

### 3. Проверка статуса

```bash
sudo systemctl status legal-bot
sudo journalctl -u legal-bot -f
```

## 🔧 Полезные команды

### Управление сервисом
```bash
# Остановить бота
sudo systemctl stop legal-bot

# Перезапустить бота
sudo systemctl restart legal-bot

# Посмотреть логи
sudo journalctl -u legal-bot -f

# Проверить статус
sudo systemctl status legal-bot
```

### Обновление бота
```bash
# Остановить сервис
sudo systemctl stop legal-bot

# Загрузить новый архив
scp legal_bot.tar.gz user@your-server-ip:/home/user/legal_bot/

# Распаковать
cd /home/user/legal_bot
tar -xzf legal_bot.tar.gz

# Перезапустить
sudo systemctl start legal-bot
```

## 🔒 Безопасность

### 1. Настройка файрвола
```bash
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. Настройка SSL (если нужно)
```bash
sudo apt install certbot
sudo certbot --nginx
```

## 📊 Мониторинг

### 1. Проверка логов
```bash
# Логи systemd
sudo journalctl -u legal-bot -f

# Логи приложения
tail -f /home/user/legal_bot/bot.log
```

### 2. Мониторинг ресурсов
```bash
# Использование памяти
htop

# Дисковое пространство
df -h

# Процессы Python
ps aux | grep python
```

## 🆘 Устранение проблем

### 1. Бот не запускается
```bash
# Проверить логи
sudo journalctl -u legal-bot -f

# Проверить права доступа
ls -la /home/user/legal_bot/

# Проверить виртуальное окружение
source venv/bin/activate
python --version
```

### 2. Проблемы с базой данных
```bash
# Проверить подключение
sudo -u postgres psql -d legal_bot_db

# Проверить права пользователя
sudo -u postgres psql -c "\du"
```

### 3. Проблемы с Telegram API
```bash
# Проверить переменные окружения
cat .env

# Тестировать подключение
python test_session.py
```
