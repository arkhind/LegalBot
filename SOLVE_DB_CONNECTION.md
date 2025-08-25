# 🔧 Решение проблемы "SSL connection has been closed unexpectedly"

## ❌ Проблема
```
SSL connection has been closed unexpectedly
```

Эта ошибка возникает из-за нестабильного подключения к PostgreSQL.

## 🚀 Быстрое решение

### 1. Получите обновления
```bash
cd /home/root/projects/LegalBot
git pull origin main
```

### 2. Запустите диагностику
```bash
python diagnose_db.py
```

### 3. Проверьте настройки .env
```bash
python fix_env.py
```

### 4. Перезапустите бота
```bash
sudo systemctl restart legal-bot
sudo systemctl status legal-bot
```

## 🔍 Подробная диагностика

### Проверка PostgreSQL
```bash
# Статус PostgreSQL
sudo systemctl status postgresql

# Если не запущен
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Проверка подключения
```bash
# Тест подключения
python test_database.py

# Диагностика
python diagnose_db.py
```

### Проверка настроек PostgreSQL
```bash
# Подключитесь к PostgreSQL
sudo -u postgres psql

# Проверьте настройки
SHOW max_connections;
SHOW tcp_keepalives_idle;
SHOW tcp_keepalives_interval;
SHOW tcp_keepalives_count;

# Выйдите
\q
```

## ⚙️ Настройка PostgreSQL

### 1. Отредактируйте конфигурацию
```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```

### 2. Добавьте/измените настройки
```conf
# Таймауты соединений
tcp_keepalives_idle = 30
tcp_keepalives_interval = 10
tcp_keepalives_count = 5

# Максимальное количество соединений
max_connections = 100

# Таймаут неактивных соединений
idle_in_transaction_session_timeout = 300000

# Таймаут подключения
connect_timeout = 10
```

### 3. Перезапустите PostgreSQL
```bash
sudo systemctl restart postgresql
```

## 🔧 Альтернативные решения

### Решение 1: Использование пула соединений
```bash
# Установите pgBouncer
sudo apt install pgbouncer

# Настройте pgBouncer
sudo nano /etc/pgbouncer/pgbouncer.ini
```

### Решение 2: Увеличение лимитов
```bash
# Проверьте лимиты системы
ulimit -n

# Увеличьте лимиты в /etc/security/limits.conf
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
```

### Решение 3: Настройка SSL
```bash
# Отключите SSL для локальных подключений
sudo nano /etc/postgresql/*/main/postgresql.conf

# Добавьте:
ssl = off
```

## 📊 Мониторинг

### Проверка активных соединений
```sql
-- Подключитесь к PostgreSQL
sudo -u postgres psql

-- Проверьте активные соединения
SELECT pid, usename, application_name, client_addr, state, query_start 
FROM pg_stat_activity 
WHERE state = 'active';

-- Проверьте количество соединений по пользователям
SELECT usename, count(*) 
FROM pg_stat_activity 
GROUP BY usename;
```

### Логи PostgreSQL
```bash
# Просмотр логов
sudo tail -f /var/log/postgresql/postgresql-*.log

# Поиск ошибок
sudo grep -i "connection" /var/log/postgresql/postgresql-*.log
```

## 🆘 Если ничего не помогает

### 1. Пересоздайте базу данных
```bash
# Остановите бота
sudo systemctl stop legal-bot

# Удалите базу данных
sudo -u postgres dropdb legal_bot

# Создайте заново
sudo -u postgres createdb legal_bot

# Запустите бота
sudo systemctl start legal-bot
```

### 2. Используйте SQLite (временное решение)
```bash
# Измените .env файл
DATABASE_URL=sqlite:///legal_bot.db
```

### 3. Отключите базу данных (временное решение)
```bash
# Закомментируйте все вызовы базы данных в main.py
# Это временное решение для тестирования
```

## 📋 Чек-лист решения

- [ ] Получены обновления кода
- [ ] Запущена диагностика
- [ ] Проверены настройки .env
- [ ] Проверен статус PostgreSQL
- [ ] Настроены параметры PostgreSQL
- [ ] Перезапущен PostgreSQL
- [ ] Перезапущен бот
- [ ] Проверены логи
- [ ] Протестировано подключение

## 📞 Полезные команды

```bash
# Статус всех сервисов
sudo systemctl status legal-bot postgresql

# Логи бота
sudo journalctl -u legal-bot -f

# Логи PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log

# Тест подключения
python test_database.py

# Диагностика
python diagnose_db.py
```

## ⚠️ Важно

1. **Проблема решена в коде** - добавлена retry логика
2. **Проверьте настройки PostgreSQL** - особенно таймауты
3. **Мониторьте логи** - для выявления паттернов
4. **Рассмотрите пул соединений** - для высоконагруженных систем
