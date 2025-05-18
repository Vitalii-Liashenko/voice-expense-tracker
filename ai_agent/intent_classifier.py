"""
Модуль для класифікації намірів повідомлень.
"""

def classify_intent(message: str) -> str:
    """
    Класифікує намір повідомлення.
    Повертає "expense" для витрат, "analytics" для аналітики, або "unknown".
    """
    # Тимчасова реалізація - буде замінена на AI-модель
    message = message.lower()
    
    # Перевірка на аналітику
    if any(word in message for word in ["аналітика", "відчуження", "відчужено", "відчужені"]):
        return "analytics"
    
    # Перевірка на витрату
    if any(word in message for word in ["купив", "купила", "заплатив", "заплатила", "видали", "видала"]):
        return "expense"
    
    return "unknown"
