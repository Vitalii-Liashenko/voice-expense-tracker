"""
Головний файл для налаштування та запуску Telegram бота.
"""
from telegram.ext import Application, CommandHandler, MessageHandler, filters, Updater
from telegram import Update
import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TELEGRAM_BOT_TOKEN, AUTHOR_USER_ID

# Отримуємо токен бота з конфігурації
TELEGRAM_TOKEN = TELEGRAM_BOT_TOKEN
AUTHOR_USER_ID = AUTHOR_USER_ID

async def start_handler(update, context):
    """Обробник команди /start."""
    await update.message.reply_text("Привіт! Я Voice Expense Tracker бот. Надішліть мені голосове повідомлення про ваші витрати.")

async def help_handler(update, context):
    """Обробник команди /help."""
    help_text = """
    Використання Voice Expense Tracker:
    
    /start - Початок роботи з ботом
    /help - Показати цю довідку
    
    Голосове повідомлення - надішліть аудіо з описом витрат
    Текстове повідомлення - введіть суму і опис витрат вручну
    """
    await update.message.reply_text(help_text)

async def voice_message_handler(update, context):
    """Обробник голосових повідомлень."""
    await update.message.reply_text("Отримано голосове повідомлення. Обробка...")
    # Тут буде логіка обробки голосових повідомлень

async def text_message_handler(update, context):
    """Обробник текстових повідомлень."""
    await update.message.reply_text("Отримано текстове повідомлення. Обробка...")
    # Тут буде логіка обробки текстових повідомлень

async def error_handler(update, context):
    """Обробка помилок."""
    print(f"Error: {context.error}")
    await context.bot.send_message(
        chat_id=AUTHOR_USER_ID,
        text="Вибачте, сталася помилка. Спробуйте ще раз."
    )

def setup_bot():
    """Налаштування бота."""
    # Створюємо додаток
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Додаємо обробники
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(MessageHandler(filters.VOICE, voice_message_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    
    # Додаємо обробник помилок
    application.add_error_handler(error_handler)
    
    return application

def start_bot():
    """Запуск бота."""
    application = setup_bot()
    
    # Пускаємо бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    start_bot()
