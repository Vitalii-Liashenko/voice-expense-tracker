import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from tools.transcriber import download_voice_message, transcribe_audio

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_telegram_file():
    """Fixture to create a mock Telegram File object."""
    mock_file = AsyncMock()
    mock_file.file_id = "test_file_id"
    mock_file.file_unique_id = "test_unique_id"
    return mock_file

async def test_download_voice_message_success(mock_telegram_file):
    """Test successful download of a voice message."""
    # Patch tempfile.NamedTemporaryFile to control the temporary file path
    with patch('tempfile.NamedTemporaryFile') as mock_named_temp_file:
        # Configure the mock for NamedTemporaryFile
        mock_temp_file_object = MagicMock()
        # Ensure the mock file object has a context manager interface if needed by `with`
        mock_temp_file_object.__enter__ = MagicMock(return_value=mock_temp_file_object)
        mock_temp_file_object.__exit__ = MagicMock(return_value=None)
        mock_temp_file_object.name = "mock_temp_download.ogg"
        mock_named_temp_file.return_value = mock_temp_file_object

        downloaded_path = await download_voice_message(mock_telegram_file)

        mock_telegram_file.download_to_drive.assert_called_once_with(
            custom_path=Path("mock_temp_download.ogg")
        )
        assert downloaded_path == Path("mock_temp_download.ogg")

async def test_download_voice_message_download_failure(mock_telegram_file):
    """Test download failure."""
    mock_telegram_file.download_to_drive.side_effect = Exception("Download failed")
    with pytest.raises(Exception, match="Download failed"):
        await download_voice_message(mock_telegram_file)

async def test_transcribe_audio_success():
    """Test successful audio transcription."""
    audio_data = b"dummy audio data"
    # Create a dummy audio file for the test
    # tempfile.NamedTemporaryFile is used as a context manager
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_audio_file_obj:
        tmp_audio_file_obj.write(audio_data)
        audio_path = Path(tmp_audio_file_obj.name)

    # Mock the OpenAI client's transcription creation
    # Patching 'tools.transcriber.client' assuming 'client' is an instance of OpenAI client in transcriber.py
    with patch('tools.transcriber.client.audio.transcriptions.create') as mock_transcribe_create:
        # The API returns a model object, not just a string. Let's mock that.
        mock_response_object = MagicMock()
        # Assuming the actual response object behaves like a string or has a direct string representation
        # For this example, let's assume it can be directly converted to the string we need.
        # If the actual object has attributes like .text, you'd mock that: mock_response_object.text = "Тестовий текст"
        # Based on the usage `return response`, it seems it might be a direct string or an object that converts to one.
        # For simplicity, let's assume the `response_format="text"` means the API returns a string-like object or string.
        mock_transcribe_create.return_value = "Тестовий транскрибований текст"

        result = await transcribe_audio(audio_path)

        # Check that the mock was called
        mock_transcribe_create.assert_called_once()
        
        # Verify arguments passed to the mock
        _, kwargs = mock_transcribe_create.call_args
        assert kwargs['model'] == 'whisper-1'
        assert kwargs['language'] == 'uk'
        assert kwargs['response_format'] == 'text'
        
        # Verify the file argument. The 'file' should be a file-like object.
        # We can check if the name attribute of the passed file object matches our path.
        assert hasattr(kwargs['file'], 'name')
        assert kwargs['file'].name == str(audio_path)
        # Optionally, read the file content passed to the mock if necessary and compare
        # kwargs['file'].seek(0) # Reset cursor if read before
        # assert kwargs['file'].read() == audio_data
        
        assert result == "Тестовий транскрибований текст"
        assert not audio_path.exists() # Ensure temporary file is cleaned up

async def test_transcribe_audio_api_failure():
    """Test transcription failure due to API error."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_audio_file_obj:
        tmp_audio_file_obj.write(b"dummy audio data")
        audio_path = Path(tmp_audio_file_obj.name)

    with patch('tools.transcriber.client.audio.transcriptions.create') as mock_transcribe_create:
        mock_transcribe_create.side_effect = Exception("API error")

        with pytest.raises(Exception, match="API error"):
            await transcribe_audio(audio_path)
        
        assert not audio_path.exists() # Ensure temporary file is cleaned up even on failure

async def test_transcribe_audio_file_not_found():
    """Test transcription when the audio file does not exist."""
    non_existent_path = Path("non_existent_audio_file.ogg")
    with pytest.raises(FileNotFoundError):
        await transcribe_audio(non_existent_path)
