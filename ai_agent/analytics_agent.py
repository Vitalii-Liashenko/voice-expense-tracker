"""
Модуль для генерації аналітики витрат.
"""
from db.queries import get_expenses_by_category, get_total_expenses

def generate_analytics(message: str) -> str:
    """
    Генерує аналітику витрат на основі повідомлення.
    """
    try:
        # Тимчасова реалізація - буде замінена на AI-модель
        db = get_db_session()
        try:
            # Отримуємо витрати по категоріям
            expenses_by_cat = get_expenses_by_category(db)
            total_expenses = get_total_expenses(db)
            
            # Формуємо повідомлення з аналітикою
            message = "📊 <b>Аналітика витрат</b>\n\n"
            
            for category, amount in expenses_by_cat.items():
                message += f"• {category}: {amount} грн\n"
            
            message += f"\n💰 Загальні витрати: {total_expenses} грн"
            
            return message
        finally:
            db.close()
    except Exception as e:
        print(f"Помилка при генерації аналітики: {e}")
        return "Вибачте, сталася помилка при генерації аналітики. Спробуйте ще раз."
