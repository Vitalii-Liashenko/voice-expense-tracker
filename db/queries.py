"""
CRUD операції для роботи з базою даних Voice Expense Tracker.
"""
from sqlalchemy.orm import Session
from sqlalchemy import extract, func, and_
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple

from db.models import Expense, BudgetLimit

# Операції з витратами
def save_expense(
    db: Session,
    user_id: int,
    category: str,
    amount: float,
    description: str,
    transcript: str
) -> Expense:
    """
    Зберігає нову витрату у базу даних.
    
    Args:
        db: Сесія бази даних
        user_id: ID користувача в Telegram
        category: Категорія витрати (одна з фіксованих)
        amount: Сума витрати
        description: Опис витрати
        transcript: Оригінальний текст з голосового повідомлення
        
    Returns:
        Об'єкт витрати
    """
    expense = Expense(
        user_id=user_id,
        category=category,
        amount=amount,
        description=description,
        transcript=transcript
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense

def get_expenses_by_category(
    db: Session,
    user_id: int,
    category: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Expense]:
    """
    Отримує витрати користувача за категорією.
    
    Args:
        db: Сесія бази даних
        user_id: ID користувача в Telegram
        category: Категорія витрати
        start_date: Початкова дата для фільтрації
        end_date: Кінцева дата для фільтрації
        
    Returns:
        Список витрат
    """
    query = db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.category == category
    )
    
    if start_date:
        query = query.filter(Expense.created_at >= start_date)
    if end_date:
        query = query.filter(Expense.created_at <= end_date)
    
    return query.all()

def get_expenses_by_period(
    db: Session,
    user_id: int,
    start_date: datetime,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None
) -> List[Expense]:
    """
    Отримує витрати користувача за вказаний період.
    
    Args:
        db: Сесія бази даних
        user_id: ID користувача в Telegram
        start_date: Початкова дата
        end_date: Кінцева дата (якщо не вказана, то до поточного часу)
        category: Опціональна категорія для фільтрації
        
    Returns:
        Список витрат
    """
    if not end_date:
        end_date = datetime.now()
    
    query = db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.created_at >= start_date,
        Expense.created_at <= end_date
    )
    
    if category:
        query = query.filter(Expense.category == category)
    
    return query.all()

def get_expense_sum_by_category(
    db: Session,
    user_id: int,
    category: str,
    year: Optional[int] = None,
    month: Optional[int] = None
) -> float:
    """
    Отримує суму витрат за категорією за місяць.
    
    Args:
        db: Сесія бази даних
        user_id: ID користувача в Telegram
        category: Категорія витрати
        year: Рік (якщо не вказаний, поточний)
        month: Місяць (якщо не вказаний, поточний)
        
    Returns:
        Сума витрат
    """
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    result = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.category == category,
        extract('year', Expense.created_at) == year,
        extract('month', Expense.created_at) == month
    ).scalar()
    
    return float(result) if result else 0.0

# Операції з лімітами бюджету
def get_budget_limit(
    db: Session,
    user_id: int,
    category: str
) -> Optional[BudgetLimit]:
    """
    Отримує ліміт бюджету для користувача по категорії.
    
    Args:
        db: Сесія бази даних
        user_id: ID користувача в Telegram
        category: Категорія витрати
        
    Returns:
        Об'єкт ліміту бюджету або None, якщо ліміт не встановлено
    """
    return db.query(BudgetLimit).filter(
        BudgetLimit.user_id == user_id,
        BudgetLimit.category == category
    ).first()

def set_budget_limit(
    db: Session,
    user_id: int,
    category: str,
    limit_amount: float
) -> BudgetLimit:
    """
    Встановлює ліміт бюджету для користувача по категорії.
    Якщо ліміт вже існує, оновлює його.
    
    Args:
        db: Сесія бази даних
        user_id: ID користувача в Telegram
        category: Категорія витрати
        limit_amount: Сума ліміту
        
    Returns:
        Об'єкт ліміту бюджету
    """
    budget_limit = get_budget_limit(db, user_id, category)
    
    if budget_limit:
        budget_limit.limit_amount = limit_amount
    else:
        budget_limit = BudgetLimit(
            user_id=user_id,
            category=category,
            limit_amount=limit_amount
        )
        db.add(budget_limit)
    
    db.commit()
    db.refresh(budget_limit)
    return budget_limit

def get_all_limits(db: Session, user_id: int) -> List[BudgetLimit]:
    """
    Отримує всі ліміти бюджету для користувача.
    
    Args:
        db: Сесія бази даних
        user_id: ID користувача в Telegram
        
    Returns:
        Список лімітів бюджету
    """
    return db.query(BudgetLimit).filter(BudgetLimit.user_id == user_id).all()

