"""
Transcriber module for working with OpenAI's Whisper API.

This module provides functions for downloading Telegram voice messages
and transcribing them to text using OpenAI's Whisper API.
"""

import os
import logging
import tempfile
from openai import OpenAI
from pathlib import Path
from telegram import File as TelegramFile
from config import OPENAI_API_KEY

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

async def download_voice_message(voice_file: TelegramFile) -> Path:
    """
    Download a voice message from Telegram.
    
    Args:
        voice_file: The Telegram File object representing the voice message
        
    Returns:
        Path: Path to the downloaded voice message file
    """
    try:
        # Create a temporary file with .ogg extension (Telegram voice format)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
        temp_file.close()
        temp_path = Path(temp_file.name)
        
        # Download the voice file
        await voice_file.download_to_drive(custom_path=temp_path)
        logger.info(f"Voice message downloaded to {temp_path}")
        
        return temp_path
    except Exception as e:
        logger.error(f"Error downloading voice message: {e}")
        raise

async def transcribe_audio(audio_file_path: Path) -> str:
    """
    Transcribe an audio file using OpenAI's Whisper API.
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        str: Transcribed text in Ukrainian
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            # Call the OpenAI API to transcribe the audio
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="uk",  # Ukrainian language code
                response_format="text"
            )
        
        logger.info("Audio successfully transcribed")
        
        # Clean up the temporary file
        os.unlink(audio_file_path)
        
        return response
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        # Clean up the temporary file even if transcription fails
        if os.path.exists(audio_file_path):
            os.unlink(audio_file_path)
        raise 