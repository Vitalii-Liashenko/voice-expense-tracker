"""
Module for parsing and processing expense-related messages.
"""
import logging
import json
from typing import Dict, Optional, Any
from db.database import get_db_session
from db.queries import save_expense, check_budget_limit
import openai
from config import OPENAI_API_KEY, EXPENSE_CATEGORIES

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create OpenAI client
client = None
if OPENAI_API_KEY:
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {e}")
else:
    logger.warning("OPENAI_API_KEY not found in environment variables")


class ExpenseParser:
    """Class for parsing expense information from text messages."""
    
    def __init__(self):
        self.expense_categories = EXPENSE_CATEGORIES
        self.openai_client = client
    
    def parse_expense(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Parse expense from message using OpenAI gpt-4o-mini.
        
        Args:
            message: Message text in Ukrainian
            
        Returns:
            Dictionary with expense information in JSON format or None if expense couldn't be recognized
        """
        if not self.openai_client:
            logger.error("OpenAI client not initialized")
            return None

        try:
            # Form system prompt
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
            
            # Send request to OpenAI
            logger.info(f"Sending request to OpenAI for expense parsing: '{message}'")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.0,  # Low temperature for deterministic responses
                response_format={"type": "json_object"}
            )
            
            # Get response
            raw_result = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response: '{raw_result}'")
            
            # Parse JSON response
            try:
                # Try to parse response as JSON
                result_json = json.loads(raw_result)
                
                # Check if JSON has required fields
                if all(key in result_json for key in ["amount", "category", "description"]):
                    # Validate amount
                    if result_json["amount"] is not None:
                        try:
                            result_json["amount"] = float(result_json["amount"])
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid amount value: {result_json['amount']}")
                            return None
                    
                    # Validate category
                    if result_json["category"] not in self.expense_categories:
                        logger.warning(f"Invalid category: {result_json['category']}")
                        return None
                    
                    logger.info(f"Successfully parsed expense: {result_json}")
                    return result_json
                else:
                    logger.warning("Response missing required fields")
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode JSON response from OpenAI: '{raw_result}'")
            except Exception as e:
                logger.error(f"Error processing OpenAI response: {e}")
            
            return None
        except Exception as e:
            logger.error(f"Error parsing expense: {e}")
            return None


# Create a singleton instance
expense_parser = ExpenseParser()

def parse_expense(message: str) -> Optional[Dict[str, Any]]:
    """
    Parse expense from message.
    
    Args:
        message: Message text
        
    Returns:
        Dictionary with expense information or None if expense couldn't be recognized
    """
    try:
        return expense_parser.parse_expense(message)
    except Exception as e:
        logger.error(f"Error parsing expense: {e}")
        return None

def save_expenses(expense: dict, user_id: int, text: str) -> str:
    """
    Save expense to database and format response message.
    
    Args:
        expense: Dictionary containing expense details (amount, category, description)
        user_id: User ID
        text: Original text message
        
    Returns:
        str: Formatted message in HTML format
    """
    logger.info(f"Recognized expense: {expense}")
    db = get_db_session()
    try:
        # Get data from parsing
        amount = expense["amount"]
        category = expense["category"]
        description = expense["description"]
        
        # Check budget limit
        is_over, remaining = check_budget_limit(db, user_id, category, amount)
        
        # Save expense
        saved_expense = save_expense(
            db, 
            user_id, 
            category, 
            amount, 
            description,
            text  # transcript - original text in Ukrainian
        )
        
        # Format and send message
        message = f"✅ Збережено витрату: <b>{expense['amount']:.2f} грн</b> ({expense['category']})\n"
        message += f"📝 Опис: {expense['description']}\n"
        
        if is_over:
            message += f"\n⚠️ <b>Увага!</b> Ви перевищили ліміт у категорії <b>{category}</b>.\n"
            message += f"Перевищення на: <b>{abs(remaining):.2f} грн</b>"
        else:
            message += f"\n💰 Залишок у категорії <b>{category}</b>: <b>{remaining:.2f} грн</b>"
        
        return message
    except Exception as e:
        logger.error(f"Error saving expense: {e}")
        return f"Сталася помилка при збереженні витрати: {str(e)}"
    finally:
        db.close() 