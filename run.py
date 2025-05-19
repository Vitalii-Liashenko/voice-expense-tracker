"""
Voice Expense Tracker - головний файл запуску

Цей файл запускає Telegram бота для відстеження витрат за допомогою голосових повідомлень.
"""
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """
    Головна функція запуску бота.
    
    1. Перевіряє наявність необхідних змінних середовища
    2. Завантажує конфігурацію
    3. Запускає Telegram бота
    """
    logger.info("Запуск Voice Expense Tracker")
    
    # Змінні середовища вже завантажені в config.py, тому повторно не викликаємо load_dotenv()
    # Імпортуємо config, щоб переконатися, що змінні середовища завантажені
    import config
    
    # Перевіряємо наявність необхідних API ключів
    required_env_vars = [
        "TELEGRAM_BOT_TOKEN",
        "AUTHOR_USER_ID",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Відсутні необхідні змінні середовища: {', '.join(missing_vars)}")
        logger.error("Будь ласка, додайте їх у файл .env.local")
        sys.exit(1)
    
    # Імпортуємо модуль бота
    from telegram_bot.bot import run_bot
    
    # Запускаємо бота
    try:
        logger.info("Запускаємо бота...")
        run_bot()
    except KeyboardInterrupt:
        logger.info("Бот зупинений користувачем")
    except Exception as e:
        logger.error(f"Помилка при запуску бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 