"""
Module for translating text between languages using OpenAI.
"""
import os
import logging
import openai
from typing import Optional

from config import OPENAI_API_KEY

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

def translate_to_english(text: str) -> Optional[str]:
    """
    Translates text from Ukrainian to English using OpenAI.
    
    Args:
        text: Text in Ukrainian to translate
        
    Returns:
        Translated text in English or None if translation failed
    """
    if not client or not OPENAI_API_KEY:
        logger.error("OpenAI client not initialized")
        return None
    
    try:
        logger.info(f"Translating text: '{text}'")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a translator. Translate the following Ukrainian text to English. Keep the meaning and context intact."},
                {"role": "user", "content": text}
            ],
            temperature=0.2
        )
        
        translated_text = response.choices[0].message.content.strip()
        logger.info(f"Translation successful: '{translated_text}'")
        return translated_text
        
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return None 