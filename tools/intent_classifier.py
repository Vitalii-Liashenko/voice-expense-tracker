"""
Module for classifying message intents using LangChain and OpenAI gpt-4o-mini.
"""
import logging
import json
from typing import Literal, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field, validator

import config

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Intent types
IntentType = Literal["expense", "analytics", "unknown"]

# Define the output schema for intent classification
class IntentOutput(BaseModel):
    intention: IntentType = Field(description="The classified intent of the message")
    
    @validator('intention')
    def validate_intention(cls, v):
        if v not in ["expense", "analytics", "unknown"]:
            raise ValueError(f"Intention must be one of: expense, analytics, unknown")
        return v

# Create the output parser
output_parser = JsonOutputParser(pydantic_model=IntentOutput)

# LLM will be created inside the function to make it more testable

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
Example of response:
{{{{"intention": "expense"}}}}


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
    # Check if API key is available
    if not config.OPENAI_API_KEY:
        logger.warning("OpenAI API key not configured. Using local classifier.")
        return "unknown"
        
    # Log that we have an API key and will proceed
    logger.info("OpenAI API key found, proceeding with LLM classification")
    
    try:
        # Log the request
        logger.info(f"Sending request to LangChain for classification: '{message}'")
        
        # Create the LLM inside the function
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=config.OPENAI_API_KEY
        )
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("user", "{message}")
        ])
        
        # Create the chain with the output parser
        intent_chain = prompt | llm | output_parser
        
        try:
            # Run the chain
            result = intent_chain.invoke({"message": message})
            
            # Log the parsed result
            logger.info(f"Parsed intent: {result}")
            
            # Extract the intention from the result
            intent = result.get("intention", "unknown")
            logger.info(f"Extracted intent: {intent}")
            
            return intent if intent in ["expense", "analytics", "unknown"] else "unknown"
            
        except Exception as parsing_error:
            # Fallback to manual parsing if the output parser fails
            logger.warning(f"Output parser failed: {parsing_error}. Falling back to manual parsing.")
            
            # Create a chain without the output parser as fallback
            fallback_chain = prompt | llm
            result = fallback_chain.invoke({"message": message})
            
            # Debug the result object
            logger.info(f"Result type: {type(result)}")
            logger.info(f"Result attributes: {dir(result)}")
            
            # Get response content based on result type
            if hasattr(result, 'content') and isinstance(result.content, str):
                response_content = result.content.strip()
            elif isinstance(result, str):
                response_content = result.strip()
            else:
                response_content = str(result).strip()
                
            logger.info(f"LangChain raw response: {response_content}")
            
            # Try to parse JSON response
            try:
                response_json = json.loads(response_content)
                if isinstance(response_json, dict) and "intention" in response_json:
                    intent = response_json["intention"].lower()
                    logger.info(f"Parsed intent from JSON: {intent}")
                else:
                    logger.warning(f"JSON response missing 'intention' key: {response_json}")
                    intent = "unknown"
            except json.JSONDecodeError:
                # If not valid JSON, check if it's a direct intent string
                logger.warning(f"Response is not valid JSON: {response_content}")
                intent = response_content.lower() if response_content.lower() in ["expense", "analytics", "unknown"] else "unknown"
                logger.info(f"Extracted intent from text: {intent}")
            
            # Return intent if valid, otherwise return unknown
            return intent if intent in ["expense", "analytics"] else "unknown"
                
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return "unknown"
            
    except Exception as e:
        logger.error(f"Error classifying intent: {e}")
        return "unknown"