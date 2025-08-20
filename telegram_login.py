#!/usr/bin/env python3
"""
Скрипт для автоматического входа в Telegram аккаунт @narhipovd
Использует Telethon для работы с Telegram API
"""

import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
from loguru import logger

# Загружаем переменные окружения
load_dotenv()

class TelegramLogin:
    def __init__(self):
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.phone = os.getenv("TELEGRAM_PHONE")  # Номер телефона аккаунта @narhipovd
        self.session_file = "veretenov_session.txt"
        
    async def login(self):
        """Вход в аккаунт Telegram"""
        if not all([self.api_id, self.api_hash, self.phone]):
            logger.error("❌ Не все переменные окружения установлены")
            logger.error("Нужно установить: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
            return False
        
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
                code = input("📱 Введите код подтверждения из Telegram: ")
                
                try:
                    # Входим с кодом
                    await client.sign_in(self.phone, code)
                    logger.info("✅ Авторизация успешна!")
                except Exception as e:
                    # Если нужен пароль от двухфакторной аутентификации
                    if "2FA" in str(e) or "password" in str(e).lower():
                        password = input("🔒 Введите пароль от двухфакторной аутентификации: ")
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
            logger.error(f"❌ Ошибка входа: {e}")
            return False
    
    def load_session(self):
        """Загрузка сохраненной сессии"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            logger.error(f"Ошибка загрузки сессии: {e}")
        return None
    
    async def test_connection(self):
        """Тест подключения с сохраненной сессией"""
        session_string = self.load_session()
        if not session_string:
            logger.error("❌ Нет сохраненной сессии")
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
                logger.info(f"✅ Подключение успешно: {me.first_name} (@{me.username})")
                await client.disconnect()
                return True
            else:
                logger.error("❌ Сессия недействительна")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования подключения: {e}")
            return False

async def main():
    """Основная функция"""
    login_manager = TelegramLogin()
    
    print("🤖 Telegram Login Manager")
    print("=" * 40)
    
    # Проверяем существующую сессию
    if await login_manager.test_connection():
        print("✅ Сессия активна, повторный вход не требуется")
        return
    
    # Выполняем вход
    print("🔐 Выполняем вход в аккаунт...")
    if await login_manager.login():
        print("✅ Вход выполнен успешно!")
        print(f"📁 Сессия сохранена в {login_manager.session_file}")
    else:
        print("❌ Ошибка входа")

if __name__ == "__main__":
    asyncio.run(main())
