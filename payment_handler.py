import os
import uuid
from datetime import datetime
from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from yookassa import Configuration, Payment
from yookassa.domain.request import PaymentRequest


class PaymentHandler:
    def __init__(self):
        # Настройка ЮKassa
        self.shop_id = os.getenv("YOOKASSA_SHOP_ID")
        self.secret_key = os.getenv("YOOKASSA_SECRET_KEY")
        
        if not self.shop_id or not self.secret_key:
            logger.warning("YOOKASSA_SHOP_ID или YOOKASSA_SECRET_KEY не настроены")
        else:
            Configuration.account_id = self.shop_id
            Configuration.secret_key = self.secret_key
            logger.info("ЮKassa настроена успешно")
        
        # Цены консультаций в рублях (увеличены на 5%)
        self.oral_consultation_price = 3150.0  # 3000 + 5% = 3150 руб
        self.full_consultation_price = 13650.0  # 13000 + 5% = 13650 руб
    
    def create_payment(self, consultation_type: str = "oral", user_id: int = None, user_email: str = None) -> dict:
        """
        Создание платежа через ЮKassa
        
        Args:
            consultation_type: Тип консультации (oral/full)
            user_id: ID пользователя Telegram
            
        Returns:
            dict: Информация о платеже
        """
        try:
            if not self.shop_id or not self.secret_key:
                logger.error("ЮKassa не настроена")
                return {
                    "success": False,
                    "error": "ЮKassa не настроена"
                }
            
            logger.info(f"Создание платежа для {consultation_type} консультации")
            
            # Выбираем цену в зависимости от типа консультации
            if consultation_type == "full":
                amount = self.full_consultation_price
                title = "Полная консультация с изучением документов"
                description = "Полная юридическая консультация с изучением и анализом документов"
            else:
                amount = self.oral_consultation_price
                title = "Устная консультация"
                description = "Устная юридическая консультация с профессиональным юристом"
            
            # Создаем уникальный ID платежа
            payment_id = str(uuid.uuid4())
            
            # Создаем платеж в ЮKassa
            payment_request = PaymentRequest(
                amount={
                    "value": str(amount),
                    "currency": "RUB"
                },
                confirmation={
                    "type": "redirect",
                    "return_url": "https://t.me/your_bot_username"  # Замените на username вашего бота
                },
                capture=True,
                description=description,
                receipt={
                    "customer": {
                        "email": user_email or "client@example.com"  # Используем email пользователя или дефолтный
                    },
                    "items": [
                        {
                            "description": title,
                            "quantity": "1",
                            "amount": {
                                "value": str(amount),
                                "currency": "RUB"
                            },
                            "vat_code": "1",  # Код НДС (1 = без НДС)
                            "payment_subject": "service",  # Тип товара/услуги
                            "payment_mode": "full_payment"  # Тип платежа
                        }
                    ]
                },
                metadata={
                    "consultation_type": consultation_type,
                    "user_id": str(user_id) if user_id else "",
                    "payment_id": payment_id
                }
            )
            
            # Создаем платеж
            payment = Payment.create(payment_request)
            
            logger.info(f"Платеж создан: {payment.id}")
            
            return {
                "success": True,
                "payment_id": payment.id,
                "confirmation_url": payment.confirmation.confirmation_url,
                "amount": amount,
                "title": title,
                "description": description,
                "consultation_type": consultation_type,
                "status": payment.status
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания платежа: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_payment_status(self, payment_id: str) -> dict:
        """
        Проверка статуса платежа
        
        Args:
            payment_id: ID платежа в ЮKassa
            
        Returns:
            dict: Информация о статусе платежа
        """
        try:
            if not self.shop_id or not self.secret_key:
                logger.error("ЮKassa не настроена")
                return {
                    "success": False,
                    "error": "ЮKassa не настроена"
                }
            
            payment = Payment.find_one(payment_id)
            
            return {
                "success": True,
                "payment_id": payment.id,
                "status": payment.status,
                "amount": float(payment.amount.value),
                "currency": payment.amount.currency,
                "paid": payment.paid,
                "metadata": payment.metadata
            }
            
        except Exception as e:
            logger.error(f"Ошибка проверки статуса платежа: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_consultation_price_rub(self, consultation_type: str = "oral") -> float:
        """
        Получение цены консультации в рублях
        
        Args:
            consultation_type: Тип консультации (oral/full)
            
        Returns:
            float: Цена консультации в рублях
        """
        if consultation_type == "full":
            return self.full_consultation_price
        else:
            return self.oral_consultation_price
    
    def create_consultation_keyboard(self) -> InlineKeyboardMarkup:
        """
        Создание клавиатуры выбора типа консультации
        
        Returns:
            InlineKeyboardMarkup: Клавиатура с вариантами консультации
        """
        keyboard = [
            [InlineKeyboardButton("💬 Устная консультация (3150₽)", callback_data="pay_oral_consultation")],
            [InlineKeyboardButton("📋 Полная консультация с изучением документов (13650₽)", callback_data="pay_full_consultation")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_consultation_message(self) -> str:
        """
        Формирование сообщения о выборе типа консультации
        
        Returns:
            str: Текст сообщения
        """
        return (
            "👨‍💼 Консультация с юристом\n\n"
            "Выберите тип консультации:\n\n"
            "💬 Устная консультация (3150₽)\n"
            "• Устная юридическая консультация\n"
            "• Общие правовые рекомендации\n"
            "• Ответы на вопросы\n"
            "• Поддержка в течение 24 часов\n\n"
            "📋 Полная консультация с изучением документов (13650₽)\n"
            "• Детальный анализ документов\n"
            "• Письменные правовые заключения\n"
            "• Стратегия решения проблемы\n"
            "• Подготовка документов\n"
            "• Поддержка в течение 7 дней"
        )
    
    def is_payment_successful(self, status: str) -> bool:
        """
        Проверка успешности платежа
        
        Args:
            status: Статус платежа
            
        Returns:
            bool: True если платеж успешен
        """
        return status == "succeeded"
    
    def get_consultation_price(self) -> float:
        """
        Получение цены консультации
        
        Returns:
            float: Цена консультации
        """
        return 12.5
    
    def create_receipt(self, payment_id: str, user_email: str = None, user_phone: str = None) -> dict:
        """
        Проверка создания чека через ЮKassa
        
        Args:
            payment_id: ID платежа
            user_email: Email пользователя (опционально)
            user_phone: Телефон пользователя (опционально)
            
        Returns:
            dict: Результат проверки чека
        """
        try:
            if not self.shop_id or not self.secret_key:
                logger.error("ЮKassa не настроена для проверки чека")
                return {
                    "success": False,
                    "error": "ЮKassa не настроена"
                }
            
            # Получаем информацию о платеже
            payment = Payment.find_one(payment_id)
            if not payment:
                logger.error(f"Платеж {payment_id} не найден")
                return {
                    "success": False,
                    "error": "Платеж не найден"
                }
            
            # Проверяем, что платеж успешен
            if payment.status != "succeeded":
                logger.warning(f"Платеж {payment_id} не оплачен (статус: {payment.status})")
                return {
                    "success": False,
                    "error": "Платеж не оплачен"
                }
            
            # Чек создается автоматически при создании платежа с receipt
            logger.info(f"Чек для платежа {payment_id} создан автоматически при оплате")
            
            return {
                "success": True,
                "receipt_id": payment_id,
                "status": "succeeded",
                "message": "Чек отправлен на email автоматически"
            }
            
        except Exception as e:
            logger.error(f"Ошибка проверки чека для платежа {payment_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            } 