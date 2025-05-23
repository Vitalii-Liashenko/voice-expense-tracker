import unittest
from unittest.mock import patch, MagicMock
import logging

from tools.intent_classifier import classify_intent, IntentType

class TestIntentClassifier(unittest.TestCase):

    def setUp(self):
        # Disable logging for most tests to keep output clean, can be enabled for specific tests
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        # Re-enable logging
        logging.disable(logging.NOTSET)

    def test_classify_intent_expense_successful(self):
        # Setup the mocks
        with patch('config.OPENAI_API_KEY', 'fake_key'):
            with patch('tools.intent_classifier.ChatOpenAI') as mock_chat_openai:
                # Setup the mock LLM instance
                mock_llm_instance = MagicMock()
                mock_chat_openai.return_value = mock_llm_instance
                
                # Setup the mock response
                mock_response = MagicMock()
                mock_response.content = '{"intention": "expense"}'
                mock_llm_instance.invoke.return_value = mock_response
                
                # Call the function
                intent = classify_intent("I bought groceries for 20 dollars")
                
                # Assertions
                self.assertEqual(intent, "expense")
                mock_llm_instance.invoke.assert_called_once()

    def test_classify_intent_analytics_successful(self):
        # Setup the mocks
        with patch('config.OPENAI_API_KEY', 'fake_key'):
            with patch('tools.intent_classifier.ChatOpenAI') as mock_chat_openai:
                # Setup the mock LLM instance
                mock_llm_instance = MagicMock()
                mock_chat_openai.return_value = mock_llm_instance
                
                # Setup the mock response
                mock_response = MagicMock()
                mock_response.content = '{"intention": "analytics"}'
                mock_llm_instance.invoke.return_value = mock_response
                
                # Call the function
                intent = classify_intent("How much did I spend on food last month?")
                
                # Assertions
                self.assertEqual(intent, "analytics")
                mock_llm_instance.invoke.assert_called_once()

    def test_classify_intent_unknown_successful(self):
        # Setup the mocks
        with patch('config.OPENAI_API_KEY', 'fake_key'):
            with patch('tools.intent_classifier.ChatOpenAI') as mock_chat_openai:
                # Setup the mock LLM instance
                mock_llm_instance = MagicMock()
                mock_chat_openai.return_value = mock_llm_instance
                
                # Setup the mock response
                mock_response = MagicMock()
                mock_response.content = '{"intention": "unknown"}'
                mock_llm_instance.invoke.return_value = mock_response
                
                # Call the function
                intent = classify_intent("What is the weather like today?")
                
                # Assertions
                self.assertEqual(intent, "unknown")
                mock_llm_instance.invoke.assert_called_once()

if __name__ == '__main__':
    unittest.main()
