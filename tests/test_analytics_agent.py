import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import logging

# Temporarily adjust path to import from parent directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_agent.analytics_agent import (
    _get_period_from_text,
    _extract_category_from_text,
    _format_period_text # Assuming we might test this later
)
from config import EXPENSE_CATEGORIES, OPENAI_API_KEY

# Suppress logging during tests
logging.disable(logging.CRITICAL)

class TestAnalyticsAgentHelpers(unittest.TestCase):

    def setUp(self):
        # self.today = datetime.now() # We will mock datetime.now directly in the test
        # Ensure EXPENSE_CATEGORIES is available for mocks if needed by underlying code
        self.original_expense_categories = list(EXPENSE_CATEGORIES)
        if "TestCategory" not in EXPENSE_CATEGORIES:
             EXPENSE_CATEGORIES.append("TestCategory")

    def tearDown(self):
        global EXPENSE_CATEGORIES
        EXPENSE_CATEGORIES = self.original_expense_categories
        logging.disable(logging.NOTSET) # Re-enable logging

    @patch('ai_agent.analytics_agent.datetime')
    def test_get_period_from_text(self, mock_datetime_class):
        # Set a fixed 'today' for deterministic testing, e.g., a Thursday
        fixed_today = datetime(2025, 5, 22, 10, 0, 0) # Uses the 'datetime' imported by the test file (real one)
        mock_datetime_class.now.return_value = fixed_today

        # Ensure that calling the mocked datetime class as a constructor
        # (e.g., datetime(2025,1,1) inside _get_period_from_text)
        # still produces real datetime objects by delegating to the original datetime class.
        # The 'datetime' on the right side of lambda is the one imported at the top of this test file.
        mock_datetime_class.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        # Today
        start, end = _get_period_from_text("show expenses for today")
        self.assertEqual(start.date(), fixed_today.date())
        self.assertIsNone(end)

        # Yesterday
        start, end = _get_period_from_text("what about yesterday?")
        yesterday = fixed_today - timedelta(days=1)
        self.assertEqual(start.date(), yesterday.date())
        self.assertIsNotNone(end)
        self.assertEqual(end.date(), yesterday.date())
        self.assertEqual(end.time(), datetime(1,1,1, 23, 59, 59).time())

        # Current Week
        start, end = _get_period_from_text("expenses this week")
        start_of_week = fixed_today - timedelta(days=fixed_today.weekday())
        self.assertEqual(start.date(), start_of_week.date())
        self.assertIsNone(end) # Current week goes to now

        # Last Week
        start, end = _get_period_from_text("expenses last week")
        start_of_last_week = fixed_today - timedelta(days=fixed_today.weekday() + 7)
        end_of_last_week_date = (start_of_last_week + timedelta(days=6)).date()
        self.assertEqual(start.date(), start_of_last_week.date())
        self.assertIsNotNone(end)
        self.assertEqual(end.date(), end_of_last_week_date)

        # Current Month
        start, end = _get_period_from_text("this month's spending")
        start_of_month = fixed_today.replace(day=1)
        self.assertEqual(start.date(), start_of_month.date())
        self.assertIsNone(end)

        # Last Month
        start, end = _get_period_from_text("how much last month")
        first_day_current_month = fixed_today.replace(day=1)
        last_day_last_month_date = (first_day_current_month - timedelta(days=1)).date()
        first_day_last_month_date = last_day_last_month_date.replace(day=1)
        self.assertEqual(start.date(), first_day_last_month_date)
        self.assertIsNotNone(end)
        self.assertEqual(end.date(), last_day_last_month_date)

        # Default (current month)
        start, end = _get_period_from_text("show my expenses")
        self.assertEqual(start.date(), fixed_today.replace(day=1).date())
        self.assertIsNone(end)

    @patch('ai_agent.analytics_agent.OPENAI_API_KEY', 'fake_api_key')
    @patch('ai_agent.analytics_agent.category_chain')
    def test_extract_category_from_text_success(self, mock_category_chain):
        mock_category_chain.invoke.return_value = {"category": "TestCategory"}
        result = _extract_category_from_text("how much for TestCategory")
        self.assertEqual(result, "TestCategory")
        mock_category_chain.invoke.assert_called_once_with({"message": "how much for TestCategory"})

    @patch('ai_agent.analytics_agent.OPENAI_API_KEY', 'fake_api_key')
    @patch('ai_agent.analytics_agent.category_chain')
    def test_extract_category_from_text_unknown_category(self, mock_category_chain):
        mock_category_chain.invoke.return_value = {"category": "NonExistentCategory"}
        result = _extract_category_from_text("how much for NonExistentCategory")
        self.assertIsNone(result)

    @patch('ai_agent.analytics_agent.OPENAI_API_KEY', 'fake_api_key')
    @patch('ai_agent.analytics_agent.category_chain')
    def test_extract_category_from_text_langchain_error(self, mock_category_chain):
        mock_category_chain.invoke.side_effect = Exception("LLM error")
        result = _extract_category_from_text("any category query")
        self.assertIsNone(result)

    @patch('ai_agent.analytics_agent.OPENAI_API_KEY', None)
    def test_extract_category_from_text_no_api_key(self):
        result = _extract_category_from_text("any category query")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
