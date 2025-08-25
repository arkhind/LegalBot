#!/bin/bash
# Скрипт для автоматического деплоя LegalBot с GitHub

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка аргументов
if [ $# -eq 0 ]; then
    print_error "Использование: $0 <github-repo-url> [username] [project-dir]"
    echo "Пример: $0 https://github.com/username/LegalBot.git myuser /home/myuser/projects"
    exit 1
fi

GITHUB_URL=$1
USERNAME=${2:-$USER}
PROJECT_DIR=${3:-"/home/$USERNAME/projects"}

print_info "🚀 Начинаем деплой LegalBot с GitHub"
print_info "Репозиторий: $GITHUB_URL"
print_info "Пользователь: $USERNAME"
print_info "Директория: $PROJECT_DIR"

# Проверка прав sudo
if ! sudo -n true 2>/dev/null; then
    print_warning "Требуются права sudo. Введите пароль:"
    sudo true
fi

# Обновление системы
print_info "📦 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
print_info "🔧 Установка необходимых пакетов..."
sudo apt install python3 python3-pip python3-venv git curl htop nano screen -y

# Установка PostgreSQL (если не установлен)
if ! command -v psql &> /dev/null; then
    print_info "🗄️  Установка PostgreSQL..."
    sudo apt install postgresql postgresql-contrib -y
    sudo systemctl enable postgresql
    sudo systemctl start postgresql
fi

# Создание директории проекта
print_info "📁 Создание директории проекта..."
sudo mkdir -p "$PROJECT_DIR"
sudo chown "$USERNAME:$USERNAME" "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Клонирование репозитория
print_info "📥 Клонирование репозитория..."
if [ -d "LegalBot" ]; then
    print_warning "Директория LegalBot уже существует. Обновляем..."
    cd LegalBot
    git pull origin main
else
    git clone "$GITHUB_URL" LegalBot
    cd LegalBot
fi

# Создание виртуального окружения
print_info "🐍 Создание виртуального окружения..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Установка зависимостей
print_info "📦 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание .env файла
print_info "⚙️  Настройка конфигурации..."
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        cp env.example .env
        print_warning "Создан файл .env из env.example"
        print_warning "Не забудьте отредактировать .env файл с вашими настройками!"
    else
        print_error "Файл env.example не найден!"
        exit 1
    fi
else
    print_info "Файл .env уже существует"
fi

# Настройка прав доступа
print_info "🔒 Настройка прав доступа..."
sudo chown -R "$USERNAME:$USERNAME" "$PROJECT_DIR/LegalBot"
chmod 600 .env
chmod +x main.py

# Тестирование базы данных
print_info "🧪 Тестирование базы данных..."
if python test_database.py; then
    print_success "Тест базы данных прошел успешно"
else
    print_warning "Тест базы данных не прошел. Проверьте настройки в .env"
fi

# Создание systemd сервиса
print_info "🚀 Создание systemd сервиса..."
sudo tee /etc/systemd/system/legal-bot.service > /dev/null <<EOF
[Unit]
Description=Legal Bot Telegram
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$PROJECT_DIR/LegalBot
Environment=PATH=$PROJECT_DIR/LegalBot/venv/bin
ExecStart=$PROJECT_DIR/LegalBot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Активация сервиса
print_info "🔧 Активация сервиса..."
sudo systemctl daemon-reload
sudo systemctl enable legal-bot

# Создание скрипта обновления
print_info "📝 Создание скрипта обновления..."
tee update_bot.sh > /dev/null <<EOF
#!/bin/bash
echo "🔄 Обновление LegalBot..."

cd $PROJECT_DIR/LegalBot

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
EOF

chmod +x update_bot.sh

# Настройка файрвола
print_info "🔥 Настройка файрвола..."
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

print_success "🎉 Деплой завершен успешно!"

echo ""
print_info "📋 Следующие шаги:"
echo "1. Отредактируйте файл .env с вашими настройками:"
echo "   nano $PROJECT_DIR/LegalBot/.env"
echo ""
echo "2. Запустите бота:"
echo "   sudo systemctl start legal-bot"
echo ""
echo "3. Проверьте статус:"
echo "   sudo systemctl status legal-bot"
echo ""
echo "4. Посмотрите логи:"
echo "   sudo journalctl -u legal-bot -f"
echo ""
echo "5. Для обновления используйте:"
echo "   ./update_bot.sh"
echo ""
print_warning "⚠️  Не забудьте настроить .env файл перед запуском!"
