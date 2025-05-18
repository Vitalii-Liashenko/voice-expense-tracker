"""
Whisper Transcriber Module

This module handles the integration with OpenAI's Whisper API for transcribing
voice messages to text in Ukrainian language.
"""

from .transcriber import download_voice_message, transcribe_audio

__all__ = ["download_voice_message", "transcribe_audio"] 