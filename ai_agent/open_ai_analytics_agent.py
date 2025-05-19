"""
Модуль для генерації аналітики витрат за допомогою OpenAI gpt-4o-mini.
"""
import re
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import openai

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

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Створюємо клієнт OpenAI
client = None
if OPENAI_API_KEY:
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        logger.error(f"Помилка ініціалізації клієнта OpenAI: {e}")
else:
    logger.warning("OPENAI_API_KEY не знайдено в змінних середовища")

def _get_period_from_text(text: str) -> Tuple[datetime, Optional[datetime]]:
    """
    Визначає період з тексту запиту.
    
    Args:
        text: Текст запиту
        
    Returns:
        Кортеж: (початкова_дата, кінцева_дата)
    """
    text = text.lower()
    today = datetime.now()
    
    # За замовчуванням - поточний місяць
    start_date = datetime(today.year, today.month, 1)
    end_date = None
    
    # Шаблонні періоди
    if 'сьогодні' in text:
        start_date = datetime(today.year, today.month, today.day)
        end_date = None
    elif 'вчора' in text or 'учора' in text:
        yesterday = today - timedelta(days=1)
        start_date = datetime(yesterday.year, yesterday.month, yesterday.day)
        end_date = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
    elif 'тиждень' in text:
        if 'минулий' in text or 'попередній' in text:
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
        else:  # поточний тиждень
            start_date = today - timedelta(days=today.weekday())
            end_date = None
    elif 'місяць' in text:
        if 'минулий' in text or 'попередній' in text:
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, 1)
                end_date = datetime(today.year - 1, 12, 31, 23, 59, 59)
            else:
                start_date = datetime(today.year, today.month - 1, 1)
                end_date = datetime(today.year, today.month, 1) - timedelta(seconds=1)
        else:  # поточний місяць
            start_date = datetime(today.year, today.month, 1)
            end_date = None
    elif 'рік' in text:
        if 'минулий' in text or 'попередній' in text:
            start_date = datetime(today.year - 1, 1, 1)
            end_date = datetime(today.year - 1, 12, 31, 23, 59, 59)
        else:  # поточний рік
            start_date = datetime(today.year, 1, 1)
            end_date = None
    
    return start_date, end_date

def _extract_category_from_text(text: str) -> Optional[str]:
    """
    Використовує OpenAI для визначення категорії з тексту запиту.
    
    Args:
        text: Текст запиту
        
    Returns:
        Категорія або None, якщо не вдалося визначити
    """
    if not client or not OPENAI_API_KEY:
        return None
    
    try:
        system_prompt = f"""
        You are an assistant that analyzes text in Ukrainian to identify expense categories.
        
        Valid categories: {', '.join(EXPENSE_CATEGORIES)}
        
        Look for mentions of categories in the text. 
        Category words in Ukrainian might include:
        - Foods: їжа, продукти, харчування, супермаркет, магазин, кафе, ресторан, їдальня
        - Shopping: одяг, взуття, покупки, шопінг, електроніка, техніка
        - Housing: житло, квартира, комуналка, оренда, меблі, інтернет
        - Transportation: транспорт, таксі, автобус, метро, бензин, паливо
        - Entertainment: розваги, кіно, театр, концерт, клуб, спорт
        - Others: інше, решта, різне
        
        Return ONLY a JSON with the field 'category' containing one of the valid categories or null if none is found.
        Example: {{"category": "Foods"}} or {{"category": null}}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        # Отримуємо відповідь
        result_json = json.loads(response.choices[0].message.content)
        
        if 'category' in result_json and result_json['category'] in EXPENSE_CATEGORIES:
            return result_json['category']
        
    except Exception as e:
        logger.error(f"Помилка при визначенні категорії з OpenAI: {e}")
    
    return None

def _format_period_text(start_date: datetime, end_date: Optional[datetime]) -> str:
    """
    Форматує текстовий опис періоду для відображення.
    
    Args:
        start_date: Початкова дата
        end_date: Кінцева дата
        
    Returns:
        Текстовий опис періоду
    """
    today = datetime.now()
    
    # Сьогодні
    if (start_date.year == today.year and 
        start_date.month == today.month and 
        start_date.day == today.day and 
        (not end_date or (end_date.year == today.year and 
                          end_date.month == today.month and 
                          end_date.day == today.day))):
        return "сьогодні"
    
    # Вчора
    yesterday = today - timedelta(days=1)
    if (start_date.year == yesterday.year and 
        start_date.month == yesterday.month and 
        start_date.day == yesterday.day and 
        (not end_date or (end_date.year == yesterday.year and 
                          end_date.month == yesterday.month and 
                          end_date.day == yesterday.day))):
        return "вчора"
    
    # Поточний місяць
    if (start_date.year == today.year and 
        start_date.month == today.month and 
        start_date.day == 1 and 
        not end_date):
        return "поточний місяць"
    
    # Минулий місяць
    last_month = today.replace(day=1) - timedelta(days=1)
    if (start_date.year == last_month.year and 
        start_date.month == last_month.month and 
        start_date.day == 1 and 
        end_date and end_date.year == last_month.year and 
        end_date.month == last_month.month):
        return "минулий місяць"
    
    # Діапазон дат
    if end_date:
        return f"з {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}"
    else:
        return f"з {start_date.strftime('%d.%m.%Y')} по сьогодні"

def _extract_analytics_type(text: str) -> str:
    """
    Використовує OpenAI для визначення типу аналітики з тексту запиту.
    
    Args:
        text: Текст запиту
        
    Returns:
        Тип аналітики: "category", "limit", "summary"
    """
    if not client or not OPENAI_API_KEY:
        return "summary"
    
    try:
        system_prompt = """
        You are an assistant that analyzes expense-related queries in Ukrainian.
        
        Determine the type of analytics request from the message:
        
        1. "category" - when asking about expenses for a specific category
        2. "limit" - when asking about budget limits, remaining budget, or how much can still be spent
        3. "summary" - when asking for overall analytics, total expenses, or a general report
        
        Return ONLY a JSON with the field 'type' containing one of these values.
        Example: {"type": "category"} or {"type": "limit"} or {"type": "summary"}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        # Отримуємо відповідь
        result_json = json.loads(response.choices[0].message.content)
        
        if 'type' in result_json and result_json['type'] in ["category", "limit", "summary"]:
            return result_json['type']
        
    except Exception as e:
        logger.error(f"Помилка при визначенні типу аналітики з OpenAI: {e}")
    
    return "summary"

