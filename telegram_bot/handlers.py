"""
Обробники команд та повідомлень для Telegram бота.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from tools.transcriber import download_voice_message, transcribe_audio
from tools.translator import translate_to_english
from telegram_bot.message_processor import process_text_with_nlp

from db.database import get_db_session
from db.queries import seed_test_data
from tools.intent_classifier import classify_intent
from ai_agent.expenses_agent import parse_expense
from ai_agent.analytics_agent import generate_analytics
from config import AUTHOR_USER_ID

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
    if user_id != AUTHOR_USER_ID:
        return
    
    try:
        # Отримання голосового повідомлення
        voice_file = await update.message.voice.get_file()
        
        # Завантаження голосового повідомлення
        voice_path = await download_voice_message(voice_file)
        
        # Транскрипція голосового повідомлення
        transcribed_text = await transcribe_audio(voice_path)
        await update.message.reply_text(
            f"Отриманий текст: {transcribed_text}"
        )

        # Обробка повідомлення
        await process_text_with_nlp(update, transcribed_text)

    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await update.message.reply_text(
            "Вибачте, сталася помилка при обробці голосового повідомлення. Спробуйте ще раз."
        )

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник текстових повідомлень."""
    user_id = update.effective_user.id
    
    # Перевірка авторизації
    if user_id != AUTHOR_USER_ID:
        return
    
    try:
        message = update.message.text
        
        # Обробка повідомлення через message_processor
        await process_text_with_nlp(update, message)
        
    except Exception as e:
        logger.error(f"Error processing text message: {e}")
        await update.message.reply_text(
            "Вибачте, сталася помилка при обробці повідомлення. Спробуйте ще раз."
        )

