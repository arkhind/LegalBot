import os
import asyncio
import signal
import json
import requests
import re
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from loguru import logger
from payment_handler import PaymentHandler
from database import Database
import psycopg2.extras

# Импорты для клиента юриста (опционально)
try:
    from telethon import TelegramClient, events
    from telethon.sessions import StringSession
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    logger.warning("Telethon не установлен. Клиент юриста будет работать в режиме бота.")

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logger.add("bot.log", rotation="1 day", retention="7 days")


class TelegramSessionManager:
    """Менеджер для управления сессией Telegram аккаунта юриста"""
    
    def __init__(self):
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.phone = os.getenv("TELEGRAM_PHONE")
        self.session_file = "veretenov_session.txt"
        
    async def ensure_session(self):
        """Проверяет и создает сессию если необходимо"""
        if not all([self.api_id, self.api_hash, self.phone]):
            logger.warning("❌ Не все переменные окружения установлены для Telegram сессии")
            logger.warning("Нужно установить: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
            return False
        
        # Проверяем существующую сессию
        if await self.test_existing_session():
            logger.info("✅ Существующая сессия активна")
            return True
        
        # Создаем новую сессию
        logger.info("🔐 Создание новой сессии Telegram...")
        return await self.create_new_session()
    
    async def test_existing_session(self):
        """Тестирует существующую сессию"""
        session_string = self.load_session()
        if not session_string:
            return False
        
        try:
            client = TelegramClient(
                StringSession(session_string), 
                int(self.api_id), 
                self.api_hash
            )
            
            await client.connect()
            
            if await client.is_user_authorized():
                me = await client.get_me()
                logger.info(f"✅ Сессия активна для: {me.first_name} (@{me.username})")
                await client.disconnect()
                return True
            else:
                logger.warning("❌ Существующая сессия недействительна")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования сессии: {e}")
            return False
    
    async def create_new_session(self):
        """Создает новую сессию"""
        try:
            # Создаем клиент
            client = TelegramClient(
                StringSession(), 
                int(self.api_id), 
                self.api_hash
            )
            
            # Подключаемся к Telegram
            await client.connect()
            
            # Проверяем, авторизованы ли мы
            if not await client.is_user_authorized():
                logger.info("🔐 Требуется авторизация...")
                
                # Отправляем код подтверждения
                await client.send_code_request(self.phone)
                
                # Запрашиваем код у пользователя
                print("\n" + "="*50)
                print("🔐 ТРЕБУЕТСЯ АВТОРИЗАЦИЯ В TELEGRAM")
                print("="*50)
                print(f"📱 Код подтверждения отправлен на номер: {self.phone}")
                print("📝 Введите код из Telegram:")
                code = input("Код: ").strip()
                
                try:
                    # Входим с кодом
                    await client.sign_in(self.phone, code)
                    logger.info("✅ Авторизация успешна!")
                except Exception as e:
                    # Если нужен пароль от двухфакторной аутентификации
                    if "2FA" in str(e) or "password" in str(e).lower():
                        print("🔒 Требуется пароль от двухфакторной аутентификации:")
                        password = input("Пароль: ").strip()
                        await client.sign_in(password=password)
                        logger.info("✅ Авторизация с 2FA успешна!")
                    else:
                        raise e
            else:
                logger.info("✅ Уже авторизован")
            
            # Получаем информацию о себе
            me = await client.get_me()
            logger.info(f"👤 Вход выполнен: {me.first_name} (@{me.username})")
            
            # Сохраняем сессию
            session_string = client.session.save()
            with open(self.session_file, 'w') as f:
                f.write(session_string)
            
            logger.info(f"💾 Сессия сохранена в {self.session_file}")
            
            # Отключаемся
            await client.disconnect()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания сессии: {e}")
            return False
    
    def load_session(self):
        """Загружает сохраненную сессию"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            logger.error(f"Ошибка загрузки сессии: {e}")
        return None


class LegalBot:
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not self.bot_token:
            raise ValueError("BOT_TOKEN не найден в .env файле")
        
        # Настройка OpenRouter для Gemini
        if self.openrouter_api_key:
            logger.info("Настройка OpenRouter API для Gemini...")
            self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
            self.openrouter_headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-repo/legal-bot",
                "X-Title": "Legal AI Bot"
            }
            logger.info("OpenRouter API настроен успешно")
        else:
            logger.warning("OPENROUTER_API_KEY не найден в переменных окружения")
        
        # Настройка доступа для юристов
        lawyer_id_str = os.getenv("LAWYER_TELEGRAM_ID", "0")
        try:
            lawyer_id = int(lawyer_id_str) if lawyer_id_str.isdigit() else 0
        except (ValueError, AttributeError):
            lawyer_id = 0
            
        self.allowed_lawyers = [
            lawyer_id,  # ID юриста из .env
            89895202224  # Номер телефона юриста
        ]
        
        self.application = Application.builder().token(self.bot_token).build()
        self.payment_handler = PaymentHandler()
        self.database = Database()
        self._load_texts()
        self._setup_handlers()
        
        # Инициализация клиента юриста
        self.lawyer_client_enabled = os.getenv("LAWYER_CLIENT_ENABLED", "false").lower() == "true"
        self.lawyer_client = None
        self.lawyer_session_file = "veretenov_session.txt"
        self.lawyer_data_file = "lawyer_data.json"
        
        # Инициализация менеджера сессий
        self.session_manager = TelegramSessionManager()
        
        # Словарь для хранения пользователей, ожидающих ввода email
        self.email_waiting_users = {}
        # Словарь для хранения email пользователей
        self.user_emails = {}
        
        if self.lawyer_client_enabled:
            self._init_lawyer_client()
    
    def _load_texts(self):
        """Загрузка всех текстов из файлов"""
        try:
            logger.info("Загрузка текстовых файлов...")
            
            # Загружаем тексты
            with open('texts/welcome.txt', 'r', encoding='utf-8') as f:
                self.welcome_text = f.read().strip()
            logger.debug("welcome.txt загружен")
            
            with open('texts/ai_consultation.txt', 'r', encoding='utf-8') as f:
                self.ai_consultation_text = f.read().strip()
            logger.debug("ai_consultation.txt загружен")
            
            with open('texts/real_lawyer.txt', 'r', encoding='utf-8') as f:
                self.real_lawyer_text = f.read().strip()
            logger.debug("real_lawyer.txt загружен")
            
            with open('texts/about.txt', 'r', encoding='utf-8') as f:
                self.about_text = f.read().strip()
            logger.debug("about.txt загружен")
            
            with open('texts/error_messages.txt', 'r', encoding='utf-8') as f:
                error_lines = f.read().strip().split('\n\n')
                self.error_messages = {
                    'no_openai': error_lines[0],
                    'processing_error': error_lines[1],
                    'general_error': error_lines[2]
                }
            logger.debug("error_messages.txt загружен")
            
            # Загружаем промпт
            with open('prompts/legal_ai_prompt.txt', 'r', encoding='utf-8') as f:
                self.legal_ai_prompt = f.read().strip()
            logger.debug("legal_ai_prompt.txt загружен")
            

                
            logger.info("Все тексты успешно загружены")
        except Exception as e:
            logger.error(f"Ошибка загрузки текстов: {e}")
            logger.info("Используем fallback тексты")
            # Fallback тексты
            self.welcome_text = "Добро пожаловать в Юридический Бот!"
            self.ai_consultation_text = "ИИ Консультация"
            self.real_lawyer_text = "Связаться с юристом"
            self.about_text = "О нас"
            self.legal_ai_prompt = "Ты - юрист-консультант."

            self.error_messages = {
                'no_openai': "Извините, ИИ консультация временно недоступна. Пожалуйста, свяжитесь с юристом через кнопку 'Связаться с юристом'.",
                'processing_error': "Извините, произошла ошибка при обработке вашего вопроса. Пожалуйста, попробуйте еще раз или свяжитесь с юристом.",
                'general_error': "Извините, произошла ошибка, попробуйте еще раз"
            }
            logger.info("Fallback тексты установлены")
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        logger.info("Настройка обработчиков команд...")
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        
        # Обработчики платежей (ЮKassa)
        # Удалены старые обработчики Telegram Payments
        
        # Обработчик для юристов (проверка кодовых слов)
        self.application.add_handler(CommandHandler("check", self.check_code_word_command))
        logger.info("Обработчики команд настроены")
    
    def _init_lawyer_client(self):
        """Инициализация клиента юриста"""
        if not TELETHON_AVAILABLE:
            logger.warning("Telethon недоступен, клиент юриста отключен")
            return
        
        try:
            api_id = os.getenv("TELEGRAM_API_ID")
            api_hash = os.getenv("TELEGRAM_API_HASH")
            
            if not api_id or not api_hash:
                logger.warning("TELEGRAM_API_ID или TELEGRAM_API_HASH не установлены")
                return
            
            self.lawyer_api_id = int(api_id)
            self.lawyer_api_hash = api_hash
            self.lawyer_data = self._load_lawyer_data()
            
            logger.info("✅ Клиент юриста инициализирован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации клиента юриста: {e}")
    
    def _load_lawyer_data(self):
        """Загрузка данных клиента юриста"""
        try:
            if os.path.exists(self.lawyer_data_file):
                with open(self.lawyer_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка JSON в файле {self.lawyer_data_file}: {e}")
            # Создаем резервную копию поврежденного файла
            backup_file = f"{self.lawyer_data_file}.backup"
            try:
                import shutil
                shutil.copy2(self.lawyer_data_file, backup_file)
                logger.info(f"Создана резервная копия: {backup_file}")
            except Exception as backup_error:
                logger.error(f"Не удалось создать резервную копию: {backup_error}")
        except Exception as e:
            logger.error(f"Ошибка загрузки данных юриста: {e}")
        return {"clients": {}, "settings": {}}
    
    def _save_lawyer_data(self):
        """Сохранение данных клиента юриста"""
        try:
            with open(self.lawyer_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.lawyer_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения данных юриста: {e}")
    
    def _load_lawyer_session(self):
        """Загрузка сессии юриста"""
        return self.session_manager.load_session()
    
    def _check_lawyer_payment(self, user_id: int) -> dict:
        """Проверка оплаты консультации для юриста"""
        if not self.database.connection:
            return None
        
        try:
            cursor = self.database.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT * FROM consultations 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка проверки платежа для {user_id}: {e}")
            return None
    
    def _get_lawyer_user_info(self, user_id: int) -> dict:
        """Получение информации о пользователе для юриста"""
        if not self.database.connection:
            return None
        
        try:
            cursor = self.database.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT * FROM users 
                WHERE telegram_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе {user_id}: {e}")
            return None
    
    async def check_code_word_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для проверки кодового слова юристом"""
        user_id = update.effective_user.id
        
        # Проверяем, что команда от юриста
        if user_id not in self.allowed_lawyers:
            await update.message.reply_text("❌ У вас нет доступа к этой команде.")
            return
        
        # Получаем аргументы команды
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "💡 Как использовать команду проверки:\n\n"
                "/check <telegram_id> <кодовое_слово>\n\n"
                "Пример:\n"
                "/check 123456789 ЮРИСТ2024\n\n"
                "Или просто перешлите сообщение от клиента с кодовым словом."
            )
            return
        
        try:
            client_telegram_id = int(args[0])
            code_word = args[1]
            
            await self.verify_code_word_for_lawyer(update, client_telegram_id, code_word)
            
        except ValueError:
            await update.message.reply_text("❌ Ошибка: Telegram ID должен быть числом.")
        except Exception as e:
            logger.error(f"Ошибка проверки кодового слова: {e}")
            await update.message.reply_text("❌ Произошла ошибка при проверке кодового слова.")
    
    async def verify_code_word_for_lawyer(self, update: Update, client_telegram_id: int, code_word: str):
        """Проверка кодового слова для юриста"""
        try:
            # Проверяем кодовое слово в базе данных
            is_valid = self.database.verify_code_word(client_telegram_id, code_word)
            
            if is_valid:
                # Получаем информацию о консультации
                consultation = self.database.get_consultation_by_code_word(client_telegram_id, code_word)
                
                if consultation:
                    # Формируем сообщение с информацией о клиенте
                    message = f"✅ Кодовое слово ВЕРНОЕ!\n\n"
                    message += f"📋 Информация о клиенте:\n"
                    message += f"👤 Имя: {consultation.get('first_name', 'Не указано')} {consultation.get('last_name', '')}\n"
                    message += f"📱 Username: @{consultation.get('username', 'Не указан')}\n"
                    message += f"🆔 Telegram ID: {consultation['user_id']}\n"
                    message += f"💰 Сумма: {consultation['amount']}₽\n"
                    message += f"📋 Тип: {consultation['consultation_type']}\n"
                    message += f"📅 Дата оплаты: {consultation['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                    message += f"🆔 ID платежа: {consultation['payment_id']}\n\n"
                    message += f"✅ Можно оказывать консультацию"
                    
                    await update.message.reply_text(message)
                    
                    logger.info(f"Кодовое слово подтверждено для клиента {client_telegram_id}")
                else:
                    await update.message.reply_text(
                        "⚠️ Кодовое слово верное, но информация о консультации не найдена"
                    )
            else:
                await update.message.reply_text(
                    "❌ Кодовое слово НЕВЕРНОЕ!\n\n"
                    "Возможные причины:\n"
                    "• Неправильное кодовое слово\n"
                    "• Платеж не был совершен\n"
                    "• Неправильный Telegram ID\n"
                    "• Консультация уже использована\n\n"
                    "⚠️ Не оказывайте консультацию без подтверждения оплаты"
                )
                
                logger.warning(f"Неверное кодовое слово для клиента {client_telegram_id}")
                
        except Exception as e:
            logger.error(f"Ошибка проверки кодового слова: {e}")
            await update.message.reply_text(
                "❌ Ошибка при проверке кодового слова\n\n"
                "Пожалуйста, попробуйте еще раз или обратитесь к администратору."
            )
    
    async def notify_lawyer(self, user_id: int, amount: float, consultation_name: str, consultation_type: str):
        """
        Уведомляет юриста о новой оплаченной консультации
        """
        try:
            lawyer_chat_id = os.getenv("LAWYER_CHAT_ID")
            
            if not lawyer_chat_id:
                logger.warning("LAWYER_CHAT_ID не настроен, уведомление не отправлено")
                return
            
            # Получаем информацию о пользователе
            user_info = self.database.get_user_info(user_id)
            
            message = f"💰 НОВАЯ ОПЛАЧЕННАЯ КОНСУЛЬТАЦИЯ!\n\n"
            message += f"👤 Клиент: {user_info.get('first_name', '')} {user_info.get('last_name', '')}\n"
            message += f"📱 Username: @{user_info.get('username', 'Не указан')}\n"
            message += f"🆔 Telegram ID: {user_id}\n"
            message += f"💰 Сумма: {amount}₽\n"
            message += f"📋 Тип: {consultation_name}\n"
            message += f"🔐 Кодовое слово: ЮРИСТ2024\n\n"
            message += f"📞 Контакты для связи:\n"
            message += f"👤 Telegram: @narhipovd\n\n"
            message += f"💡 Ожидайте обращения клиента с кодовым словом"
            
            await self.application.bot.send_message(
                chat_id=lawyer_chat_id,
                text=message
            )
            
            logger.info(f"Уведомление отправлено юристу о консультации пользователя {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления юристу: {e}")
    
    def get_legal_advice_from_gemini(self, user_message):
        """
        Получает юридическую консультацию через OpenRouter API с Gemini 2.0 Flash Lite
        """
        if not self.openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY не установлен, консультация пропущена")
            return None
        
        try:
            # Формируем промпт для юридической консультации
            system_prompt = self.legal_ai_prompt
            
            # Добавляем дополнительную инструкцию о форматировании
            formatting_instruction = "\n\nВАЖНО: Отвечай простым текстом без использования специальных символов разметки, эмодзи или форматирования."
            prompt = f"{system_prompt}{formatting_instruction}\n\nПользователь: {user_message}"
            
            data = {
                "model": "google/gemini-2.0-flash-lite-001",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1500
            }
            
            response = requests.post(
                self.openrouter_url, 
                headers=self.openrouter_headers, 
                json=data, 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"Ошибка OpenRouter API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при получении консультации через OpenRouter: {e}")
            return None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        logger.info(f"Команда /start от пользователя {user.id} (@{user.username})")
        
        # Сохраняем информацию о пользователе в базу данных
        try:
            self.database.add_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            logger.info(f"Пользователь {user.id} сохранен в базу данных")
        except Exception as e:
            logger.error(f"Ошибка сохранения пользователя {user.id} в базу данных: {e}")
        
        keyboard = [
            [InlineKeyboardButton("🤖 ИИ консультация", callback_data="ai_consultation")],
            [InlineKeyboardButton("👨‍💼 Связаться с юристом", callback_data="real_lawyer")],
            [InlineKeyboardButton("ℹ️ О нас", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await update.message.reply_text(
                self.welcome_text,
                reply_markup=reply_markup
            )
            logger.info(f"Пользователь {user.id} запустил бота")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в start_command: {e}")
            # Попробуем отправить простой текст
            try:
                await update.message.reply_text(
                    "Добро пожаловать в Юридический Бот!",
                    reply_markup=reply_markup
                )
                logger.info(f"Пользователь {user.id} запустил бота (fallback)")
            except Exception as e2:
                logger.error(f"Критическая ошибка отправки сообщения: {e2}")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        try:
            await query.answer()
            
            logger.info(f"Обработка кнопки: {query.data} от пользователя {query.from_user.id}")
            
            # Проверяем, что query.message существует
            if not query.message:
                logger.error(f"query.message is None для кнопки {query.data}")
                # Пытаемся отправить новое сообщение пользователю
                try:
                    await context.bot.send_message(
                        chat_id=query.from_user.id,
                        text="❌ Произошла ошибка. Попробуйте еще раз или начните заново с /start"
                    )
                except Exception as send_error:
                    logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")
                return
            
            if query.data == "ai_consultation":
                await self.handle_ai_consultation(query)
            elif query.data == "real_lawyer":
                await self.handle_real_lawyer(query)
            elif query.data == "pay_oral_consultation":
                await self.handle_payment(query, "oral")
            elif query.data == "pay_full_consultation":
                await self.handle_payment(query, "full")
            elif query.data.startswith("check_payment_"):
                payment_id = query.data.replace("check_payment_", "")
                await self.handle_check_payment(query, payment_id)
            elif query.data.startswith("enter_email_"):
                consultation_type = query.data.replace("enter_email_", "")
                await self.handle_enter_email(query, consultation_type)
            elif query.data.startswith("no_receipt_"):
                consultation_type = query.data.replace("no_receipt_", "")
                await self.handle_no_receipt(query, consultation_type)
            
            elif query.data == "about":
                await self.handle_about(query)

            elif query.data == "main_menu":
                await self.handle_main_menu(query)
            else:
                logger.warning(f"Неизвестная кнопка: {query.data}")
        except Exception as e:
            logger.error(f"Ошибка в обработке кнопки: {e}")
            try:
                await query.answer(self.error_messages['general_error'])
            except:
                logger.error("Не удалось отправить сообщение об ошибке")
    
    async def handle_ai_consultation(self, query):
        """Обработка ИИ консультации"""
        user_id = query.from_user.id
        
        keyboard = [
            [InlineKeyboardButton("👨‍💼 Связаться с юристом", callback_data="real_lawyer")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "🤖 ИИ консультация\n\n"
            "Задайте ваш юридический вопрос, и я постараюсь помочь вам с ответом.\n\n"
            "Примеры вопросов:\n"
            "• Как расторгнуть договор?\n"
            "• Какие документы нужны для регистрации ИП?\n"
            "• Как защитить свои права при покупке товара?\n\n"
            "Просто напишите ваш вопрос в следующем сообщении.\n\n"
            "💡 Безлимитное использование ИИ консультаций!"
        )
        
        try:
            if query.message:
                await query.message.reply_text(
                    message,
                    reply_markup=reply_markup
                )
            else:
                await query.get_bot().send_message(
                    chat_id=user_id,
                    text=message,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в handle_ai_consultation: {e}")
            return
        
        logger.info(f"Пользователь {user_id} выбрал ИИ консультацию (безлимит)")
    
    async def handle_real_lawyer(self, query):
        """Обработка связи с юристом"""
        reply_markup = self.payment_handler.create_consultation_keyboard()
        message_text = self.payment_handler.get_consultation_message()
        
        try:
            if query.message:
                await query.message.reply_text(
                    message_text,
                    reply_markup=reply_markup
                )
            else:
                # Альтернативный способ отправки сообщения
                await query.get_bot().send_message(
                    chat_id=query.from_user.id,
                    text=message_text,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в handle_real_lawyer: {e}")
            return
            
        logger.info(f"Пользователь {query.from_user.id} выбрал связь с юристом")
    

    
    async def handle_payment(self, query, consultation_type="oral"):
        """Обработка оплаты консультации через ЮKassa"""
        user_id = query.from_user.id
        
        logger.info(f"Пользователь {user_id} запросил {consultation_type} консультацию")
        
        # Запрашиваем email для чека
        await self.request_email_for_receipt(query, consultation_type)
    
    async def request_email_for_receipt(self, query, consultation_type="oral"):
        """Запрос email для отправки чека"""
        user_id = query.from_user.id
        
        # Создаем клавиатуру для ввода email
        keyboard = [
            [InlineKeyboardButton("📧 Ввести email", callback_data=f"enter_email_{consultation_type}")],
            [InlineKeyboardButton("🚫 Без чека", callback_data=f"no_receipt_{consultation_type}")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = (
            f"🧾 Для отправки официального чека нужен ваш email\n\n"
            f"📧 Чек будет отправлен на указанный email\n"
            f"💡 Если не укажете email, чек не будет создан\n\n"
            f"Выберите действие:"
        )
        
        if query.message:
            await query.message.reply_text(message_text, reply_markup=reply_markup)
        else:
            await query.get_bot().send_message(
                chat_id=query.from_user.id,
                text=message_text,
                reply_markup=reply_markup
            )
    
    async def handle_enter_email(self, query, consultation_type="oral"):
        """Обработка ввода email"""
        user_id = query.from_user.id
        
        # Сохраняем состояние ожидания email
        self.email_waiting_users[user_id] = consultation_type
        
        message_text = (
            f"📧 Введите ваш email для отправки чека:\n\n"
            f"💡 Пример: example@mail.ru\n"
            f"⚠️ Email должен быть корректным\n\n"
            f"Отправьте email текстовым сообщением"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚫 Отмена", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query.message:
            await query.message.reply_text(message_text, reply_markup=reply_markup)
        else:
            await query.get_bot().send_message(
                chat_id=query.from_user.id,
                text=message_text,
                reply_markup=reply_markup
            )
    
    async def handle_no_receipt(self, query, consultation_type="oral"):
        """Обработка отказа от чека"""
        user_id = query.from_user.id
        
        # Создаем платеж без чека
        payment_info = self.payment_handler.create_payment(consultation_type, user_id, None)
        
        if payment_info["success"]:
            # Сохраняем консультацию в базу данных (без email)
            self.database.add_consultation(
                user_id=user_id,
                consultation_type=consultation_type,
                amount=payment_info["amount"],
                payment_id=payment_info["payment_id"],
                code_word="ЮРИСТ2024",
                email=None
            )
            try:
                # Создаем клавиатуру с кнопкой для оплаты
                keyboard = [
                    [InlineKeyboardButton("💳 Оплатить", url=payment_info["confirmation_url"])],
                    [InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_payment_{payment_info['payment_id']}")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message_text = (
                    f"💳 Оплата {payment_info['title']}\n\n"
                    f"💰 Сумма: {payment_info['amount']}₽\n"
                    f"📝 Описание: {payment_info['description']}\n\n"
                    f"⚠️ Чек не будет создан\n\n"
                    f"Для оплаты нажмите кнопку ниже 👇"
                )
                
                if query.message:
                    await query.message.reply_text(message_text, reply_markup=reply_markup)
                else:
                    await query.get_bot().send_message(
                        chat_id=query.from_user.id,
                        text=message_text,
                        reply_markup=reply_markup
                    )
                
                logger.info(f"Пользователь {user_id} создал платеж {payment_info['payment_id']} для {consultation_type} консультации (без чека)")
                
            except Exception as e:
                logger.error(f"Ошибка отправки платежа: {e}")
                error_message = "❌ Ошибка создания платежа. Попробуйте позже."
                try:
                    if query.message:
                        await query.message.reply_text(error_message)
                    else:
                        await query.get_bot().send_message(
                            chat_id=query.from_user.id,
                            text=error_message
                        )
                except Exception as send_error:
                    logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")
        else:
            error_message = f"❌ Ошибка создания платежа: {payment_info.get('error', 'Неизвестная ошибка')}"
            try:
                if query.message:
                    await query.message.reply_text(error_message)
                else:
                    await query.get_bot().send_message(
                        chat_id=query.from_user.id,
                        text=error_message
                    )
            except Exception as send_error:
                logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")
            logger.error(f"Ошибка создания платежа для пользователя {user_id}: {payment_info.get('error')}")
        
        if payment_info["success"]:
            try:
                # Создаем клавиатуру с кнопкой для оплаты
                keyboard = [
                    [InlineKeyboardButton("💳 Оплатить", url=payment_info["confirmation_url"])],
                    [InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_payment_{payment_info['payment_id']}")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message_text = (
                    f"💳 Оплата {payment_info['title']}\n\n"
                    f"💰 Сумма: {payment_info['amount']}₽\n"
                    f"📝 Описание: {payment_info['description']}\n\n"
                    f"Для оплаты нажмите кнопку ниже 👇"
                )
                
                if query.message:
                    await query.message.reply_text(message_text, reply_markup=reply_markup)
                else:
                    await query.get_bot().send_message(
                        chat_id=query.from_user.id,
                        text=message_text,
                        reply_markup=reply_markup
                    )
                
                logger.info(f"Пользователь {user_id} создал платеж {payment_info['payment_id']} для {consultation_type} консультации")
                
            except Exception as e:
                logger.error(f"Ошибка отправки платежа: {e}")
                error_message = "❌ Ошибка создания платежа. Попробуйте позже."
                try:
                    if query.message:
                        await query.message.reply_text(error_message)
                    else:
                        await query.get_bot().send_message(
                            chat_id=query.from_user.id,
                            text=error_message
                        )
                except Exception as send_error:
                    logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")
        else:
            error_message = f"❌ Ошибка создания платежа: {payment_info.get('error', 'Неизвестная ошибка')}"
            try:
                if query.message:
                    await query.message.reply_text(error_message)
                else:
                    await query.get_bot().send_message(
                        chat_id=query.from_user.id,
                        text=error_message
                    )
            except Exception as send_error:
                logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")
            logger.error(f"Ошибка создания платежа для пользователя {user_id}: {payment_info.get('error')}")
    
    async def handle_check_payment(self, query, payment_id):
        """Проверка статуса платежа"""
        user_id = query.from_user.id
        
        logger.info(f"Пользователь {user_id} проверяет статус платежа {payment_id}")
        
        payment_status = self.payment_handler.check_payment_status(payment_id)
        
        if payment_status["success"]:
            if payment_status["status"] == "succeeded":
                # Платеж успешен
                amount = payment_status["amount"]
                consultation_type = payment_status["metadata"].get("consultation_type", "oral")
                
                # Получаем email из базы данных
                user_email = self.database.get_consultation_email(payment_id)
                
                # Определяем название типа консультации
                consultation_name = "Устная консультация" if consultation_type == "oral" else "Полная консультация с изучением документов"
                
                keyboard = [
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Отправляем сообщение об успешной оплате
                await query.message.reply_text(
                    f"✅ Платеж успешно оплачен!\n\n"
                    f"💰 Сумма: {amount}₽\n"
                    f"📋 Тип консультации: {consultation_name}\n"
                    f"🆔 ID платежа: {payment_id}\n\n"
                    f"Спасибо за оплату! Наш юрист свяжется с вами в ближайшее время.\n\n"
                    f"📞 Контакты для связи:\n"
                    f"👤 Telegram: @narhipovd",
                    reply_markup=reply_markup
                )
                
                # Создаем чек через ЮKassa
                try:
                    # Получаем email из базы данных
                    user_email = self.database.get_consultation_email(payment_id)
                    receipt_result = self.payment_handler.create_receipt(payment_id, user_email)
                    if receipt_result["success"]:
                        await query.message.reply_text(
                            f"🧾 Чек отправлен!\n\n"
                            f"✅ Официальный чек создан автоматически\n"
                            f"📧 Чек отправлен на email\n"
                            f"🆔 ID платежа: {payment_id}\n\n"
                            f"💡 Если чек не пришел, проверьте папку 'Спам'"
                        )
                        logger.info(f"Чек ЮKassa подтвержден для пользователя {user_id}: {receipt_result.get('receipt_id')}")
                    else:
                        logger.error(f"Ошибка проверки чека ЮKassa для пользователя {user_id}: {receipt_result.get('error')}")
                        # Отправляем уведомление об ошибке
                        await query.message.reply_text(
                            f"⚠️ Платеж успешен, но возникла проблема с чеком\n\n"
                            f"📋 Услуга: {consultation_name}\n"
                            f"💰 Сумма: {amount}₽\n"
                            f"🆔 ID платежа: {payment_id}\n\n"
                            f"📞 Обратитесь в поддержку: @narhipovd"
                        )
                except Exception as e:
                    logger.error(f"Ошибка создания чека ЮKassa для пользователя {user_id}: {e}")
                    # Отправляем уведомление об ошибке
                    await query.message.reply_text(
                        f"⚠️ Платеж успешен, но возникла проблема с чеком\n\n"
                        f"📋 Услуга: {consultation_name}\n"
                        f"💰 Сумма: {amount}₽\n"
                        f"🆔 ID платежа: {payment_id}\n\n"
                        f"📞 Обратитесь в поддержку: @narhipovd"
                    )
                
                # Отправляем кодовое слово отдельным сообщением
                await query.message.reply_text(
                    f"🔐 КОДОВОЕ СЛОВО ДЛЯ ЮРИСТА\n\n"
                    f"📝 ЮРИСТ2024\n\n"
                    f"⚠️ ВАЖНО: При обращении к юристу обязательно назовите это кодовое слово для подтверждения оплаты.\n\n"
                    f"💡 Как использовать:\n"
                    f"1. Свяжитесь с юристом по указанным контактам\n"
                    f"2. Назовите кодовое слово: ЮРИСТ2024\n"
                    f"3. Укажите ваш Telegram ID: {user_id}\n"
                    f"4. Опишите ваш вопрос\n\n"
                    f"🔒 Кодовое слово действительно только для этой консультации."
                )
                
                logger.info(f"Успешный платеж от пользователя {user_id}: {amount}₽ за {consultation_type} консультацию")
                
                # Уведомляем юриста о новой оплаченной консультации
                await self.notify_lawyer(user_id, amount, consultation_name, consultation_type)
                
            elif payment_status["status"] == "pending":
                # Платеж в обработке
                keyboard = [
                    [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    f"⏳ Платеж в обработке\n\n"
                    f"Пожалуйста, подождите. Платеж обрабатывается платежной системой.\n\n"
                    f"Вы можете проверить статус через несколько минут.",
                    reply_markup=reply_markup
                )
                
            else:
                # Платеж не оплачен или отменен
                keyboard = [
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data="real_lawyer")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    f"❌ Платеж не оплачен\n\n"
                    f"Статус: {payment_status['status']}\n\n"
                    f"Попробуйте создать новый платеж.",
                    reply_markup=reply_markup
                )
        else:
            # Ошибка при проверке статуса
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"check_payment_{payment_id}")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                f"❌ Ошибка проверки статуса платежа\n\n"
                f"Ошибка: {payment_status.get('error', 'Неизвестная ошибка')}\n\n"
                f"Попробуйте проверить статус еще раз.",
                reply_markup=reply_markup
            )
    
    # Удалены старые обработчики Telegram Payments
    # async def pre_checkout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    # async def successful_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    

    
    async def handle_about(self, query):
        """Обработка кнопки 'О нас'"""
        keyboard = [
            [InlineKeyboardButton("🤖 ИИ консультация", callback_data="ai_consultation")],
            [InlineKeyboardButton("👨‍💼 Связаться с юристом", callback_data="real_lawyer")],
            [InlineKeyboardButton("ℹ️ О нас", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            if query.message:
                await query.message.reply_text(
                    self.about_text,
                    reply_markup=reply_markup
                )
            else:
                # Альтернативный способ отправки сообщения
                await query.get_bot().send_message(
                    chat_id=query.from_user.id,
                    text=self.about_text,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в handle_about: {e}")
            return
            
        logger.info(f"Пользователь {query.from_user.id} открыл 'О нас'")
    
    async def handle_main_menu(self, query):
        """Обработка кнопки 'Главное меню'"""
        user = query.from_user
        
        # Сохраняем информацию о пользователе в базу данных
        self.database.add_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        keyboard = [
            [InlineKeyboardButton("🤖 ИИ консультация", callback_data="ai_consultation")],
            [InlineKeyboardButton("👨‍💼 Связаться с юристом", callback_data="real_lawyer")],
            [InlineKeyboardButton("ℹ️ О нас", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            if query.message:
                await query.message.reply_text(
                    self.welcome_text,
                    reply_markup=reply_markup
                )
            else:
                # Альтернативный способ отправки сообщения
                await query.get_bot().send_message(
                    chat_id=query.from_user.id,
                    text=self.welcome_text,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в handle_main_menu: {e}")
            return
            
        logger.info(f"Пользователь {user.id} вернулся в главное меню")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений для Gemini консультации через OpenRouter"""
        user_message = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"Пользователь {user_id} отправил сообщение: {user_message[:50]}...")
        
        # Проверяем, ожидает ли пользователь ввода email
        if user_id in self.email_waiting_users:
            await self.handle_email_input(update, user_message)
            return
        
        # Проверяем, является ли пользователь юристом
        if user_id in self.allowed_lawyers:
            # Обрабатываем сообщение как проверку кодового слова
            await self.handle_lawyer_message(update, user_message)
            return
        

        
        try:
            # Проверяем, есть ли токен OpenRouter
            if not self.openrouter_api_key:
                logger.error(f"OPENROUTER_API_KEY не найден для пользователя {user_id}")
                await update.message.reply_text(
                    self.error_messages['no_openai']
                )
                return
            
            logger.info(f"Отправляем запрос к Gemini через OpenRouter для пользователя {user_id}")
            
            # Получаем консультацию через OpenRouter
            try:
                ai_response = self.get_legal_advice_from_gemini(user_message)
                if ai_response:
                    logger.info(f"Получен ответ от Gemini для пользователя {user_id}: {ai_response[:100]}...")
                else:
                    logger.error(f"Не удалось получить ответ от Gemini для пользователя {user_id}")
                    ai_response = self.error_messages['processing_error']
            except Exception as gemini_error:
                # Если Gemini недоступен, отправляем сообщение об ошибке
                logger.error(f"Gemini через OpenRouter недоступен для пользователя {user_id}: {gemini_error}")
                ai_response = self.error_messages['processing_error']
            
            # Создаем кнопки для ответа ИИ
            keyboard = [
                [InlineKeyboardButton("🤖 ИИ консультация", callback_data="ai_consultation")],
                [InlineKeyboardButton("👨‍💼 Связаться с юристом", callback_data="real_lawyer")],
                [InlineKeyboardButton("ℹ️ О нас", callback_data="about")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Сохраняем ИИ консультацию в базу данных
            self.database.add_ai_consultation(user_id, user_message, ai_response)
            
            # Отправляем ответ пользователю с кнопками
            # Отключаем Markdown для ответов от Gemini, так как они могут содержать сложную разметку
            await update.message.reply_text(ai_response, reply_markup=reply_markup)
            logger.info(f"Gemini через OpenRouter ответил пользователю {user_id}")
            
        except Exception as e:
            logger.error(f"Общая ошибка при обработке Gemini консультации через OpenRouter для пользователя {user_id}: {e}")
            keyboard = [
                [InlineKeyboardButton("🤖 ИИ консультация", callback_data="ai_consultation")],
                [InlineKeyboardButton("👨‍💼 Связаться с юристом", callback_data="real_lawyer")],
                [InlineKeyboardButton("ℹ️ О нас", callback_data="about")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                self.error_messages['processing_error'],
                reply_markup=reply_markup
            )
    
    async def handle_email_input(self, update: Update, email: str):
        """Обработка ввода email для чека"""
        user_id = update.effective_user.id
        consultation_type = self.email_waiting_users.get(user_id, "oral")
        
        # Удаляем пользователя из ожидающих
        del self.email_waiting_users[user_id]
        
        # Проверяем корректность email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            keyboard = [
                [InlineKeyboardButton("📧 Попробовать снова", callback_data=f"enter_email_{consultation_type}")],
                [InlineKeyboardButton("🚫 Без чека", callback_data=f"no_receipt_{consultation_type}")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ Неверный формат email: {email}\n\n"
                f"💡 Примеры корректных email:\n"
                f"• example@mail.ru\n"
                f"• user@gmail.com\n"
                f"• test@yandex.ru\n\n"
                f"Попробуйте еще раз или выберите 'Без чека'",
                reply_markup=reply_markup
            )
            return
        
        # Сохраняем email пользователя
        self.user_emails[user_id] = email
        
        # Создаем платеж с email
        payment_info = self.payment_handler.create_payment(consultation_type, user_id, email)
        
        if payment_info["success"]:
            try:
                # Сохраняем email в базу данных сразу после создания платежа
                self.database.add_consultation(
                    user_id=user_id,
                    consultation_type=consultation_type,
                    amount=payment_info["amount"],
                    payment_id=payment_info["payment_id"],
                    code_word="ЮРИСТ2024",
                    email=email
                )
                
                # Создаем клавиатуру с кнопкой для оплаты
                keyboard = [
                    [InlineKeyboardButton("💳 Оплатить", url=payment_info["confirmation_url"])],
                    [InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_payment_{payment_info['payment_id']}")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message_text = (
                    f"💳 Оплата {payment_info['title']}\n\n"
                    f"💰 Сумма: {payment_info['amount']}₽\n"
                    f"📝 Описание: {payment_info['description']}\n"
                    f"📧 Email для чека: {email}\n\n"
                    f"✅ Чек будет отправлен на указанный email\n\n"
                    f"Для оплаты нажмите кнопку ниже 👇"
                )
                
                await update.message.reply_text(message_text, reply_markup=reply_markup)
                
                logger.info(f"Пользователь {user_id} создал платеж {payment_info['payment_id']} для {consultation_type} консультации с email {email}")
                
            except Exception as e:
                logger.error(f"Ошибка отправки платежа: {e}")
                error_message = "❌ Ошибка создания платежа. Попробуйте позже."
                await update.message.reply_text(error_message)
        else:
            error_message = f"❌ Ошибка создания платежа: {payment_info.get('error', 'Неизвестная ошибка')}"
            await update.message.reply_text(error_message)
            logger.error(f"Ошибка создания платежа для пользователя {user_id}: {payment_info.get('error')}")
    
    async def handle_lawyer_message(self, update: Update, message_text: str):
        """Обработка сообщений от юристов для проверки кодовых слов"""
        user_id = update.effective_user.id
        
        logger.info(f"Получено сообщение от юриста {user_id}: {message_text[:50]}...")
        
        # Ищем кодовое слово в сообщении
        import re
        code_word_match = re.search(r'ЮРИСТ2024', message_text, re.IGNORECASE)
        
        if code_word_match:
            # Ищем Telegram ID в сообщении
            telegram_id_match = re.search(r'(\d{8,})', message_text)
            
            if telegram_id_match:
                client_telegram_id = int(telegram_id_match.group(1))
                await self.verify_code_word_for_lawyer(update, client_telegram_id, "ЮРИСТ2024")
            else:
                await update.message.reply_text(
                    "❌ Кодовое слово найдено, но не найден Telegram ID клиента\n\n"
                    "Пожалуйста, убедитесь, что в сообщении указан Telegram ID клиента.\n"
                    "Пример: 'Клиент говорит кодовое слово ЮРИСТ2024, его ID: 123456789'\n\n"
                    "Или используйте команду: /check 123456789 ЮРИСТ2024"
                )
        else:
            # Если кодовое слово не найдено, предлагаем помощь
            await update.message.reply_text(
                "💡 Как использовать бота для проверки кодовых слов:\n\n"
                "1. Перешлите сообщение от клиента с кодовым словом\n"
                "2. Или напишите сообщение в формате:\n"
                "   'Клиент ID: 123456789, код: ЮРИСТ2024'\n"
                "3. Или используйте команду:\n"
                "   /check 123456789 ЮРИСТ2024\n\n"
                "Бот автоматически проверит кодовое слово и покажет информацию о клиенте."
            )
    
    async def _handle_lawyer_client_message(self, event):
        """Обработка сообщений для клиента юриста (только личные сообщения)"""
        if not self.lawyer_client_enabled:
            return
        
        # Проверяем, что это личное сообщение
        if not event.is_private:
            logger.debug(f"Пропускаем сообщение из чата (не личное): {event.chat_id}")
            return
        
        sender = await event.get_sender()
        message_text = event.text
        
        # Проверяем, что сообщение не от самого юриста
        me = await self.lawyer_client.get_me()
        if sender.id == me.id:
            logger.debug(f"Пропускаем собственное сообщение от юриста")
            return
        
        logger.info(f"Личное сообщение от {sender.id} (@{sender.username}): {message_text[:100]}...")
        
        # Ищем кодовое слово в сообщении (в любом месте)
        code_match = re.search(r'ЮРИСТ2024', message_text, re.IGNORECASE)
        
        # Если кодового слова нет, не отвечаем
        if not code_match:
            logger.debug(f"Кодовое слово не найдено в сообщении от {sender.id}, пропускаем")
            return
        
        # Ищем Telegram ID в сообщении (в любом месте)
        id_match = re.search(r'(\d{8,})', message_text)
        
        if not id_match:
            await event.reply(
                "❌ Не найден Telegram ID в сообщении.\n\n"
                "Пожалуйста, укажите ваш ID в любом месте сообщения."
            )
            return
        
        client_id = int(id_match.group(1))
        
        # Проверяем оплату
        payment_info = self._check_lawyer_payment(client_id)
        
        if not payment_info:
            await event.reply(
                "❌ Вы не оплатили консультацию.\n\n"
                "Оплатите консультацию через бота и попробуйте снова."
            )
            return
        
        # Получаем информацию о пользователе
        user_info = self._get_lawyer_user_info(client_id)
        
        # Формируем простой ответ
        response = f"Здравствуйте!\n\n"
        response += f"✅ Оплата подтверждена!\n\n"
        response += f"Можете задать ваш вопрос."
        

        
        await event.reply(response)
        
        # Сохраняем информацию о клиенте
        self.lawyer_data["clients"][str(client_id)] = {
            "user_info": user_info,
            "payment_info": payment_info,
            "last_contact": datetime.now().isoformat(),
            "sender_id": sender.id,
            "sender_username": sender.username
        }
        self._save_lawyer_data()
    
    async def _handle_lawyer_client_command(self, event):
        """Обработка команд для клиента юриста (только личные сообщения)"""
        if not self.lawyer_client_enabled:
            return
        
        # Проверяем, что это личное сообщение
        if not event.is_private:
            logger.debug(f"Пропускаем команду из чата (не личное): {event.chat_id}")
            return
        
        sender = await event.get_sender()
        
        # Проверяем, что команда не от самого юриста
        me = await self.lawyer_client.get_me()
        if sender.id == me.id:
            logger.debug(f"Пропускаем собственную команду от юриста")
            return
        
        command = event.text.lower()
        
        if command == "/start":
            await event.reply(
                "👨‍💼 Добро пожаловать!\n\n"
                "Напишите ваш ID и кодовое слово ЮРИСТ2024.\n"
                "Пример: 123456789 ЮРИСТ2024\n\n"
                "Команды:\n"
                "/help - Инструкция\n"
                "/stats - Статистика"
            )
        
        elif command == "/help":
            await event.reply(
                "📋 Инструкция:\n\n"
                "Клиент пишет: ID + ЮРИСТ2024\n"
                "Система проверяет оплату\n"
                "Если оплачено - можете консультировать\n\n"
                "Пример: 123456789 ЮРИСТ2024"
            )
        
        elif command == "/stats":
            if not self.lawyer_data["clients"]:
                await event.reply("📊 Статистика пуста - нет активных клиентов")
                return
            
            stats_text = "📊 Статистика активных клиентов:\n\n"
            
            for client_id, data in self.lawyer_data["clients"].items():
                user_info = data.get("user_info", {})
                payment_info = data.get("payment_info", {})
                last_contact = data.get("last_contact", "")
                
                stats_text += f"👤 {user_info.get('first_name', '')} {user_info.get('last_name', '')}\n"
                stats_text += f"🆔 ID: {client_id}\n"
                stats_text += f"💰 Оплата: {payment_info.get('amount', 0)}₽\n"
                stats_text += f"📅 Последний контакт: {last_contact[:10]}\n\n"
            
            await event.reply(stats_text)
    
    async def _start_lawyer_client(self):
        """Запуск клиента юриста"""
        if not self.lawyer_client_enabled or not TELETHON_AVAILABLE:
            logger.info("Клиент юриста отключен (LAWYER_CLIENT_ENABLED=false или Telethon недоступен)")
            return
        
        try:
            session_string = self._load_lawyer_session()
            if not session_string:
                logger.warning("❌ Нет сохраненной сессии юриста. Клиент юриста не запущен.")
                logger.info("💡 Для запуска клиента юриста выполните вход в Telegram при следующем запуске")
                return
            
            # Создаем клиент
            self.lawyer_client = TelegramClient(
                StringSession(session_string),
                self.lawyer_api_id,
                self.lawyer_api_hash
            )
            
            # Подключаемся
            await self.lawyer_client.connect()
            
            if not await self.lawyer_client.is_user_authorized():
                logger.error("❌ Сессия юриста недействительна. Клиент юриста не запущен.")
                logger.info("💡 Удалите файл veretenov_session.txt и перезапустите бота для повторной авторизации")
                return
            
            me = await self.lawyer_client.get_me()
            logger.info(f"✅ Клиент юриста подключен как: {me.first_name} (@{me.username})")
            
            # Регистрируем обработчики только для личных сообщений
            @self.lawyer_client.on(events.NewMessage(pattern=r'^/', func=lambda e: e.is_private))
            async def command_handler(event):
                await self._handle_lawyer_client_command(event)
            
            @self.lawyer_client.on(events.NewMessage(func=lambda e: not e.text.startswith('/') and e.is_private))
            async def message_handler(event):
                await self._handle_lawyer_client_message(event)
            
            logger.info("🤖 Клиент юриста запущен и готов к работе (только личные сообщения с кодовым словом)")
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска клиента юриста: {e}")
            logger.info("💡 Клиент юриста будет работать в режиме бота через команды /check")
    
    async def run_async(self):
        """Асинхронный запуск бота и клиента юриста"""
        logger.info("Бот запускается...")
        
        # Проверяем и создаем сессию Telegram при запуске
        logger.info("🔐 Проверка сессии Telegram...")
        session_ready = await self.session_manager.ensure_session()
        
        if session_ready:
            logger.info("✅ Сессия Telegram готова")
        else:
            logger.warning("⚠️ Сессия Telegram не создана, клиент юриста будет работать в режиме бота")
        
        # Запускаем клиент юриста в отдельной задаче
        lawyer_task = None
        if self.lawyer_client_enabled:
            lawyer_task = asyncio.create_task(self._start_lawyer_client())
        
        try:
            logger.info("Запуск polling...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Ждем завершения
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Ошибка при запуске polling: {e}")
        finally:
            # Останавливаем клиент юриста
            if lawyer_task:
                lawyer_task.cancel()
                try:
                    await lawyer_task
                except asyncio.CancelledError:
                    pass
            
            # Закрываем приложение
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            
            # Закрываем соединение с базой данных
            if hasattr(self, 'database'):
                logger.info("Закрытие соединения с базой данных...")
                self.database.close()
            logger.info("Бот остановлен")
    
    def run(self):
        """Запуск бота (синхронная обертка)"""
        asyncio.run(self.run_async())

if __name__ == "__main__":
    try:
        logger.info("Инициализация бота...")
        bot = LegalBot()
        logger.info("Бот инициализирован, запуск...")
        bot.run()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"Критическая ошибка запуска бота: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
