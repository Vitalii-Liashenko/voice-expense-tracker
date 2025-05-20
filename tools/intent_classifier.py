"""
Module for classifying message intents using LangChain and OpenAI gpt-4o-mini.
"""
import logging
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config import OPENAI_API_KEY

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Intent types
IntentType = Literal["expense", "analytics", "unknown"]

# Create the LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=OPENAI_API_KEY
)

# Create the prompt template
system_template = """
You are acting as a text analyzer that takes messages in English language and must classify the user's intent.
You must determine if the message is about:
1. Expense reporting (expense) - when the user is recording a purchase or payment
2. Analytics request (analytics) - when the user wants information about their expenses
3. Unknown intent (unknown) - messages that don't fit the above categories

It's very important to distinguish between:
- Expense messages (expense): user reports an already completed transaction. Such messages often contain verbs in past tense: "bought", "spent", "paid for", "purchased".
- Analytics requests (analytics): user wants to get information about their finances. Such messages often contain question constructions or request verbs: "how much", "show", "tell", "what amount", "find out".

You MUST respond in a valid JSON format with a single key "intention" and one of these three values: "expense", "analytics", or "unknown".
Example responses:
{{"intention": "expense"}}
{{"intention": "analytics"}}
{{"intention": "unknown"}}

Do not include any explanations, only return the JSON object.
"""

def classify_intent(message: str) -> IntentType:
    """
    Classifies message intent using LangChain and OpenAI gpt-4o-mini.
    Returns "expense" for expenses, "analytics" for analytics, or "unknown".
    
    Args:
        message: Message text
        
    Returns:
        Intent type: "expense", "analytics", or "unknown"
    """
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API key not configured. Using local classifier.")
        return "unknown"
    
    try:
        # Log the request
        logger.info(f"Sending request to LangChain for classification: '{message}'")
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("user", message)
        ])
        
        # Create the chain and run it
        chain = prompt | llm
        result = chain.invoke({})
        
        # Debug the result object
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result attributes: {dir(result)}")
        
        # Extract the intent from the result - handle different response structures
        if hasattr(result, 'content') and isinstance(result.content, str):
            response_content = result.content.strip()
            logger.info(f"LangChain raw response (from content): {response_content}")
        elif isinstance(result, str):
            response_content = result.strip()
            logger.info(f"LangChain raw response (from string): {response_content}")
        else:
            # Try to convert the entire result to a string
            try:
                response_content = str(result).strip()
                logger.info(f"LangChain raw response (from str conversion): {response_content}")
            except Exception as e:
                logger.error(f"Failed to extract content from result: {e}")
                return "unknown"
        
        # Parse the JSON response
        try:
            import json
            # First try to parse as JSON
            try:
                response_json = json.loads(response_content)
                if isinstance(response_json, dict) and "intention" in response_json:
                    intent = response_json["intention"].lower()
                    logger.info(f"Parsed intent from JSON: {intent}")
                else:
                    # If JSON parsed but doesn't have the right structure
                    logger.warning(f"JSON response missing 'intention' key: {response_json}")
                    intent = "unknown"
            except json.JSONDecodeError:
                # If not valid JSON, try to extract intent directly
                logger.warning(f"Response is not valid JSON: {response_content}")
                # Look for simple text response
                if response_content.lower() in ["expense", "analytics", "unknown"]:
                    intent = response_content.lower()
                    logger.info(f"Extracted intent from plain text: {intent}")
                else:
                    intent = "unknown"
            
            # Check if intent is one of the allowed values
            if intent in ["expense", "analytics", "unknown"]:
                return intent
            else:
                logger.warning(f"Unexpected intent: '{intent}'")
                return "unknown"
                
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            logger.error(f"Raw response was: {response_content}")
            return "unknown"
            
    except Exception as e:
        logger.error(f"Error classifying intent: {e}")
        return "unknown"