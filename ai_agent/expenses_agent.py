"""
Module for parsing and processing expense-related messages using LangChain.
"""
import logging
import json
from typing import Dict, Optional, Any, List
from db.database import get_db_session
from db.queries import save_expense, check_budget_limit

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field, validator

from config import OPENAI_API_KEY, EXPENSE_CATEGORIES

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define the output schema for expense parsing
class ExpenseOutput(BaseModel):
    amount: Optional[float] = Field(description="The numeric value (float) of the expense")
    category: Optional[str] = Field(description="The expense category")
    description: Optional[str] = Field(description="A brief description of the expense")
    
    @validator('category')
    def validate_category(cls, v):
        if v is not None and v not in EXPENSE_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(EXPENSE_CATEGORIES)}")
        return v

# Create the output parser
output_parser = JsonOutputParser(pydantic_model=ExpenseOutput)

# Create the LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=OPENAI_API_KEY
)

# Create the prompt template
system_template = f"""
You are an assistant that helps analyze expenses from text messages in English.
Your task is to extract expense information from the message: amount (numeric value),
category from the list: {', '.join(EXPENSE_CATEGORIES)}, and a brief description of the expense.

Rules:
1. If it's impossible to determine any field, set its value to null
2. If the message doesn't contain category information, return "Others" for category

Return the result in JSON format without any additional text or explanations.

Example of successful JSON:
{{{{
    "amount": 45.7,
    "category": "Foods",
    "description": "Grocery shopping at the supermarket"
}}}}

"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_template),
    ("user", "{message}")
])

# Create the chain
expense_chain = prompt | llm | output_parser

class ExpenseParser:
    """Class for parsing expense information from text messages using LangChain."""
    
    def __init__(self):
        self.expense_categories = EXPENSE_CATEGORIES
    
    def parse_expense(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Parse expense from message using LangChain and OpenAI gpt-4o-mini.
        
        Args:
            message: Message text in Ukrainian
            
        Returns:
            Dictionary with expense information in JSON format or None if expense couldn't be recognized
        """
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not configured")
            return None

        try:
            # Log the request
            logger.info(f"Sending request to LangChain for expense parsing: '{message}'")
            
            # Run the chain
            result = expense_chain.invoke({"message": message})
            
            # Log the result
            logger.info(f"LangChain response: {result}")
            
            # Check if we have valid expense data
            if result.get("amount") is None and result.get("category") is None:
                logger.warning("No expense information found in the message")
                return None
                
            # Convert the result to a dictionary
            expense_data = {
                "amount": result.get("amount"),
                "category": result.get("category"),
                "description": result.get("description")
            }
            
            # Validate the expense data
            if expense_data["amount"] is not None and expense_data["category"] is not None:
                logger.info(f"Successfully parsed expense: {expense_data}")
                return expense_data
            else:
                logger.warning("Missing required expense fields")
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