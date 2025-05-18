"""
Database models for Voice Expense Tracker.
"""
from sqlalchemy import Column, Integer, String, Numeric, BigInteger, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Expense(Base):
    """
    Модель для зберігання витрат користувача.
    """
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    amount = Column(Numeric, nullable=False)
    description = Column(Text, nullable=True)
    transcript = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=False))
    
    def __repr__(self):
        return f"<Expense(id={self.id}, user_id={self.user_id}, category={self.category}, amount={self.amount})>"

class BudgetLimit(Base):
    """
    Модель для зберігання лімітів бюджету по категоріях.
    """
    __tablename__ = "budget_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    limit_amount = Column(Numeric, nullable=False)
    
    def __repr__(self):
        return f"<BudgetLimit(id={self.id}, user_id={self.user_id}, category={self.category}, limit_amount={self.limit_amount})>"
    
    __table_args__ = (
        # Унікальний індекс, щоб у користувача міг бути лише один ліміт для кожної категорії
        {"sqlite_autoincrement": True},
    )
