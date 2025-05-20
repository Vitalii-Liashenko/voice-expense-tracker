"""
Tests for the Whisper transcriber module
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from tools.transcriber import download_voice_message, transcribe_audio

# Mock response for OpenAI transcription
MOCK_TRANSCRIPTION = "Купив продукти за 250 гривень"

@pytest.fixture
def mock_voice_file():
    """Create a mock Telegram voice file"""
    voice_file = AsyncMock()
    voice_file.download_to_drive = AsyncMock()
    return voice_file

@pytest.fixture
def temp_audio_file():
    """Create a temporary audio file for testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
    temp_file.write(b"dummy audio data")
    temp_file.close()
    yield Path(temp_file.name)
    # Cleanup after test
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)

@pytest.mark.asyncio
async def test_download_voice_message(mock_voice_file):
    """Test downloading a voice message"""
    result = await download_voice_message(mock_voice_file)
    
    assert isinstance(result, Path)
    assert result.suffix == ".ogg"
    assert mock_voice_file.download_to_drive.called
    
    # Clean up the temp file
    if os.path.exists(result):
        os.unlink(result)

@pytest.mark.asyncio
@patch('tools.transcriber.client')
async def test_transcribe_audio(mock_client, temp_audio_file):
    """Test transcribing audio using the OpenAI API"""
    # Configure the mock client
    mock_transcription = MagicMock()
    mock_transcription.create.return_value = MOCK_TRANSCRIPTION
    mock_client.audio.transcriptions = mock_transcription
    
    # Test the transcription function
    result = await transcribe_audio(temp_audio_file)
    
    assert result == MOCK_TRANSCRIPTION
    mock_client.audio.transcriptions.create.assert_called_once()
    
    # Verify the file was cleaned up
    assert not os.path.exists(temp_audio_file)

@pytest.mark.asyncio
@patch('tools.transcriber.client')
async def test_transcribe_audio_handles_errors(mock_client, temp_audio_file):
    """Test error handling during audio transcription"""
    # Configure the mock client to raise an exception
    mock_transcription = MagicMock()
    mock_transcription.create.side_effect = Exception("API Error")
    mock_client.audio.transcriptions = mock_transcription
    
    # Test the transcription function with error handling
    with pytest.raises(Exception):
        await transcribe_audio(temp_audio_file)
    
    # Verify the file was cleaned up even if an error occurred
    assert not os.path.exists(temp_audio_file) 