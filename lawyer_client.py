#!/usr/bin/env python3
"""
Скрипт для обработки личных сообщений на аккаунт юриста @narhipovd
Проверяет оплату консультаций и ведет диалог с клиентами
"""

import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import psycopg2
from psycopg2.extras import RealDictCursor
from loguru import logger

# Загружаем переменные окружения
load_dotenv()

class LawyerClient:
    def __init__(self):
        self.bot_token = os.getenv("LAWYER_BOT_TOKEN")  # Токен для аккаунта @narhipovd
        self.database_url = os.getenv("DATABASE_URL")
        self.session_file = "lawyer_session.json"
        self.connection = None
        self.connect_database()
        
        # Загружаем сохраненную сессию
        self.session_data = self.load_session()
        
    def connect_database(self):
        """Подключение к базе данных"""
        try:
            self.connection = psycopg2.connect(self.database_url)
            logger.info("✅ Подключение к базе данных установлено")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к базе данных: {e}")
            self.connection = None
    
    def load_session(self):
        """Загрузка сохраненной сессии"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки сессии: {e}")
        return {}
    
    def save_session(self):
        """Сохранение сессии"""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения сессии: {e}")
    
    def check_payment(self, user_id: int) -> dict:
        """
        Проверка оплаты консультации пользователем
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            dict: Информация о платеже или None
        """
        if not self.connection:
            return None
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
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
    
    def get_user_info(self, user_id: int) -> dict:
        """
        Получение информации о пользователе
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            dict: Информация о пользователе
        """
        if not self.connection:
            return None
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
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
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        logger.info(f"Команда /start от пользователя {user.id} (@{user.username})")
        
        await update.message.reply_text(
            "👨‍💼 Добро пожаловать!\n\n"
            "Напишите ваш ID и кодовое слово ЮРИСТ2024.\n"
            "Пример: 123456789 ЮРИСТ2024"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка входящих сообщений"""
        user = update.effective_user
        message_text = update.message.text
        
        logger.info(f"Сообщение от {user.id} (@{user.username}): {message_text[:100]}...")
        
        # Ищем Telegram ID в сообщении (в любом месте)
        import re
        id_match = re.search(r'(\d{8,})', message_text)
        code_match = re.search(r'ЮРИСТ2024', message_text, re.IGNORECASE)
        
        if not id_match:
            await update.message.reply_text(
                "❌ Не найден Telegram ID в сообщении.\n\n"
                "Пожалуйста, укажите ваш ID в любом месте сообщения."
            )
            return
        
        client_id = int(id_match.group(1))
        
        if not code_match:
            await update.message.reply_text(
                "❌ Не найдено кодовое слово ЮРИСТ2024.\n\n"
                "Пожалуйста, укажите кодовое слово в любом месте сообщения.\n"
                "Пример: Мой ID 123456789, код ЮРИСТ2024, вопрос: как расторгнуть договор?"
            )
            return
        
        # Проверяем оплату
        payment_info = self.check_payment(client_id)
        
        if not payment_info:
            await update.message.reply_text(
                "❌ Вы не оплатили консультацию.\n\n"
                "Оплатите консультацию через бота и попробуйте снова."
            )
            return
        
        # Получаем информацию о пользователе
        user_info = self.get_user_info(client_id)
        
        # Формируем простой ответ
        response = f"Здравствуйте!\n\n"
        response += f"✅ Оплата подтверждена!\n\n"
        response += f"Можете задать ваш вопрос."
        

        
        await update.message.reply_text(response)
        
        # Сохраняем информацию о клиенте в сессии
        self.session_data[str(client_id)] = {
            "user_info": user_info,
            "payment_info": payment_info,
            "last_contact": datetime.now().isoformat()
        }
        self.save_session()
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        await update.message.reply_text(
            "📋 Инструкция:\n\n"
            "Клиент пишет: ID + ЮРИСТ2024\n"
            "Система проверяет оплату\n"
            "Если оплачено - можете консультировать\n\n"
            "Пример: 123456789 ЮРИСТ2024"
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats - показывает статистику сессии"""
        if not self.session_data:
            await update.message.reply_text("📊 Статистика пуста - нет активных клиентов")
            return
        
        stats_text = "📊 Статистика активных клиентов:\n\n"
        
        for client_id, data in self.session_data.items():
            user_info = data.get("user_info", {})
            payment_info = data.get("payment_info", {})
            last_contact = data.get("last_contact", "")
            
            stats_text += f"👤 {user_info.get('first_name', '')} {user_info.get('last_name', '')}\n"
            stats_text += f"🆔 ID: {client_id}\n"
            stats_text += f"💰 Оплата: {payment_info.get('amount', 0)}₽\n"
            stats_text += f"📅 Последний контакт: {last_contact[:10]}\n\n"
        
        await update.message.reply_text(stats_text)
    
    def run(self):
        """Запуск бота"""
        if not self.bot_token:
            logger.error("❌ LAWYER_BOT_TOKEN не установлен в .env файле")
            return
        
        # Создаем приложение
        application = Application.builder().token(self.bot_token).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("🤖 Бот юриста запущен")
        
        # Запускаем бота
        application.run_polling()

if __name__ == "__main__":
    lawyer_client = LawyerClient()
    lawyer_client.run()
