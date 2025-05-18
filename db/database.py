"""
Database connection setup for Voice Expense Tracker.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Перевірка необхідних параметрів
required_params = {
    'DB_HOST': DB_HOST,
    'DB_PORT': DB_PORT,
    'DB_NAME': DB_NAME,
    'DB_USER': DB_USER,
    'DB_PASSWORD': DB_PASSWORD
}

for param_name, value in required_params.items():
    if not value:
        raise ValueError(f"Помилка: не встановлено {param_name} у файлі .env.local")

# Рядок підключення до бази даних
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Створення движка бази даних
engine = create_engine(DATABASE_URL)

# Створення сесії
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас для моделей
Base = declarative_base()

def get_db_session():
    """
    Створює сесію для взаємодії з базою даних.
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def init_db():
    """
    Ініціалізує базу даних, створює таблиці.
    """
    from db.models import Base
    Base.metadata.create_all(bind=engine)
