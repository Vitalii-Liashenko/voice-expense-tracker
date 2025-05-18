"""
Database module for Voice Expense Tracker.
Contains database connection, models, and CRUD operations.
"""

from db.database import get_db_session, init_db, engine
from db.models import Base, Expense, BudgetLimit
from db.queries import (
    save_expense,
    get_expenses_by_category,
    get_expenses_by_period,
    get_budget_limit,
    check_budget_limit,
    get_remaining_budget,
    get_all_limits,
    seed_test_data
)

__all__ = [
    'get_db_session',
    'init_db',
    'engine',
    'Base',
    'Expense',
    'BudgetLimit',
    'save_expense',
    'get_expenses_by_category',
    'get_expenses_by_period',
    'get_budget_limit',
    'check_budget_limit',
    'get_remaining_budget',
    'get_all_limits',
    'seed_test_data'
]
