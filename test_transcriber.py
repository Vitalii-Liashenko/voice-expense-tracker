import asyncio
import logging
import os
from pathlib import Path
from telegram import Bot, File as TelegramFile
from tools.transcriber import download_voice_message, transcribe_audio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_transcription():
    try:
        # Initialize bot with your token
        bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        
        # Test file path - replace with your test audio file
        test_audio_path = Path("test_audio.ogg")
        
        # Create a mock TelegramFile object with bot instance
        mock_voice_file = TelegramFile(
            file_id="test_file_id",
            file_unique_id="test_unique_id",
            file_size=1024,
            file_path=str(test_audio_path),
            bot=bot
        )
        
        # Test download
        logger.info("Testing voice message download...")
        downloaded_path = await download_voice_message(mock_voice_file)
        logger.info(f"Downloaded to: {downloaded_path}")
        
        # Test transcription
        logger.info("Testing audio transcription...")
        transcription = await transcribe_audio(downloaded_path)
        logger.info(f"Transcription result: {transcription}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        # Close the bot session
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_transcription()) 