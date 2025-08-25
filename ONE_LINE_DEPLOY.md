# 🚀 Деплой одной командой

## ⚡ Самый быстрый способ

### 1. Выполните эту команду на сервере:

```bash
curl -s https://raw.githubusercontent.com/arkhind/LegalBot/main/deploy_from_github.sh | bash -s https://github.com/arkhind/LegalBot.git
```

### 2. Настройте .env файл:
```bash
nano .env
```

### 3. Запустите бота:
```bash
sudo systemctl start legal-bot
sudo systemctl status legal-bot
```

## 🔧 Альтернативный способ (если curl не работает)

### 1. Клонируйте репозиторий:
```bash
git clone https://github.com/arkhind/LegalBot.git
cd LegalBot
```

### 2. Запустите скрипт деплоя:
```bash
chmod +x deploy_from_github.sh
./deploy_from_github.sh https://github.com/arkhind/LegalBot.git
```

### 3. Настройте и запустите:
```bash
nano .env
sudo systemctl start legal-bot
```

## 📋 Что происходит автоматически:

- ✅ Обновление системы
- ✅ Установка Python, Git, PostgreSQL
- ✅ Клонирование репозитория
- ✅ Создание виртуального окружения
- ✅ Установка зависимостей
- ✅ Создание .env файла
- ✅ Настройка systemd сервиса
- ✅ Настройка файрвола

## 🆘 Полезные команды:

```bash
# Статус бота
sudo systemctl status legal-bot

# Логи
sudo journalctl -u legal-bot -f

# Перезапуск
sudo systemctl restart legal-bot

# Обновление
cd LegalBot && git pull origin main && sudo systemctl restart legal-bot
```

## ⚠️ Важно:

Не забудьте отредактировать `.env` файл с вашими настройками перед запуском бота!
