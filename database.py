import os
import psycopg2
from psycopg2.extras import RealDictCursor
from loguru import logger
from datetime import datetime
from typing import Optional, Dict, List
import time


class Database:
    def __init__(self):
        self.connection = None
        self.max_retries = 3
        self.retry_delay = 2
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Подключение к базе данных с retry логикой"""
        for attempt in range(self.max_retries):
            try:
                # Сначала пробуем использовать DATABASE_URL
                database_url = os.getenv('DATABASE_URL')
                if database_url:
                    self.connection = psycopg2.connect(
                        database_url,
                        # Дополнительные параметры для стабильности
                        keepalives_idle=30,
                        keepalives_interval=10,
                        keepalives_count=5,
                        connect_timeout=10
                    )
                else:
                    # Если DATABASE_URL нет, используем отдельные переменные
                    self.connection = psycopg2.connect(
                        host=os.getenv('PGHOST'),
                        database=os.getenv('PGDATABASE'),
                        user=os.getenv('PGUSER'),
                        password=os.getenv('PGPASSWORD'),
                        sslmode=os.getenv('PGSSLMODE'),
                        channel_binding=os.getenv('PGCHANNELBINDING'),
                        # Дополнительные параметры для стабильности
                        keepalives_idle=30,
                        keepalives_interval=10,
                        keepalives_count=5,
                        connect_timeout=10
                    )
                logger.info("✅ Подключение к базе данных установлено")
                return
            except Exception as e:
                logger.warning(f"⚠️ Попытка подключения {attempt + 1}/{self.max_retries} не удалась: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"❌ Ошибка подключения к базе данных после {self.max_retries} попыток: {e}")
                    self.connection = None
    
    def ensure_connection(self):
        """Проверяет и восстанавливает соединение с базой данных"""
        try:
            if self.connection is None or self.connection.closed:
                logger.info("🔄 Восстановление соединения с базой данных...")
                self.connect()
                if self.connection and not self.connection.closed:
                    return True
                else:
                    return False
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка проверки соединения: {e}")
            return False
    
    def execute_with_retry(self, operation, *args, **kwargs):
        """Выполняет операцию с автоматическим retry при ошибках подключения"""
        for attempt in range(self.max_retries):
            try:
                if not self.ensure_connection():
                    raise Exception("Не удалось установить соединение с базой данных")
                
                return operation(*args, **kwargs)
                
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                logger.warning(f"⚠️ Ошибка подключения (попытка {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    # Закрываем соединение и пробуем переподключиться
                    if self.connection:
                        try:
                            self.connection.close()
                        except:
                            pass
                    self.connection = None
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"❌ Операция не удалась после {self.max_retries} попыток: {e}")
                    raise
            except Exception as e:
                logger.error(f"❌ Ошибка выполнения операции: {e}")
                raise
    
    def create_tables(self):
        """Создание таблиц"""
        if not self.ensure_connection():
            return
        
        try:
            cursor = self.connection.cursor()
            
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    phone VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица консультаций
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consultations (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    consultation_type VARCHAR(50) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    payment_id VARCHAR(255),
                    payment_status VARCHAR(50) DEFAULT 'pending',
                    code_word VARCHAR(50) DEFAULT 'ЮРИСТ2024',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                )
            """)
            
            # Добавляем поле code_word, если его нет
            cursor.execute("""
                ALTER TABLE consultations 
                ADD COLUMN IF NOT EXISTS code_word VARCHAR(50) DEFAULT 'ЮРИСТ2024'
            """)
            
            # Добавляем поле email, если его нет
            cursor.execute("""
                ALTER TABLE consultations 
                ADD COLUMN IF NOT EXISTS email VARCHAR(255)
            """)
            
            # Таблица ИИ консультаций
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_consultations (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                )
            """)
            
            # Таблица подписок на ИИ консультации
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_subscriptions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    subscription_type VARCHAR(50) NOT NULL,
                    consultations_count INT NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    payment_id VARCHAR(255),
                    payment_status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                )
            """)
            
            self.connection.commit()
            cursor.close()
            logger.info("✅ Таблицы созданы/проверены")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц: {e}")
    
    def add_user(self, telegram_id: int, username: Optional[str] = None, 
                 first_name: Optional[str] = None, last_name: Optional[str] = None,
                 phone: Optional[str] = None) -> bool:
        """
        Добавление или обновление пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            username: Username пользователя
            first_name: Имя пользователя
            last_name: Фамилия пользователя
            phone: Номер телефона
            
        Returns:
            bool: True если успешно
        """
        def _add_user_operation():
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name, phone, updated_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (telegram_id) 
                DO UPDATE SET 
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    phone = EXCLUDED.phone,
                    updated_at = CURRENT_TIMESTAMP
            """, (telegram_id, username, first_name, last_name, phone))
            
            self.connection.commit()
            cursor.close()
            logger.info(f"✅ Пользователь {telegram_id} добавлен/обновлен")
            return True
        
        try:
            return self.execute_with_retry(_add_user_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка добавления пользователя {telegram_id}: {e}")
            return False
    
    def add_consultation(self, user_id: int, consultation_type: str, 
                        amount: float, payment_id: Optional[str] = None, 
                        code_word: str = "ЮРИСТ2024", email: Optional[str] = None) -> bool:
        """
        Добавление записи о консультации
        
        Args:
            user_id: ID пользователя в Telegram
            consultation_type: Тип консультации
            amount: Сумма платежа
            payment_id: ID платежа
            
        Returns:
            bool: True если успешно
        """
        def _add_consultation_operation():
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO consultations (user_id, consultation_type, amount, payment_id, payment_status, code_word, email)
                VALUES (%s, %s, %s, %s, 'completed', %s, %s)
            """, (user_id, consultation_type, amount, payment_id, code_word, email))
            
            self.connection.commit()
            cursor.close()
            logger.info(f"✅ Консультация добавлена для пользователя {user_id}")
            return True
        
        try:
            return self.execute_with_retry(_add_consultation_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка добавления консультации для {user_id}: {e}")
            return False
    
    def get_user_info(self, telegram_id: int) -> Optional[Dict]:
        """
        Получение информации о пользователе
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Dict: Информация о пользователе или None
        """
        def _get_user_operation():
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM users WHERE telegram_id = %s
            """, (telegram_id,))
            
            user = cursor.fetchone()
            cursor.close()
            
            return dict(user) if user else None
        
        try:
            return self.execute_with_retry(_get_user_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о пользователе {telegram_id}: {e}")
            return None
    
    def get_last_consultation(self, telegram_id: int) -> Optional[Dict]:
        """
        Получение информации о последней консультации пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Dict: Информация о последней консультации или None
        """
        def _get_consultation_operation():
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT c.*, u.username, u.phone
                FROM consultations c
                JOIN users u ON c.user_id = u.telegram_id
                WHERE c.user_id = %s
                ORDER BY c.created_at DESC
                LIMIT 1
            """, (telegram_id,))
            
            consultation = cursor.fetchone()
            cursor.close()
            
            return dict(consultation) if consultation else None
        
        try:
            return self.execute_with_retry(_get_consultation_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка получения последней консультации для {telegram_id}: {e}")
            return None
    
    def verify_code_word(self, telegram_id: int, code_word: str) -> bool:
        """
        Проверка кодового слова для пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            code_word: Кодовое слово для проверки
            
        Returns:
            bool: True если кодовое слово верное
        """
        def _verify_operation():
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM consultations 
                WHERE user_id = %s AND code_word = %s AND payment_status = 'completed'
                ORDER BY created_at DESC
                LIMIT 1
            """, (telegram_id, code_word))
            
            count = cursor.fetchone()[0]
            cursor.close()
            
            return count > 0
        
        try:
            return self.execute_with_retry(_verify_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка проверки кодового слова для {telegram_id}: {e}")
            return False
    
    def get_consultation_by_code_word(self, telegram_id: int, code_word: str) -> Optional[Dict]:
        """
        Получение информации о консультации по кодовому слову
        
        Args:
            telegram_id: ID пользователя в Telegram
            code_word: Кодовое слово
            
        Returns:
            Dict: Информация о консультации или None
        """
        def _get_consultation_operation():
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT c.*, u.username, u.first_name, u.last_name, u.phone
                FROM consultations c
                JOIN users u ON c.user_id = u.telegram_id
                WHERE c.user_id = %s AND c.code_word = %s
                ORDER BY c.created_at DESC
                LIMIT 1
            """, (telegram_id, code_word))
            
            consultation = cursor.fetchone()
            cursor.close()
            
            return dict(consultation) if consultation else None
        
        try:
            return self.execute_with_retry(_get_consultation_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка получения консультации по кодовому слову для {telegram_id}: {e}")
            return None
    
    def get_consultation_email(self, payment_id: str) -> Optional[str]:
        """
        Получение email из консультации по ID платежа
        
        Args:
            payment_id: ID платежа
            
        Returns:
            str: Email или None
        """
        def _get_email_operation():
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT email FROM consultations 
                WHERE payment_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (payment_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result else None
        
        try:
            return self.execute_with_retry(_get_email_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка получения email для платежа {payment_id}: {e}")
            return None
    
    def get_user_statistics(self, telegram_id: int) -> Dict:
        """
        Получение статистики пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Dict: Статистика пользователя
        """
        def _get_stats_operation():
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Общее количество консультаций
            cursor.execute("""
                SELECT COUNT(*) as total_consultations,
                       SUM(amount) as total_amount
                FROM consultations 
                WHERE user_id = %s
            """, (telegram_id,))
            
            stats = cursor.fetchone()
            cursor.close()
            
            return {
                'total_consultations': stats['total_consultations'] if stats else 0,
                'total_amount': float(stats['total_amount']) if stats and stats['total_amount'] else 0.0
            }
        
        try:
            return self.execute_with_retry(_get_stats_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики для {telegram_id}: {e}")
            return {}
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Соединение с базой данных закрыто")
    
    def add_ai_consultation(self, user_id: int, question: str, answer: str = None) -> bool:
        """
        Добавление ИИ консультации
        
        Args:
            user_id: ID пользователя
            question: Вопрос пользователя
            answer: Ответ ИИ
            
        Returns:
            bool: True если успешно
        """
        def _add_ai_consultation_operation():
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO ai_consultations (user_id, question, answer)
                VALUES (%s, %s, %s)
            """, (user_id, question, answer))
            
            self.connection.commit()
            cursor.close()
            return True
        
        try:
            return self.execute_with_retry(_add_ai_consultation_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка добавления ИИ консультации для {user_id}: {e}")
            return False
    
    def get_ai_consultations_count(self, user_id: int) -> int:
        """
        Получение количества ИИ консультаций пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            int: Количество консультаций
        """
        def _get_count_operation():
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM ai_consultations 
                WHERE user_id = %s
            """, (user_id,))
            
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        
        try:
            return self.execute_with_retry(_get_count_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка получения количества ИИ консультаций для {user_id}: {e}")
            return 0
    
    def get_ai_subscription_consultations(self, user_id: int) -> int:
        """
        Получение количества доступных консультаций по подписке
        
        Args:
            user_id: ID пользователя
            
        Returns:
            int: Количество доступных консультаций
        """
        def _get_subscription_operation():
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT SUM(consultations_count) FROM ai_subscriptions 
                WHERE user_id = %s AND payment_status = 'completed'
            """, (user_id,))
            
            result = cursor.fetchone()[0]
            cursor.close()
            return int(result) if result else 0
        
        try:
            return self.execute_with_retry(_get_subscription_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка получения подписки ИИ консультаций для {user_id}: {e}")
            return 0
    
    def get_used_subscription_consultations(self, user_id: int) -> int:
        """
        Получение количества использованных консультаций из подписки
        
        Args:
            user_id: ID пользователя
            
        Returns:
            int: Количество использованных консультаций из подписки
        """
        def _get_used_operation():
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM ai_consultations 
                WHERE user_id = %s AND id > (
                    SELECT COALESCE(MAX(id), 0) FROM ai_consultations 
                    WHERE user_id = %s AND id <= (
                        SELECT COALESCE(MAX(id), 0) FROM ai_consultations 
                        WHERE user_id = %s 
                        ORDER BY created_at 
                        LIMIT 5
                    )
                )
            """, (user_id, user_id, user_id))
            
            result = cursor.fetchone()[0]
            cursor.close()
            return int(result) if result else 0
        
        try:
            return self.execute_with_retry(_get_used_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка получения использованных подписочных консультаций для {user_id}: {e}")
            return 0
    
    def add_ai_subscription(self, user_id: int, subscription_type: str, 
                          consultations_count: int, amount: float, 
                          payment_id: str = None) -> bool:
        """
        Добавление подписки на ИИ консультации
        
        Args:
            user_id: ID пользователя
            subscription_type: Тип подписки
            consultations_count: Количество консультаций
            amount: Сумма
            payment_id: ID платежа
            
        Returns:
            bool: True если успешно
        """
        def _add_subscription_operation():
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO ai_subscriptions (user_id, subscription_type, consultations_count, amount, payment_id, payment_status)
                VALUES (%s, %s, %s, %s, %s, 'completed')
            """, (user_id, subscription_type, consultations_count, amount, payment_id))
            
            self.connection.commit()
            cursor.close()
            return True
        
        try:
            return self.execute_with_retry(_add_subscription_operation)
        except Exception as e:
            logger.error(f"❌ Ошибка добавления подписки ИИ для {user_id}: {e}")
            return False
    
    def can_user_use_ai(self, user_id: int) -> bool:
        """
        Проверка, может ли пользователь использовать ИИ консультации
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если может использовать (всегда True для безлимитного использования)
        """
        return True
    
    def get_remaining_ai_consultations(self, user_id: int) -> int:
        """
        Получение количества оставшихся ИИ консультаций
        
        Args:
            user_id: ID пользователя
            
        Returns:
            int: Количество оставшихся консультаций (безлимит = -1)
        """
        return -1  # -1 означает безлимит 