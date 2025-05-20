"""
Module for generating expense analytics using LangChain and OpenAI gpt-4o-mini.
"""
import re
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from db.database import get_db_session
from db.queries import (
    get_expenses_by_category, 
    get_total_expenses, 
    get_expenses_by_period,
    get_budget_limit,
    get_remaining_budget,
    check_budget_limit,
    get_all_limits,
    get_expense_sum_by_category
)
from config import EXPENSE_CATEGORIES, AUTHOR_USER_ID, OPENAI_API_KEY

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=OPENAI_API_KEY
)

def _get_period_from_text(text: str) -> Tuple[datetime, Optional[datetime]]:
    """
    Determines period from query text.
    
    Args:
        text: Query text
        
    Returns:
        Tuple: (start_date, end_date)
    """
    text = text.lower()
    today = datetime.now()
    
    # Default to current month
    start_date = datetime(today.year, today.month, 1)
    end_date = None
    
    # Common periods
    if 'today' in text:
        start_date = datetime(today.year, today.month, today.day)
        end_date = None
    elif 'yesterday' in text or 'day before' in text:
        yesterday = today - timedelta(days=1)
        start_date = datetime(yesterday.year, yesterday.month, yesterday.day)
        end_date = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
    elif 'week' in text:
        if 'last' in text or 'previous' in text:
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
        else:  # current week
            start_date = today - timedelta(days=today.weekday())
            end_date = None
    elif 'month' in text:
        if 'last' in text or 'previous' in text:
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, 1)
                end_date = datetime(today.year - 1, 12, 31, 23, 59, 59)
            else:
                start_date = datetime(today.year, today.month - 1, 1)
                end_date = datetime(today.year, today.month, 1) - timedelta(seconds=1)
        else:  # current month
            start_date = datetime(today.year, today.month, 1)
            end_date = None
    elif 'year' in text:
        if 'last' in text or 'previous' in text:
            start_date = datetime(today.year - 1, 1, 1)
            end_date = datetime(today.year - 1, 12, 31, 23, 59, 59)
        else:  # current year
            start_date = datetime(today.year, 1, 1)
            end_date = None
    
    return start_date, end_date

# Define the output schema for category extraction
class CategoryOutput(BaseModel):
    category: Optional[str] = Field(description="The expense category identified in the text")

# Create the output parser for category extraction
category_parser = JsonOutputParser(pydantic_model=CategoryOutput)

# Create the prompt template for category extraction
category_template = f"""
You are an assistant that analyzes text in English to identify expense categories.

Valid categories: {', '.join(EXPENSE_CATEGORIES)}

Look for mentions of categories in the text. 
Category words in English might include:
- Foods: food, groceries, nutrition, supermarket, store, cafe, restaurant, cafeteria
- Shopping: clothes, shoes, purchases, shopping, electronics, appliances
- Housing: housing, apartment, utilities, rent, furniture, internet
- Transportation: transport, taxi, bus, metro, gasoline, fuel
- Entertainment: entertainment, cinema, theater, concert, club, sports
- Others: other, rest, various

Example of successful JSON:
            {{{{
                "category": "Foods"
            }}}}
"""

# Create the category prompt
category_prompt = ChatPromptTemplate.from_messages([
    ("system", category_template),
    ("user", "{message}")
])

# Create the chain for category extraction
category_chain = category_prompt | llm | category_parser

def _extract_category_from_text(text: str) -> Optional[str]:
    """
    Uses LangChain to determine category from query text.
    
    Args:
        text: Query text
        
    Returns:
        Category or None if couldn't determine
    """
    if not OPENAI_API_KEY:
        return None
    
    try:
        # Log the request
        logger.info(f"Sending request to LangChain for category extraction: '{text}'")
        
        # Run the chain
        result = category_chain.invoke({"message": text})
        
        # Log the result
        logger.info(f"LangChain category response: {result}")
        
        # Extract and validate the category
        category = result.get("category")
        if category in EXPENSE_CATEGORIES:
            return category
        
    except Exception as e:
        logger.error(f"Error determining category from LangChain: {e}")
    
    return None

def _format_period_text(start_date: datetime, end_date: Optional[datetime]) -> str:
    """
    Format period text for analytics response.
    
    Args:
        start_date: Start date
        end_date: End date (optional)
        
    Returns:
        Formatted period text
    """
    if end_date is None:
        end_date = datetime.now()
    
    # If period is less than a day
    if (end_date - start_date).total_seconds() < 86400:
        return "сьогодні"
    
    # If period is less than a week
    if (end_date - start_date).total_seconds() < 604800:
        return "цей тиждень"
    
    # If period is less than a month
    if (end_date - start_date).total_seconds() < 2592000:
        return "цей місяць"
    
    # If period is less than a year
    if (end_date - start_date).total_seconds() < 31536000:
        return "цей рік"
    
    # For longer periods
    return f"з {start_date.strftime('%Y-%m-%d')} по {end_date.strftime('%Y-%m-%d')}"

