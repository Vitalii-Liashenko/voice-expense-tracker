"""
Module for coordinating message processing and NLP tasks.
"""
import logging
from telegram import Update
from telegram.constants import ParseMode

from tools.intent_classifier import classify_intent
from ai_agent.expenses_agent import parse_expense, save_expenses
from ai_agent.analytics_agent import generate_analytics
from tools.translator import translate_to_english

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def process_text_with_nlp(update: Update, text: str):
    """
    Process text message using NLP pipeline.
    
    1. Intent classification
    2. Recognize expense or generate analytics
    3. Save expense or send analytics to user
    
    Args:
        update: Telegram message object
        text: Text to process
    """
    user_id = update.effective_user.id
    # Переклад на англійську
    translated_text = translate_to_english(text)
    if not translated_text:
        logger.error("Failed to translate text")
        await update.message.reply_text(
            "Вибачте, щось пішло не так. Повторіть, будь ласка."
        )
        return
    
    # 1. Intent classification
    logger.info(f"Classifying intent: '{translated_text}'")
    intent = classify_intent(translated_text)
    logger.info(f"Recognized intent: {intent}")
    
    if intent == "expense":
        # 2. Parse expense
        logger.info("Processing as expense")
        expense = parse_expense(translated_text)
        
        if expense:
            message = save_expenses(expense, user_id, translated_text)
            await update.message.reply_text(message, parse_mode=ParseMode.HTML)    
        else:
            await update.message.reply_text(
                "Не вдалося розпізнати витрату. "
                "Будь ласка, вкажіть суму та опис."
            )
    elif intent == "analytics":
        # 2. Generate analytics
        logger.info("Processing as analytics request")
        try:
            analytics_response = generate_analytics(translated_text)
            await update.message.reply_text(analytics_response, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            await update.message.reply_text(
                "Вибачте, сталася помилка при обробці вашого запиту на аналітику. Спробуйте ще раз."
            )
    else:
        # Unknown intent
        logger.info("Unknown intent")
        await update.message.reply_text(
            "Вибачте, я не зміг розібрати ваше повідомлення. Ви можете:\n"
            "- Зареєструвати витрату (наприклад, 'Купив продукти за 300 гривень')\n"
            "- Запитати аналітику (наприклад, 'Скільки я витратив на їжу цього місяця?')"
        ) 