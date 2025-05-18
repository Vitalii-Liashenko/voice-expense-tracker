"""
Обробники команд та повідомлень для Telegram бота.
"""
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from db.database import get_db_session
from db.queries import seed_test_data, check_budget_limit, get_remaining_budget
from ai_agent.intent_classifier import classify_intent
from ai_agent.expense_parser import parse_expense
from ai_agent.analytics_agent import generate_analytics
from config import AUTHOR_USER_ID

AUTHOR_USER_ID = AUTHOR_USER_ID

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /start."""
    user_id = update.effective_user.id
    
    # Перевірка авторизації
    if user_id != AUTHOR_USER_ID:
        await update.message.reply_text(
            "Вибачте, але ви не маєте доступу до цього бота."
        )
        return
    
    # Ініціалізація бази даних з тестовими даними
    db = get_db_session()
    try:
        seed_test_data(db, user_id)
        await update.message.reply_text(
            "Привіт! Я - ваш AI-бухгалтер. Ви можете:\n"
            "- Відправляти голосові повідомлення про витрати\n"
            "- Запитувати аналітику витрат\n"
            "- Отримувати сповіщення про перевищення лімітів\n"
            "\n"
            "Спробуйте відправити голосове повідомлення з витратою, наприклад:\n"
            "'Купив продукти за 300 гривень'"
        )
    finally:
        db.close()

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /help."""
    await update.message.reply_text(
        "Доступні команди:\n"
        "/start - Почати роботу з ботом\n"
        "/help - Ця допомога\n\n"
        "Ви можете:\n"
        "- Відправляти голосові повідомлення про витрати\n"
        "- Запитувати аналітику витрат голосом або текстом\n"
        "- Отримувати сповіщення про перевищення лімітів"
    )

async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник голосових повідомлень."""
    user_id = update.effective_user.id
    
    # Перевірка авторизації
    if user_id != int(os.getenv("AUTHOR_USER_ID")):
        return
    
    # Отримання голосового повідомлення
    voice_file = await update.message.voice.get_file()
    
    # Тут буде інтеграція з Whisper API для транскрипції голосу
    # Поки що повертаємо повідомлення про отримання голосового повідомлення
    await update.message.reply_text(
        "Я отримав ваше голосове повідомлення."
    )

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник текстових повідомлень."""
    user_id = update.effective_user.id
    
    # Перевірка авторизації
    if user_id != AUTHOR_USER_ID:
        return
    
    message = update.message.text
    
    # Класифікація наміру
    intent = classify_intent(message)
    
    if intent == "expense":
        # Парсинг витрати
        expense = parse_expense(message)
        if expense:
            # Збереження витрати в базу даних
            db = get_db_session()
            try:
                # Тут буде збереження витрати
                # Поки що повертаємо повідомлення про успішне збереження
                await update.message.reply_text(
                    f"Збережено витрату: {expense['amount']} грн - {expense['category']}"
                )
            finally:
                db.close()
    elif intent == "analytics":
        # Генерація аналітики
        analytics = generate_analytics(message)
        await update.message.reply_text(
            analytics,
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            "Вибачте, я не розумію це запитання. Спробуйте спочатку записати витрату або запитати про аналітику."
        )
