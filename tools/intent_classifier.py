"""
Module for classifying message intents using OpenAI gpt-4o-mini.
"""
import re
import os
import json
import logging
from typing import Dict, Optional, Literal
import openai
from config import OPENAI_API_KEY

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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

# Intent types
IntentType = Literal["expense", "analytics", "unknown"]

def classify_intent(message: str) -> IntentType:
    """
    Classifies message intent using OpenAI gpt-4o-mini.
    Returns "expense" for expenses, "analytics" for analytics, or "unknown".
    
    Args:
        message: Message text
        
    Returns:
        Intent type: "expense", "analytics", or "unknown"
    """
    if not client or not OPENAI_API_KEY:
        logger.warning("OpenAI API key not configured or client not initialized. Using local classifier.")
        return "unknown"
    
    try:
        # Form prompt for OpenAI
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
        
        # Send request to OpenAI
        logger.info(f"Sending request to OpenAI for classification: '{message}'")
        response = client.chat.completions.create(
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
            
            # Check if JSON has 'intention' field
            if 'intention' in result_json:
                intent = result_json['intention'].lower()
                logger.info(f"Recognized intent: {intent}")
                
                # Check if intent is one of the allowed values
                if intent in ["expense", "analytics", "unknown"]:
                    return intent
                else:
                    logger.warning(f"Unexpected intent from OpenAI: '{intent}'")
            else:
                logger.warning(f"Response missing 'intention' field")
        except json.JSONDecodeError:
            logger.warning(f"Failed to decode JSON response from OpenAI: '{raw_result}'")
        except Exception as e:
            logger.error(f"Error processing OpenAI response: {e}")
        
        return "unknown"
    except Exception as e:
        logger.error(f"Error classifying intent: {e}")
        return "unknown" 