"""
Тестовий скрипт для перевірки роботи бази даних.
"""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Завантаження змінних оточення
load_dotenv()

# Імпорт наших модулів
from db.database import init_db, get_db_session, engine
from db.models import Base, Expense, BudgetLimit
from db.queries import (
    seed_test_data,
    get_all_limits,
    get_expenses_by_category,
    get_expenses_by_period,
    get_expense_sum_by_category,
    check_budget_limit,
    get_remaining_budget,
    save_expense
)

def main():
    """
    Головна функція для тестування бази даних.
    """
    print("Тестування модуля бази даних Voice Expense Tracker")
    print("-" * 50)
    
    # Створення таблиць
    print("Створення таблиць бази даних...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Таблиці успішно створено.")
    
    # Створення сесії
    db = get_db_session()
    
    # Тестовий користувач
    test_user_id = 123456789
    
    # Заповнення тестовими даними
    print("\nЗаповнення бази даних тестовими даними...")
    seed_test_data(db, test_user_id)
    print("Тестові дані додано.")
    
    # Перевірка лімітів
    print("\nПеревірка лімітів бюджету:")
    limits = get_all_limits(db, test_user_id)
    print(f"Знайдено {len(limits)} лімітів:")
    for limit in limits:
        print(f"- {limit.category}: {float(limit.limit_amount)} грн")
    
    # Перевірка витрат за категоріями
    print("\nПеревірка витрат за категоріями:")
    categories = ["Foods", "Transportation", "Entertainment", "Housing"]
    
    for category in categories:
        expenses = get_expenses_by_category(db, test_user_id, category)
        if expenses:
            print(f"Категорія '{category}':")
            for exp in expenses:
                print(f"  - {exp.description}: {float(exp.amount)} грн ({exp.created_at.strftime('%d.%m.%Y')})")
        else:
            print(f"Категорія '{category}': витрат не знайдено")
    
    # Додавання нової витрати
    print("\nДодавання нової витрати...")
    new_expense = save_expense(
        db, 
        test_user_id, 
        "Entertainment", 
        1200.0, 
        "Квитки в театр", 
        "Купив квитки в театр за 1200 гривень"
    )
    print(f"Додано нову витрату: {new_expense.description} на суму {float(new_expense.amount)} грн")
    
    # Перевірка лімітів після додавання
    category = "Entertainment"
    total = get_expense_sum_by_category(db, test_user_id, category)
    print(f"\nЗагальна сума витрат у категорії '{category}': {total} грн")
    
    is_over, remaining = check_budget_limit(db, test_user_id, category, 5000.0)
    if is_over:
        print(f"Нова витрата на 5000 грн перевищить ліміт у категорії '{category}'")
        if remaining is not None:
            print(f"Перевищення: {abs(remaining)} грн")
    else:
        print(f"Ліміт у категорії '{category}' не буде перевищено")
        if remaining is not None:
            print(f"Залишок: {remaining} грн")
    
    print("\nТестування завершено!")

if __name__ == "__main__":
    main()
