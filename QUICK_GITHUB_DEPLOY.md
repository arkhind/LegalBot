# 🚀 Быстрый деплой с GitHub

## ⚡ Автоматический деплой (рекомендуется)

### 1. Загрузите скрипт на сервер
```bash
# Скачайте скрипт на сервер
wget https://raw.githubusercontent.com/your-username/LegalBot/main/deploy_from_github.sh
chmod +x deploy_from_github.sh
```

### 2. Запустите автоматический деплой
```bash
# Замените на ваш URL репозитория
./deploy_from_github.sh https://github.com/your-username/LegalBot.git
```

### 3. Настройте .env файл
```bash
nano .env
```

### 4. Запустите бота
```bash
sudo systemctl start legal-bot
sudo systemctl status legal-bot
```

## 🔧 Ручной деплой

### 1. Подключение к серверу
```bash
ssh username@your-server-ip
```

### 2. Клонирование репозитория
```bash
git clone https://github.com/your-username/LegalBot.git
cd LegalBot
```

### 3. Настройка окружения
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env
nano .env
```

### 4. Создание сервиса
```bash
sudo nano /etc/systemd/system/legal-bot.service
```

Содержимое:
```ini
[Unit]
Description=Legal Bot Telegram
After=network.target

[Service]
Type=simple
User=username
WorkingDirectory=/home/username/LegalBot
Environment=PATH=/home/username/LegalBot/venv/bin
ExecStart=/home/username/LegalBot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5. Запуск
```bash
sudo systemctl daemon-reload
sudo systemctl enable legal-bot
sudo systemctl start legal-bot
```

## 📋 Чек-лист

- [ ] Репозиторий склонирован
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] .env файл настроен
- [ ] База данных настроена
- [ ] Сервис создан и запущен
- [ ] Бот отвечает в Telegram

## 🆘 Полезные команды

```bash
# Статус бота
sudo systemctl status legal-bot

# Логи бота
sudo journalctl -u legal-bot -f

# Перезапуск
sudo systemctl restart legal-bot

# Обновление
git pull origin main
sudo systemctl restart legal-bot
```

## 📞 Поддержка

При проблемах проверьте:
1. Логи: `sudo journalctl -u legal-bot -f`
2. .env файл: `cat .env`
3. Статус: `sudo systemctl status legal-bot`
