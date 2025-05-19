"""
Приклад використання класу ExpenseParser з OpenAI gpt-4o-mini
для парсингу витрат з текстових повідомлень українською мовою.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Додаємо кореневу директорію проекту до шляху
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent.expense_parser import ExpenseParser

def main():
    """
    Демонструє використання ExpenseParser з OpenAI gpt-4o-mini.
    
    Потрібен API ключ OpenAI у змінній оточення OPENAI_API_KEY.
    """
    # Завантажуємо змінні оточення
    load_dotenv()
    
    # Перевіряємо наявність API ключа
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Помилка: API ключ OpenAI не знайдено.")
        print("Встановіть OPENAI_API_KEY у змінних оточення або .env файлі.")
        sys.exit(1)
    
    # Створюємо парсер
    parser = ExpenseParser()
    
    # Приклади повідомлень
    examples = [
        "Купив продукти в АТБ за 235,50 грн",
        "Витратив 400 гривень на таксі вчора",
        "Заплатив 2800 грн за квартиру",
        "Обід в кафе коштував 175 грн",
        "Квитки в кіно на 350 гривень",
    ]
    
    print("===== ДЕМО ПАРСЕРА ВИТРАТ З OPENAI GPT-4O-MINI =====\n")
    
    # Обробляємо кожне повідомлення
    for message in examples:
        print(f"Повідомлення: \"{message}\"")
        
        try:
            # Аналізуємо повідомлення
            result = parser.parse_expense(message)
            
            # Виводимо результат
            if result:
                print("Результат парсингу:")
                print(f"  Сума: {result['amount']} грн")
                print(f"  Категорія: {result['category']}")
                print(f"  Опис: {result['description']}")
                print(f"  JSON: {json.dumps(result, ensure_ascii=False)}")
            else:
                print("Повідомлення не розпізнано як витрату.")
                
        except Exception as e:
            print(f"Помилка: {str(e)}")
            
        print("-" * 50)

if __name__ == "__main__":
    main() 