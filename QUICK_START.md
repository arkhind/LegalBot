# 🚀 Быстрый старт

## 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

## 2. Настройка .env файла
```env
BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
LAWYER_TELEGRAM_ID=your_lawyer_telegram_id_here
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
LAWYER_PHONE=89895202224
```

## 3. Получение API ключей

### Для основного бота:
- **BOT_TOKEN**: @BotFather → /newbot
- **OPENROUTER_API_KEY**: https://openrouter.ai/keys

### Для мониторинга сообщений:
- **TELEGRAM_API_ID** и **TELEGRAM_API_HASH**: https://my.telegram.org
- Подробная инструкция: [TELEGRAM_CLIENT_SETUP.md](TELEGRAM_CLIENT_SETUP.md)

## 4. Запуск системы

### Вариант 1: Все компоненты сразу
```bash
python start_all.py
```

### Вариант 2: По отдельности
```bash
# Основной бот
python main.py

# В другом терминале - мониторинг сообщений
python message_monitor.py
```

## 5. Первый запуск мониторинга

При первом запуске `message_monitor.py`:
1. Введите номер телефона: `89895202224`
2. Введите код из SMS
3. При необходимости - пароль двухфакторной аутентификации

## ✅ Готово!

Теперь система:
- 🤖 Отвечает на вопросы через ИИ
- 💳 Обрабатывает платежи
- 🔍 Автоматически проверяет кодовые слова в сообщениях юристу
- 📊 Ведет логи всех операций

## 📞 Тестирование

1. Найдите бота в Telegram
2. Отправьте `/start`
3. Выберите консультацию и оплатите
4. Получите кодовое слово "ЮРИСТ2024"
5. Напишите юристу: "Мой ID 123456789, код ЮРИСТ2024"
6. Система автоматически проверит и ответит
