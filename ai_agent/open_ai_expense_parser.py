"""
Модуль для парсингу витрат з повідомлень за допомогою OpenAI gpt-4o-mini.
"""
import json
import os
import traceback
from typing import Dict, Optional, Any, List
from config import EXPENSE_CATEGORIES
import openai

class ExpenseParser:
    """
    Клас для парсингу витрат з повідомлень за допомогою OpenAI gpt-4o-mini.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Ініціалізує клас ExpenseParser.
        
        Args:
            api_key: API ключ для OpenAI API (опціонально).
                    Якщо не вказано, буде використано ключ з OPENAI_API_KEY.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API ключ для OpenAI не знайдено")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Категорії витрат
        self.expense_categories = EXPENSE_CATEGORIES
    
    def parse_expense(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Парсить витрату з повідомлення використовуючи OpenAI gpt-4o-mini.
        
        Args:
            message: Текст повідомлення українською мовою
            
        Returns:
            Словник з інформацією про витрату у форматі JSON або None, якщо не вдалося розпізнати витрату
        """
        try:
            # Формуємо системний промпт
            system_prompt = f"""
            You are an assistant that helps analyze expenses from text messages in Ukrainian.
            Your task is to extract expense information from the message: amount (numeric value),
            category, and a brief description of the expense.
            
            Rules:
            1. Allowed expense categories: {', '.join(self.expense_categories)}
            2. Return ONLY a valid JSON object with the following fields:
               - amount: numeric value (float) of the expense
               - category: expense category (one of the allowed categories)
               - description: brief description of the expense
            3. If it's impossible to determine any field, set its value to null
            4. Do not add any explanations, comments, introductions, or conclusions - just clean JSON
            5. If the message doesn't contain expense information, return an empty JSON: {{}}
            
            Example of successful JSON:
            {{
                "amount": 45.7,
                "category": "Foods",
                "description": "Grocery shopping at the supermarket"
            }}
            """
            
            # Відправляємо запит до OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.0,  # Низька температура для детермінованих відповідей
                response_format={"type": "json_object"}
            )
            
            # Отримуємо відповідь
            json_response = response.choices[0].message.content
            
            # Парсимо JSON
            result = json.loads(json_response)
            
            # Якщо результат порожній, повертаємо None
            if not result:
                return None
            
            # Валідуємо поля результату
            if 'amount' not in result or not isinstance(result['amount'], (int, float)):
                return None
            
            if 'category' not in result or result['category'] not in self.expense_categories:
                result['category'] = "Others"
                
            if 'description' not in result or not result['description']:
                result['description'] = "Без опису"
                
            # Додаємо оригінальне повідомлення
            result['transcript'] = message
            
            return result
        except json.JSONDecodeError:
            print(f"Помилка декодування JSON від OpenAI: {response.choices[0].message.content}")
            return None
        except Exception as e:
            print(f"Помилка при парсингу витрати: {str(e)}")
            traceback.print_exc()
            return None

# Для зворотної сумісності
def parse_expense(message: str) -> Optional[Dict[str, Any]]:
    """
    Парсить витрату з повідомлення.
    
    Args:
        message: Текст повідомлення
        
    Returns:
        Словник з інформацією про витрату або None, якщо не вдалося розпізнати витрату
    """
    try:
        parser = ExpenseParser()
        return parser.parse_expense(message)
    except Exception as e:
        print(f"Помилка при парсингу витрати: {str(e)}")
        return None 