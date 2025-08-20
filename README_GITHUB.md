# Юридический Telegram Бот

Telegram бот для предоставления юридических консультаций с использованием искусственного интеллекта и возможностью связи с реальными юристами.

## 🚀 Возможности

- 🤖 Консультации с использованием ИИ (Gemini 2.0 Flash Lite)
- 👨‍💼 Связь с реальными юристами
- 💳 Интеграция с ЮKassa для приема платежей
- 🔐 Автоматическая регистрация в Telegram
- 💬 Обработка только личных сообщений с кодовым словом
- 📊 Статистика пользователей и консультаций

## 📋 Требования

- Python 3.9+
- PostgreSQL (опционально)
- Telegram Bot API
- OpenRouter API (для Gemini)
- ЮKassa (для платежей)

## 🛠️ Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/legal-bot.git
cd legal-bot
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
Создайте файл `.env` в корневой папке:
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

### 4. Настройка базы данных
```bash
# Создание таблиц (если используется PostgreSQL)
python database.py
```

### 5. Запуск бота
```bash
python main.py
```

## 🔧 Настройка

### Получение API ключей

1. **Telegram Bot Token**: Создайте бота через @BotFather
2. **OpenRouter API Key**: Получите на [openrouter.ai](https://openrouter.ai/keys)
3. **Telegram API ID/Hash**: Получите на [my.telegram.org](https://my.telegram.org)
4. **ЮKassa**: Настройте в личном кабинете ЮKassa

### Первый запуск

При первом запуске система автоматически запросит авторизацию в Telegram для аккаунта юриста. Введите код подтверждения из Telegram.

## 📁 Структура проекта

```
legal-bot/
├── main.py                    # Основной файл бота
├── payment_handler.py         # Обработка платежей
├── database.py               # Работа с базой данных
├── telegram_login.py         # Авторизация в Telegram
├── lawyer_client.py          # Клиент юриста
├── texts/                    # Текстовые файлы
├── prompts/                  # Промпты для ИИ
├── requirements.txt          # Зависимости
└── README.md                # Документация
```

## 🚀 Деплой на сервер

См. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) для подробных инструкций по деплою на сервер.

## 🔒 Безопасность

- Все конфиденциальные данные хранятся в `.env` файле
- Сессии Telegram исключены из репозитория
- Логи и временные файлы не загружаются в Git

## 📝 Лицензия

Этот проект предназначен для личного использования. Пожалуйста, не используйте для коммерческих целей без разрешения.

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📞 Поддержка

По вопросам обращайтесь к разработчику или создавайте Issues в репозитории.

## ⚠️ Важно

- Не загружайте `.env` файл в репозиторий
- Не публикуйте сессии Telegram
- Храните API ключи в безопасности
- Соблюдайте условия использования Telegram API
