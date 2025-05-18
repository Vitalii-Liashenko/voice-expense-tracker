"""
Простий скрипт для перевірки налаштування бази даних.
"""
import os
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Виводимо інформацію про налаштування бази даних
print("Налаштування бази даних:")
print(f"- Хост: {DB_HOST}")
print(f"- Порт: {DB_PORT}")
print(f"- База даних: {DB_NAME}")
print(f"- Користувач: {DB_USER}")
print(f"- Пароль: {'*' * len(DB_PASSWORD) if DB_PASSWORD else 'не вказано'}")

# Перевіряємо з'єднання з базою даних
print("\nПеревірка з'єднання з базою даних...")
from db.database import engine
try:
    connection = engine.connect()
    print("✓ З'єднання з базою даних встановлено успішно!")
    connection.close()
except Exception as e:
    print(f"✗ Помилка з'єднання з базою даних: {e}")
    exit(1)

# Створюємо таблиці
print("\nСтворення таблиць...")
from db.database import init_db
try:
    from db.models import Base
    Base.metadata.create_all(bind=engine)
    print("✓ Таблиці успішно створено!")
except Exception as e:
    print(f"✗ Помилка створення таблиць: {e}")
    exit(1)

# Перевіряємо створення сесії
print("\nСтворення сесії бази даних...")
from db.database import get_db_session
try:
    db = get_db_session()
    print("✓ Сесія створена успішно!")
except Exception as e:
    print(f"✗ Помилка створення сесії: {e}")
    exit(1)

# Заповнюємо тестовими даними
print("\nЗаповнення бази тестовими даними...")
from db.queries import seed_test_data
try:
    # Використовуємо тестовий ID користувача
    test_user_id = 123456789
    seed_test_data(db, test_user_id)
    print("✓ Тестові дані успішно додано!")
except Exception as e:
    print(f"✗ Помилка заповнення тестовими даними: {e}")
    exit(1)

# Перевіряємо ліміти
print("\nПеревірка лімітів бюджету...")
from db.queries import get_all_limits
try:
    limits = get_all_limits(db, test_user_id)
    print(f"✓ Знайдено {len(limits)} лімітів:")
    for limit in limits:
        print(f"  - {limit.category}: {float(limit.limit_amount)} грн")
except Exception as e:
    print(f"✗ Помилка отримання лімітів: {e}")

# Перевіряємо тестові витрати
print("\nПеревірка тестових витрат...")
from db.queries import get_expenses_by_period
from datetime import datetime, timedelta
try:
    # Отримуємо витрати за останні 2 місяці
    start_date = datetime.now() - timedelta(days=60)
    expenses = get_expenses_by_period(db, test_user_id, start_date)
    print(f"✓ Знайдено {len(expenses)} витрат:")
    for exp in expenses:
        print(f"  - {exp.category}: {float(exp.amount)} грн - {exp.description}")
except Exception as e:
    print(f"✗ Помилка отримання витрат: {e}")

db.close()
print("\n✓ Перевірка бази даних завершена успішно!")