# Define the analytics type
AnalyticsType = Literal["category", "limit", "summary"]

# Define the output schema for analytics type extraction
class AnalyticsTypeOutput(BaseModel):
    type: AnalyticsType = Field(description="The type of analytics request")

# Create the output parser for analytics type extraction
analytics_type_parser = JsonOutputParser(pydantic_model=AnalyticsTypeOutput)

# Create the prompt template for analytics type extraction
analytics_type_template = f"""
You are an assistant that analyzes expense-related queries in English.

Determine the type of analytics request from the message:

1. "category" - when asking about expenses for a specific category
2. "limit" - when asking about budget limits, remaining budget, or how much can still be spent
3. "summary" - when asking for overall analytics, total expenses, or a general report
Return the result in JSON format without any additional text or explanations.

Example of successful JSON:
{{{{
    "type": "category"
}}}}
"""

analytics_type_prompt = ChatPromptTemplate.from_messages([
    ("system", analytics_type_template),
    ("user", "{message}")
])

# Create the chain for analytics type extraction
analytics_type_chain = analytics_type_prompt | llm | analytics_type_parser

def _extract_analytics_type(text: str) -> str:
    """
    Uses LangChain to determine analytics type from query text.
    
    Args:
        text: Query text
        
    Returns:
        Analytics type: "category", "limit", "summary"
    """
    if not OPENAI_API_KEY:
        return "summary"
    
    try:
        # Log the request
        logger.info(f"Sending request to LangChain for analytics type extraction: '{text}'")
        
        # Run the chain
        result = analytics_type_chain.invoke({"message": text})
        
        # Log the result
        logger.info(f"LangChain analytics type response: {result}")
        
        # Extract and validate the analytics type
        analytics_type = result.get("type")
        if analytics_type in ["category", "limit", "summary"]:
            return analytics_type
        
    except Exception as e:
        logger.error(f"Error determining analytics type from LangChain: {e}")
    
    return "summary"

def generate_analytics(message: str) -> str:
    """
    Generate expense analytics based on message.
    
    Args:
        message: Message text with analytics request
        
    Returns:
        Analytics text
    """
    try:
        db = get_db_session()
        
        try:
            # 1. Determine period
            start_date, end_date = _get_period_from_text(message)
            period_text = _format_period_text(start_date, end_date)
            
            # 2. Determine category (if any)
            category = _extract_category_from_text(message)
            
            # 3. Determine analytics type
            analytics_type = _extract_analytics_type(message)
            
            response = ""
            
            if analytics_type == "category" and category:
                # Category-specific analytics
                expenses = get_expenses_by_category(db, AUTHOR_USER_ID, category, start_date, end_date)
                total = sum(expense.amount for expense in expenses) if expenses else 0
                
                response = f"📊 <b>Витрати на {category} за {period_text}</b>\n\n"
                
                if not expenses:
                    response += f"Не знайдено витрат на {category} за цей період.\n"
                else:
                    response += f"Загальна сума: {total:.2f} грн\n"
                    
                    # Add individual expenses
                    for expense in expenses:
                        response += f"• {expense.amount:.2f} грн - {expense.description}\n"
            
            elif analytics_type == "limit":
                # Budget limit analytics
                limits = get_all_limits(db, AUTHOR_USER_ID)
                
                response = f"💰 <b>Ліміти бюджету за {period_text}</b>\n\n"
                
                for budget_limit in limits:
                    remaining = get_remaining_budget(db, AUTHOR_USER_ID, budget_limit.category)
                    limit_amount = float(budget_limit.limit_amount)
                    percentage = (float(remaining) / limit_amount) * 100 if limit_amount > 0 else 0
                    
                    response += f"• {budget_limit.category}: {remaining:.2f} грн / {limit_amount:.2f} грн ({percentage:.1f}% залишку)\n"
            
            else:
                # General analytics
                expenses_by_cat = {}
                for category in EXPENSE_CATEGORIES:
                    expenses = get_expenses_by_category(db, AUTHOR_USER_ID, category, start_date, end_date)
                    if expenses:
                        expenses_by_cat[category] = sum(expense.amount for expense in expenses)
                
                # Calculate total expenses
                total_expenses = sum(expenses_by_cat.values()) if expenses_by_cat else 0
                
                # Form message
                response = f"📊 <b>Загальна аналітика витрат за {period_text}</b>\n\n"
                
                if not expenses_by_cat:
                    response += "Не знайдено витрат за цей період.\n"
                else:
                    # Add category breakdown
                    for category, amount in expenses_by_cat.items():
                        percentage = (float(amount) / float(total_expenses)) * 100 if total_expenses > 0 else 0
                        response += f"• {category}: {amount:.2f} грн ({percentage:.1f}%)\n"
                    
                    response += f"\n💰 <b>Загальні витрати</b>: {total_expenses:.2f} грн\n"
            
            return response
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        return "Вибачте, сталася помилка при генерації аналітики. Спробуйте ще раз." 