def generate_analytics(message: str) -> str:
    """
    Генерує аналітику витрат на основі повідомлення.
    
    Args:
        message: Текст повідомлення з запитом на аналітику
        
    Returns:
        Текст аналітики
    """
    try:
        db = get_db_session()
        
        try:
            # 1. Визначаємо період
            start_date, end_date = _get_period_from_text(message)
            period_text = _format_period_text(start_date, end_date)
            
            # 2. Визначаємо категорію (якщо є)
            category = _extract_category_from_text(message)
            
            # 3. Визначаємо тип аналітики
            analytics_type = _extract_analytics_type(message)
            
            response = ""
            
            if analytics_type == "limit":
                # Загальна інформація про ліміти
                response = "💰 <b>Залишки бюджету на місяць</b>\n\n"
                
                # Отримуємо всі ліміти
                for category in EXPENSE_CATEGORIES:
                    remaining = get_remaining_budget(db, AUTHOR_USER_ID, category)
                    
                    if remaining is not None:
                        limit = get_budget_limit(db, AUTHOR_USER_ID, category)
                        percentage = (remaining / float(limit.limit_amount)) * 100
                        
                        # Додаємо індикатор залежно від залишку
                        indicator = "✅"
                        if remaining <= 0:
                            indicator = "❌"
                        elif percentage < 20:
                            indicator = "🔴"
                        elif percentage < 50:
                            indicator = "🟠"
                        elif percentage < 80:
                            indicator = "🟡"
                        
                        response += f"{indicator} {category}: {remaining:.2f} грн "
                        response += f"({percentage:.1f}% від ліміту)\n"
                    else:
                        response += f"⚪ {category}: ліміт не встановлено\n"
                
            elif analytics_type == "category" and category:
                # Аналітика по вказаній категорії
                expenses = get_expenses_by_category(db, AUTHOR_USER_ID, category, start_date, end_date)
                
                if not expenses:
                    response = f"📊 <b>Аналітика витрат на {category}</b>\n\n"
                    response += f"Немає витрат на {category} за {period_text}."
                else:
                    total_amount = sum(expense.amount for expense in expenses)
                    
                    # Перевіряємо ліміт
                    remaining = get_remaining_budget(db, AUTHOR_USER_ID, category)
                    
                    # Формуємо повідомлення
                    response = f"📊 <b>Аналітика витрат на {category}</b>\n\n"
                    response += f"• Загальна сума: {total_amount:.2f} грн\n"
                    response += f"• Кількість транзакцій: {len(expenses)}\n"
                    
                    if len(expenses) > 0:
                        avg_amount = total_amount / len(expenses)
                        response += f"• Середня сума: {avg_amount:.2f} грн\n"
                    
                    if remaining is not None:
                        response += f"\n💰 <b>Залишок у категорії</b>: {remaining:.2f} грн\n"
                    
                    # Додаємо останні 5 транзакцій
                    if len(expenses) > 0:
                        response += "\n<b>Останні транзакції:</b>\n"
                        for expense in sorted(expenses, key=lambda x: x.created_at, reverse=True)[:5]:
                            date_str = expense.created_at.strftime("%d.%m.%Y")
                            response += f"- {date_str}: {expense.description} ({float(expense.amount):.2f} грн)\n"
            
            else:
                # Загальна аналітика
                expenses_by_cat = {}
                for category in EXPENSE_CATEGORIES:
                    expenses = get_expenses_by_category(db, AUTHOR_USER_ID, category, start_date, end_date)
                    if expenses:
                        expenses_by_cat[category] = sum(expense.amount for expense in expenses)
                
                # Рахуємо загальну суму витрат
                total_expenses = sum(expenses_by_cat.values()) if expenses_by_cat else 0
                
                # Формуємо повідомлення
                response = f"📊 <b>Загальна аналітика витрат за {period_text}</b>\n\n"
                
                if not expenses_by_cat:
                    response += "Немає витрат за вказаний період.\n"
                else:
                    # Додаємо розбивку по категоріям
                    for category, amount in expenses_by_cat.items():
                        percentage = (amount / total_expenses) * 100 if total_expenses > 0 else 0
                        response += f"• {category}: {amount:.2f} грн ({percentage:.1f}%)\n"
                    
                    response += f"\n💰 <b>Загальні витрати</b>: {total_expenses:.2f} грн\n"
            
            return response
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Помилка при генерації аналітики: {e}")
        return "Вибачте, сталася помилка при генерації аналітики. Спробуйте ще раз." 