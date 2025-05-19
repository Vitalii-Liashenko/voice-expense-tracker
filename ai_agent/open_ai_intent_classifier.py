"""
Модуль для класифікації намірів повідомлень з використанням OpenAI gpt-4o-mini.
"""
import re
import os
import json
import logging
from typing import Dict, Optional, Literal
import openai
from config import OPENAI_API_KEY

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

# Типи намірів
IntentType = Literal["expense", "analytics", "unknown"]

def classify_intent(message: str) -> IntentType:
    """
    Класифікує намір повідомлення за допомогою OpenAI gpt-4o-mini.
    Повертає "expense" для витрат, "analytics" для аналітики, або "unknown".
    
    Args:
        message: Текст повідомлення
        
    Returns:
        Тип наміру: "expense", "analytics", або "unknown"
    """
    if not client or not OPENAI_API_KEY:
        logger.warning("API ключ для OpenAI не налаштовано або клієнт не ініціалізовано. Використовуємо локальний класифікатор.")
        return "unknown"
    
    try:
        # Формуємо промпт для OpenAI
        system_prompt = """
        You are acting as a text analyzer that takes messages in Ukrainian language and must classify the user's intent.
        You must determine if the message is about:
        1. Expense reporting (expense) - when the user is recording a purchase or payment
        2. Analytics request (analytics) - when the user wants information about their expenses
        3. Unknown intent (unknown) - messages that don't fit the above categories
        
        It's very important to distinguish between:
        - Expense messages (expense): user reports an already completed transaction. Such messages often contain verbs in past tense: "bought", "spent", "paid for", "purchased".
        - Analytics requests (analytics): user wants to get information about their finances. Such messages often contain question constructions or request verbs: "how much", "show", "tell", "what amount", "find out".
        
        Return ONLY a valid JSON object with field 'intention' and nothing else.
        Example: {"intention": "expense"} or {"intention": "analytics"} or {"intention": "unknown"}
        """
        
        # Відправляємо запит до OpenAI
        logger.info(f"Відправляємо запит до OpenAI для класифікації: '{message}'")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.0,  # Низька температура для детермінованих відповідей
            response_format={"type": "json_object"}
        )
        
        # Отримуємо відповідь
        raw_result = response.choices[0].message.content.strip()
        logger.info(f"Відповідь OpenAI: '{raw_result}'")
        
        # Парсимо JSON відповідь
        try:
            # Спробуємо спарсити відповідь як JSON
            result_json = json.loads(raw_result)
            
            # Перевіряємо, чи є в JSON поле 'intention'
            if 'intention' in result_json:
                intent = result_json['intention'].lower()
                logger.info(f"Розпізнаний намір: {intent}")
                
                # Перевіряємо, чи намір є одним із допустимих значень
                if intent in ["expense", "analytics", "unknown"]:
                    return intent
                else:
                    logger.warning(f"Неочікуваний намір від OpenAI: '{intent}'")
            else:
                logger.warning(f"У відповіді відсутнє поле 'intention'")
        except json.JSONDecodeError:
            logger.warning(f"Не вдалося декодувати JSON відповідь від OpenAI: '{raw_result}'")
        except Exception as e:
            logger.error(f"Помилка при обробці відповіді від OpenAI: {e}")

    except Exception as e:
        logger.error(f"Помилка під час класифікації наміру з OpenAI: {e}")
    
    return "unknown" 