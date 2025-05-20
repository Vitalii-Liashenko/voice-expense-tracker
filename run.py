"""
Voice Expense Tracker - main startup file

This file launches the Telegram bot for expense tracking using voice messages.
"""
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """
    Main bot startup function.
    
    1. Checks for required environment variables
    2. Loads configuration
    3. Launches Telegram bot
    """
    logger.info("Starting Voice Expense Tracker")
    
    # Environment variables are already loaded in config.py, so we don't call load_dotenv() again
    # Import config to ensure environment variables are loaded
    import config
    
    # Check for required API keys
    required_env_vars = [
        "TELEGRAM_BOT_TOKEN",
        "AUTHOR_USER_ID",
        "OPENAI_API_KEY",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please add them to the .env.local file")
        sys.exit(1)
    
    # Import bot module
    from telegram_bot.bot import run_bot
    
    # Start the bot
    try:
        logger.info("Starting the bot...")
        run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting the bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 