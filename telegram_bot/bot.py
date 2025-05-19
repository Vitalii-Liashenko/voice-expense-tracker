"""
Головний файл для налаштування та запуску Telegram бота.
"""
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import BotCommand
import sys
import os
import logging

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TELEGRAM_BOT_TOKEN, AUTHOR_USER_ID
from telegram_bot.handlers import (
    start_handler,
    help_handler,
    voice_message_handler,
    text_message_handler
)

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Отримуємо токен бота з конфігурації
TELEGRAM_TOKEN = TELEGRAM_BOT_TOKEN

async def error_handler(update, context):
    """Обробник помилок."""
    logger.error(f"Сталася помилка при обробці оновлення: {context.error}")

async def setup_commands(application):
    """Налаштування команд бота для меню."""
    commands = [
        BotCommand("start", "Почати роботу з ботом"),
        BotCommand("help", "Показати довідку")
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Команди бота налаштовано")

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
    
    # Налаштовуємо команди бота
    application.post_init = setup_commands
    
    logger.info("Бота налаштовано")
    return application

def run_bot():
    """Запуск бота."""
    logger.info("Запускаємо бота...")
    application = setup_bot()
    application.run_polling()
    logger.info("Бот зупинений")

if __name__ == "__main__":
    run_bot()
