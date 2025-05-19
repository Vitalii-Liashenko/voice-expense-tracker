"""
Тести для парсера витрат з використанням OpenAI gpt-4o-mini.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json

# Додаємо кореневу директорію проекту до шляху
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent.expense_parser import ExpenseParser, parse_expense


class TestOpenAIExpenseParser(unittest.TestCase):
    """Тести для ExpenseParser з використанням OpenAI gpt-4o-mini."""

    def setUp(self):
        """Встановлює необхідні моки перед виконанням тестів."""
        # Створюємо патч для клієнта OpenAI
        self.openai_patcher = patch('openai.OpenAI')
        self.mock_openai = self.openai_patcher.start()
        
        # Створюємо мок для відповіді від OpenAI
        self.mock_client = MagicMock()
        self.mock_openai.return_value = self.mock_client
        
        # Встановлюємо змінну оточення для API ключа
        if "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = "test_api_key"

    def tearDown(self):
        """Очищує всі моки після виконання тестів."""
        self.openai_patcher.stop()
        
        # Очищуємо змінну оточення, якщо вона була встановлена в тесті
        if "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"] == "test_api_key":
            del os.environ["OPENAI_API_KEY"]

    def _mock_openai_response(self, json_response):
        """Допоміжний метод для встановлення моку відповіді від OpenAI."""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = json_response
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        self.mock_client.chat.completions.create.return_value = mock_response

    def test_successful_expense_parsing(self):
        """Тест успішного парсингу витрат."""
        # Мокуємо відповідь від OpenAI
        json_response = '{"amount": 125.50, "category": "Foods", "description": "Закупка в АТБ"}'
        self._mock_openai_response(json_response)
        
        # Створюємо екземпляр парсера
        parser = ExpenseParser()
        
        # Тестуємо парсинг
        result = parser.parse_expense("Витратив 125.50 грн на продукти в АТБ")
        
        # Перевіряємо результат
        self.assertIsNotNone(result)
        self.assertEqual(result["amount"], 125.50)
        self.assertEqual(result["category"], "Foods")
        self.assertEqual(result["description"], "Закупка в АТБ")
        self.assertEqual(result["transcript"], "Витратив 125.50 грн на продукти в АТБ")

    def test_invalid_json_response(self):
        """Тест обробки невалідного JSON від OpenAI."""
        # Мокуємо невалідну JSON відповідь
        self._mock_openai_response("Invalid JSON")
        
        # Створюємо екземпляр парсера
        parser = ExpenseParser()
        
        # Тестуємо парсинг
        result = parser.parse_expense("Витратив 100 грн на каву")
        
        # Перевіряємо результат
        self.assertIsNone(result)

    def test_missing_amount(self):
        """Тест обробки відповіді без суми."""
        # Мокуємо відповідь без суми
        json_response = '{"category": "Entertainment", "description": "Похід у кіно"}'
        self._mock_openai_response(json_response)
        
        # Створюємо екземпляр парсера
        parser = ExpenseParser()
        
        # Тестуємо парсинг
        result = parser.parse_expense("Ходив у кіно")
        
        # Перевіряємо результат
        self.assertIsNone(result)

    def test_invalid_category(self):
        """Тест обробки невалідної категорії."""
        # Мокуємо відповідь з невалідною категорією
        json_response = '{"amount": 500, "category": "InvalidCategory", "description": "Покупка квитків"}'
        self._mock_openai_response(json_response)
        
        # Створюємо екземпляр парсера
        parser = ExpenseParser()
        
        # Тестуємо парсинг
        result = parser.parse_expense("Купив квитки на 500 грн")
        
        # Перевіряємо результат
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "Others")  # Має бути замінено на Others

    def test_empty_response(self):
        """Тест обробки порожньої відповіді."""
        # Мокуємо порожню відповідь
        json_response = '{}'
        self._mock_openai_response(json_response)
        
        # Створюємо екземпляр парсера
        parser = ExpenseParser()
        
        # Тестуємо парсинг
        result = parser.parse_expense("Це не витрата")
        
        # Перевіряємо результат
        self.assertIsNone(result)

    def test_empty_description(self):
        """Тест обробки відповіді без опису."""
        # Мокуємо відповідь без опису
        json_response = '{"amount": 300, "category": "Transportation", "description": ""}'
        self._mock_openai_response(json_response)
        
        # Створюємо екземпляр парсера
        parser = ExpenseParser()
        
        # Тестуємо парсинг
        result = parser.parse_expense("Таксі 300 грн")
        
        # Перевіряємо результат
        self.assertIsNotNone(result)
        self.assertEqual(result["description"], "Без опису")

    def test_legacy_function(self):
        """Тест функції зворотної сумісності."""
        # Мокуємо відповідь від OpenAI
        json_response = '{"amount": 150, "category": "Housing", "description": "Оплата інтернету"}'
        self._mock_openai_response(json_response)
        
        # Тестуємо функцію зворотної сумісності
        with patch('ai_agent.open_ai_expense_parser.ExpenseParser') as mock_parser_class:
            # Створюємо мок для екземпляра класу
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            
            # Встановлюємо очікуваний результат
            expected_result = {
                "amount": 150,
                "category": "Housing",
                "description": "Оплата інтернету",
                "transcript": "Заплатив 150 грн за інтернет"
            }
            mock_parser.parse_expense.return_value = expected_result
            
            # Викликаємо функцію
            result = parse_expense("Заплатив 150 грн за інтернет")
            
            # Перевіряємо результат
            self.assertEqual(result, expected_result)

    def test_parse_expense_invokes_class_method(self):
        test_message = "Купив продукти за 150 грн"
        expected_result = {"amount": 150.0, "category": "Foods", "description": "Продукти"}
        
        # Створюємо мок для ExpenseParser
        with patch('ai_agent.open_ai_expense_parser.ExpenseParser') as mock_parser_class:
            # Налаштовуємо мок об'єкт і його метод parse_expense
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse_expense.return_value = expected_result
            mock_parser_class.return_value = mock_parser_instance
            
            # Викликаємо функцію parse_expense
            result = parse_expense(test_message)
            
            # Перевіряємо, що ExpenseParser був викликаний
            mock_parser_class.assert_called_once()
            
            # Перевіряємо, що метод parse_expense був викликаний з правильними аргументами
            mock_parser_instance.parse_expense.assert_called_once_with(test_message)
            
            # Перевіряємо результат
            self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main() 