def check_budget_limit(
    db: Session,
    user_id: int,
    category: str,
    amount: float
) -> Tuple[bool, Optional[float]]:
    """
    Перевіряє, чи перевищить нова витрата ліміт бюджету.
    
    Args:
        db: Сесія бази даних
        user_id: ID користувача в Telegram
        category: Категорія витрати
        amount: Сума нової витрати
        
    Returns:
        (is_over_limit, remaining): Чи перевищить ліміт, залишок (або None якщо ліміт не встановлено)
    """
    # Отримуємо ліміт для категорії
    budget_limit = get_budget_limit(db, user_id, category)
    if not budget_limit:
        return False, None
    
    # Отримуємо поточні витрати за цей місяць
    now = datetime.now()
    current_month_expenses = get_expense_sum_by_category(
        db, user_id, category, now.year, now.month
    )
    
    # Розраховуємо залишок після додавання нової витрати
    limit_amount = float(budget_limit.limit_amount)
    new_total = current_month_expenses + amount
    remaining = limit_amount - new_total
    
    # Перевіряємо, чи буде перевищено ліміт
    is_over_limit = new_total > limit_amount
    
    return is_over_limit, remaining

def get_remaining_budget(
    db: Session,
    user_id: int,
    category: str
) -> Optional[float]:
    """
    Отримує залишок бюджету для категорії на поточний місяць.
    
    Args:
        db: Сесія бази даних
        user_id: ID користувача в Telegram
        category: Категорія витрати
        
    Returns:
        Залишок бюджету або None, якщо ліміт не встановлено
    """
    # Отримуємо ліміт для категорії
    budget_limit = get_budget_limit(db, user_id, category)
    if not budget_limit:
        return None
    
    # Отримуємо поточні витрати за цей місяць
    now = datetime.now()
    current_month_expenses = get_expense_sum_by_category(
        db, user_id, category, now.year, now.month
    )
    
    # Розраховуємо залишок
    limit_amount = float(budget_limit.limit_amount)
    remaining = limit_amount - current_month_expenses
    
    return remaining

def seed_test_data(db: Session, user_id: int) -> None:
    """
    Заповнює базу даних тестовими даними, якщо вона порожня.
    
    Args:
        db: Сесія бази даних
        user_id: ID користувача в Telegram
    """
    # Перевіряємо, чи є дані в таблиці budget_limits
    limits_exist = db.query(BudgetLimit).filter(BudgetLimit.user_id == user_id).first() is not None
    
    # Якщо лімітів немає, створюємо їх
    if not limits_exist:
        # Стандартні ліміти для категорій (в грн)
        default_limits = {
            "Foods": 10000,
            "Shopping": 10000,
            "Housing": 15000,
            "Transportation": 2000,
            "Entertainment": 4000,
            "Others": 10000
        }
        
        for category, limit_amount in default_limits.items():
            db.add(BudgetLimit(
                user_id=user_id,
                category=category,
                limit_amount=limit_amount
            ))
        
        db.commit()
    
    # Перевіряємо, чи є дані в таблиці expenses
    expenses_exist = db.query(Expense).filter(Expense.user_id == user_id).first() is not None
    
    # Якщо витрат немає, створюємо приклади
    if not expenses_exist:
        # Дата для тестових даних (останні 2 місяці)
        now = datetime.now()
        this_month = datetime(now.year, now.month, 1)
        prev_month = this_month - timedelta(days=1)
        prev_month = datetime(prev_month.year, prev_month.month, 1)
        
        # Приклади витрат за поточний місяць
        test_expenses_current = [
            {
                "category": "Foods",
                "amount": 450.0,
                "description": "Супермаркет АТБ",
                "transcript": "Купив продукти в АТБ за 450 гривень",
                "days_ago": 2
            },
            {
                "category": "Transportation",
                "amount": 250.0,
                "description": "Таксі",
                "transcript": "Витратив 250 гривень на таксі",
                "days_ago": 3
            },
            {
                "category": "Entertainment",
                "amount": 400.0,
                "description": "Кіно",
                "transcript": "Сходив у кіно, витратив 400 гривень",
                "days_ago": 5
            }
        ]
        
        # Приклади витрат за попередній місяць
        test_expenses_prev = [
            {
                "category": "Foods",
                "amount": 380.0,
                "description": "Продукти",
                "transcript": "Купив продукти за 380 гривень",
                "days_ago": 35
            },
            {
                "category": "Housing",
                "amount": 3000.0,
                "description": "Комунальні послуги",
                "transcript": "Заплатив за комунальні послуги 3000 гривень",
                "days_ago": 40
            }
        ]
        
        # Додаємо витрати за поточний місяць
        for expense_data in test_expenses_current:
            created_at = now - timedelta(days=expense_data["days_ago"])
            db.add(Expense(
                user_id=user_id,
                category=expense_data["category"],
                amount=expense_data["amount"],
                description=expense_data["description"],
                transcript=expense_data["transcript"],
                created_at=created_at
            ))
        
        # Додаємо витрати за попередній місяць
        for expense_data in test_expenses_prev:
            created_at = now - timedelta(days=expense_data["days_ago"])
            db.add(Expense(
                user_id=user_id,
                category=expense_data["category"],
                amount=expense_data["amount"],
                description=expense_data["description"],
                transcript=expense_data["transcript"],
                created_at=created_at
            ))
        
        db.commit()
