from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables
load_dotenv(dotenv_path=".env.local")

# Project root directory
ROOT_DIR = Path(__file__).parent

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "voice_expense_tracker")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Telegram bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHOR_USER_ID = int(os.getenv("AUTHOR_USER_ID"))

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Anthropic configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Budget limits (in Ukrainian hryvnia)
DEFAULT_BUDGET_LIMITS = {
    "Foods": 2000,
    "Shopping": 1500,
    "Housing": 3000,
    "Transportation": 1000,
    "Entertainment": 1000,
    "Others": 1000
}

# Expense categories (in Ukrainian)
EXPENSE_CATEGORIES = [
    "Foods",  # Харчування
    "Shopping",  # Покупки
    "Housing",  # Житло
    "Transportation",  # Транспорт
    "Entertainment",  # Розваги
    "Others"  # Інше
]
