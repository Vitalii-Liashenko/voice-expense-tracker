import unittest
from unittest.mock import patch, MagicMock
import logging

# Temporarily adjust path to import from parent directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_agent.expenses_agent import ExpenseParser, ExpenseOutput
from config import EXPENSE_CATEGORIES

# Suppress logging during tests
logging.disable(logging.CRITICAL)

class TestExpenseParser(unittest.TestCase):

    def setUp(self):
        # Ensure EXPENSE_CATEGORIES is available for ExpenseOutput validator
        self.original_expense_categories = list(EXPENSE_CATEGORIES)
        if "TestCategory" not in EXPENSE_CATEGORIES:
            EXPENSE_CATEGORIES.append("TestCategory")
        self.parser = ExpenseParser()

    def tearDown(self):
        # Restore original EXPENSE_CATEGORIES
        global EXPENSE_CATEGORIES
        EXPENSE_CATEGORIES = self.original_expense_categories
        logging.disable(logging.NOTSET) # Re-enable logging

    @patch('ai_agent.expenses_agent.OPENAI_API_KEY', 'fake_api_key')
    @patch('ai_agent.expenses_agent.expense_chain')
    def test_parse_expense_success(self, mock_expense_chain):
        mock_expense_chain.invoke.return_value = {
            "amount": 100.50,
            "category": "TestCategory",
            "description": "Test expense"
        }
        message = "Buy something for 100.50"
        result = self.parser.parse_expense(message)
        self.assertIsNotNone(result)
        self.assertEqual(result['amount'], 100.50)
        self.assertEqual(result['category'], 'TestCategory')
        self.assertEqual(result['description'], 'Test expense')
        mock_expense_chain.invoke.assert_called_once_with({"message": message})

    @patch('ai_agent.expenses_agent.OPENAI_API_KEY', None)
    def test_parse_expense_no_api_key(self):
        message = "Buy something for 100.50"
        result = self.parser.parse_expense(message)
        self.assertIsNone(result)

    @patch('ai_agent.expenses_agent.OPENAI_API_KEY', 'fake_api_key')
    @patch('ai_agent.expenses_agent.expense_chain')
    def test_parse_expense_missing_essential_fields(self, mock_expense_chain):
        mock_expense_chain.invoke.return_value = {
            "amount": None,
            "category": None,
            "description": "Vague expense"
        }
        message = "Something happened"
        result = self.parser.parse_expense(message)
        self.assertIsNone(result)
        mock_expense_chain.invoke.assert_called_once_with({"message": message})

    @patch('ai_agent.expenses_agent.OPENAI_API_KEY', 'fake_api_key')
    @patch('ai_agent.expenses_agent.expense_chain')
    def test_parse_expense_langchain_exception(self, mock_expense_chain):
        mock_expense_chain.invoke.side_effect = Exception("LangChain API error")
        message = "Buy something for 100.50"
        result = self.parser.parse_expense(message)
        self.assertIsNone(result)
        mock_expense_chain.invoke.assert_called_once_with({"message": message})

    @patch('ai_agent.expenses_agent.OPENAI_API_KEY', 'fake_api_key')
    @patch('ai_agent.expenses_agent.expense_chain')
    def test_parse_expense_valid_but_incomplete_data(self, mock_expense_chain):
        # Test case where e.g. amount is present but category is None (should be handled by logic inside parse_expense)
        # According to current logic, if amount OR category is None, but not both, it might still be an issue
        # The current code: `if result.get("amount") is None and result.get("category") is None:` means if one is present, it passes this check.
        # Then `if expense_data["amount"] is not None and expense_data["category"] is not None:` is the stricter check.
        mock_expense_chain.invoke.return_value = {
            "amount": 100.50,
            "category": None, # Missing category
            "description": "Test expense without category"
        }
        message = "Buy something for 100.50 without category"
        result = self.parser.parse_expense(message)
        self.assertIsNone(result) # Expect None because category is missing for a valid expense
        mock_expense_chain.invoke.assert_called_once_with({"message": message})


if __name__ == '__main__':
    unittest.main()
