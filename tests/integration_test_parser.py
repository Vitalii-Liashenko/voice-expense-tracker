"""
Інтеграційні тести для парсера витрат.
Цей скрипт демонструє реальне використання парсера витрат з OpenAI gpt-4o-mini.
Потрібен дійсний API ключ OpenAI.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Додаємо кореневу директорію проекту до шляху
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent.expense_parser import ExpenseParser

# Завантажуємо змінні оточення
load_dotenv()

def test_with_real_examples():
    """
    Демонструє роботу парсера витрат з реальними прикладами.
    
    Примітка: для запуску потрібен дійсний API ключ OpenAI, встановлений
    у змінній оточення OPENAI_API_KEY.
    """
    # Перевіряємо наявність API ключа
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ПОМИЛКА: API ключ OpenAI не знайдено. Встановіть OPENAI_API_KEY у змінних оточення.")
        sys.exit(1)
    
    # Створюємо екземпляр парсера
    parser = ExpenseParser(api_key=api_key)
    
    # Приклади повідомлень для тестування
    test_messages = [
        "Купив продукти в АТБ за 235,50 грн",
        "Витратив 400 гривень на таксі",
        "Заплатив за інтернет 340 гривень",
        "Обід в кафе коштував 175 грн",
        "Витратив 1200 грн на квитки в театр",
        "Скільки буде 2+2?",  # Не витрата, має повернути None
        "Заплатив за комуналку 2500 грн",
    ]
    
    print("Тестування парсера витрат з OpenAI gpt-4o-mini\n")
    print("=" * 50)
    
    # Тестуємо кожне повідомлення
    for message in test_messages:
        print(f"\nПовідомлення: '{message}'")
        
        try:
            result = parser.parse_expense(message)
            
            if result:
                print(f"Результат парсингу: {json.dumps(result, ensure_ascii=False, indent=2)}")
            else:
                print("Результат: Не розпізнано як витрату")
        except Exception as e:
            print(f"Помилка: {str(e)}")
        
        print("-" * 50)

def main():
    """Основна функція для запуску інтеграційних тестів."""
    test_with_real_examples()

if __name__ == "__main__":
    main() 