# 🔧 Исправление ошибки .env файла

## ❌ Проблема
```
ValueError: invalid literal for int() with base 10: 'your_lawyer_telegram_id_here'
```

Эта ошибка возникает, когда в файле `.env` остались значения по умолчанию вместо реальных настроек.

## 🚀 Быстрое исправление

### 1. Остановите бота
```bash
sudo systemctl stop legal-bot
```

### 2. Отредактируйте .env файл
```bash
nano .env
```

### 3. Замените все placeholder'ы на реальные значения:

```env
# Основные настройки бота
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz  # Ваш токен бота
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx  # Ваш ключ OpenRouter

# Настройки для входа в аккаунт юриста
TELEGRAM_API_ID=12345678  # Ваш API ID
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890  # Ваш API Hash
TELEGRAM_PHONE=+79001234567  # Ваш номер телефона

# Включение клиента юриста
LAWYER_CLIENT_ENABLED=true

# ID юриста для проверки кодовых слов (ОБЯЗАТЕЛЬНО число!)
LAWYER_TELEGRAM_ID=123456789  # Замените на реальный ID

# Настройки ЮKassa
YOOKASSA_SHOP_ID=123456  # Ваш Shop ID
YOOKASSA_SECRET_KEY=test_xxxxxxxxxxxxxxxxxxxx  # Ваш Secret Key

# Настройки базы данных
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

### 4. Запустите бота
```bash
sudo systemctl start legal-bot
sudo systemctl status legal-bot
```

## 🔍 Проверка настроек

### Автоматическая проверка
```bash
# Получите обновленный скрипт проверки
git pull origin main
python fix_env.py
```

### Ручная проверка
```bash
# Проверьте, что LAWYER_TELEGRAM_ID - это число
grep LAWYER_TELEGRAM_ID .env

# Проверьте, что нет строк с 'your_'
grep "your_" .env
```

## 📋 Обязательные поля

Убедитесь, что у вас есть все эти значения:

- ✅ `BOT_TOKEN` - от @BotFather
- ✅ `OPENROUTER_API_KEY` - от OpenRouter
- ✅ `TELEGRAM_API_ID` - от my.telegram.org
- ✅ `TELEGRAM_API_HASH` - от my.telegram.org
- ✅ `TELEGRAM_PHONE` - ваш номер телефона
- ✅ `LAWYER_TELEGRAM_ID` - ID юриста (число!)
- ✅ `YOOKASSA_SHOP_ID` - от ЮKassa
- ✅ `YOOKASSA_SECRET_KEY` - от ЮKassa
- ✅ `DATABASE_URL` - строка подключения к PostgreSQL

## 🆘 Если нет значений

### 1. Telegram Bot Token
```bash
# Напишите @BotFather в Telegram
# /newbot
# Следуйте инструкциям
```

### 2. OpenRouter API Key
```bash
# Зайдите на https://openrouter.ai/
# Создайте аккаунт и получите ключ
```

### 3. Telegram API
```bash
# Зайдите на https://my.telegram.org/
# Войдите и получите API_ID и API_HASH
```

### 4. ЮKassa
```bash
# Зайдите на https://yookassa.ru/
# Создайте магазин и получите ключи
```

## 🔧 Альтернативное решение

Если у вас нет всех значений, можете временно отключить функции:

```env
# Отключить клиент юриста
LAWYER_CLIENT_ENABLED=false

# Установить ID юриста в 0
LAWYER_TELEGRAM_ID=0
```

## 📞 Полезные команды

```bash
# Проверить статус
sudo systemctl status legal-bot

# Посмотреть логи
sudo journalctl -u legal-bot -f

# Перезапустить
sudo systemctl restart legal-bot

# Проверить .env файл
cat .env
```

## ⚠️ Важно

- `LAWYER_TELEGRAM_ID` должно быть **числом**, а не строкой
- Все значения должны быть **реальными**, а не placeholder'ами
- Не используйте кавычки вокруг значений в .env файле
