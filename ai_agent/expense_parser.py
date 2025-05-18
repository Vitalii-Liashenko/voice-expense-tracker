"""
Модуль для парсингу витрат з повідомлень.
"""

def parse_expense(message: str) -> dict:
    """
    Парсить витрату з повідомлення.
    Повертає словник з сумою та категорією, або None якщо не може спарсити.
    """
    # Тимчасова реалізація - буде замінена на AI-модель
    try:
        # Простий парсер для тестування
        words = message.lower().split()
        amount = None
        category = None
        
        # Пошук суми
        for word in words:
            if word.replace(',', '').replace('.', '').isdigit():
                amount = float(word.replace(',', '.'))
                break
        
        # Пошук категорії
        if "продукти" in message or "їжа" in message:
            category = "Foods"
        elif "транспорт" in message or "таксі" in message:
            category = "Transportation"
        elif "одяг" in message or "магазин" in message:
            category = "Shopping"
        elif "житло" in message or "комуналка" in message:
            category = "Housing"
        elif "розвл" in message or "забав" in message:
            category = "Entertainment"
        else:
            category = "Others"
        
        if amount and category:
            return {
                'amount': amount,
                'category': category
            }
        
    except Exception as e:
        print(f"Помилка при парсингу витрати: {e}")
    
    return None
