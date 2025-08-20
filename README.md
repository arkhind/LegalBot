# Юридический Telegram Бот

Telegram бот для предоставления юридических консультаций с использованием искусственного интеллекта и возможностью связи с реальными юристами.

## Возможности

- 🤖 Консультации с использованием ИИ
- 👨‍💼 Связь с реальными юристами
- 📋 Помощь в составлении документов
- 📞 Удобный интерфейс с кнопками
- 🔐 Автоматическая регистрация в Telegram при запуске
- 💾 Сохранение сессии для аккаунта юриста
- 💬 Обработка только личных сообщений с кодовым словом

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` в корневой папке проекта:
```
BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
LAWYER_TELEGRAM_ID=your_lawyer_telegram_id_here
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+7XXXXXXXXXX

# Включение клиента юриста (опционально)
LAWYER_CLIENT_ENABLED=true

# ЮKassa настройки (см. YOOKASSA_SETUP.md)
YOOKASSA_SHOP_ID=your_shop_id_here
YOOKASSA_SECRET_KEY=your_secret_key_here
```

3. Получите токены:
   - **BOT_TOKEN**: Создайте бота через @BotFather в Telegram
   - **OPENROUTER_API_KEY**: Получите API ключ на [OpenRouter](https://openrouter.ai/keys)
   - **LAWYER_TELEGRAM_ID**: Telegram ID юриста (получите через @userinfobot)
   - **TELEGRAM_API_ID** и **TELEGRAM_API_HASH**: Получите на [my.telegram.org](https://my.telegram.org) (см. TELEGRAM_SESSION_SETUP.md)
   - **TELEGRAM_PHONE**: Номер телефона аккаунта юриста в международном формате
   - **YOOKASSA_SHOP_ID** и **YOOKASSA_SECRET_KEY**: Получите в личном кабинете ЮKassa (см. YOOKASSA_SETUP.md)

## Запуск

### Основной бот:
```bash
python main.py
```

При первом запуске система автоматически запросит авторизацию в Telegram для аккаунта юриста.

### Проверка настроек:
```bash
python check_env.py
```

### Тестирование сессии:
```bash
python test_session.py
```

### Мониторинг сообщений (автоматическая проверка кодовых слов):
```bash
python message_monitor.py
```

### Запуск всех компонентов одновременно:
```bash
python start_all.py
```

**Примечание**: Для работы клиента юриста необходимо настроить Telegram API (см. TELEGRAM_SESSION_SETUP.md)

## Использование

1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Выберите тип консультации из предложенных вариантов

## Структура проекта

```
Юр бот/
├── main.py                    # Основной файл бота
├── check_env.py              # Проверка переменных окружения
├── test_session.py           # Тестирование сессии Telegram
├── message_monitor.py         # Мониторинг сообщений через Client API
├── start_all.py              # Скрипт запуска всех компонентов
├── payment_handler.py         # Обработка платежей через ЮKassa
├── requirements.txt           # Зависимости
├── README.md                 # Документация
├── TELEGRAM_SESSION_SETUP.md # Настройка автоматической регистрации
├── YOOKASSA_SETUP.md         # Настройка ЮKassa
└── .env                      # Переменные окружения (создать самостоятельно)
```

## Логирование

Бот ведет логи в файл `bot.log` с ротацией каждый день и хранением за 7 дней. 