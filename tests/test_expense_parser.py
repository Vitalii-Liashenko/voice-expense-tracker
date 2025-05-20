"""
Tests for the expense parser functionality.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json

# Додаємо кореневу директорію проекту до шляху
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent.expense_parser import ExpenseParser, parse_expense
from tools.translator import translate_to_english


class TestExpenseParser(unittest.TestCase):
    """Tests for the expense parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.mock_response = MagicMock()
        self.mock_choice = MagicMock()
        self.mock_message = MagicMock()
        self.mock_message.content = '{"amount": 100, "category": "food"}'
        self.mock_choice.message = self.mock_message
        self.mock_response.choices = [self.mock_choice]
        self.mock_client.chat.completions.create.return_value = self.mock_response

    @patch('ai_agent.expense_parser.OPENAI_API_KEY', 'dummy_key')
    def test_successful_expense_parsing(self):
        """Test successful expense parsing."""
        with patch('ai_agent.expense_parser.client', self.mock_client):
            result = parse_expense("Купив продукти за 100 гривень")
            self.assertEqual(result["amount"], 100)
            self.assertEqual(result["category"], "food")

    @patch('ai_agent.expense_parser.OPENAI_API_KEY', 'dummy_key')
    def test_invalid_json_response(self):
        """Test handling of invalid JSON response."""
        self.mock_message.content = "Invalid JSON"
        
        with patch('ai_agent.expense_parser.client', self.mock_client):
            result = parse_expense("Купив продукти за 100 гривень")
            self.assertIsNone(result)

    @patch('ai_agent.expense_parser.OPENAI_API_KEY', None)
    def test_missing_api_key(self):
        """Test behavior when API key is missing."""
        result = parse_expense("Купив продукти за 100 гривень")
        self.assertIsNone(result)

    def test_expense_parser_class(self):
        """Test the ExpenseParser class."""
        with patch('ai_agent.expense_parser.ExpenseParser') as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse.return_value = {"amount": 100, "category": "food"}
            
            result = parse_expense("Купив продукти за 100 гривень")
            self.assertEqual(result["amount"], 100)
            self.assertEqual(result["category"], "food")

    def test_missing_amount(self):
        """Тест обробки відповіді без суми."""
        # Мокуємо відповідь без суми
        json_response = '{"category": "Entertainment", "description": "Похід у кіно"}'
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
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
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
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
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
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
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
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
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
        # Тестуємо функцію зворотної сумісності
        with patch('ai_agent.expense_parser.ExpenseParser') as mock_parser_class:
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
        with patch('ai_agent.expense_parser.ExpenseParser') as mock_parser_class:
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

    def test_expense_parsing_with_translation(self):
        """Тест парсингу витрат з перекладом з української на англійську."""
        # Мокуємо відповідь перекладу
        ukrainian_text = "Витратив 125.50 грн на продукти в АТБ"
        english_text = "Spent 125.50 UAH on groceries at ATB"
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
        # Перевіряємо переклад
        translated = translate_to_english(ukrainian_text)
        self.assertEqual(translated, english_text)
        
        # Мокуємо відповідь парсера
        json_response = '{"amount": 125.50, "category": "Foods", "description": "Grocery shopping at ATB"}'
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
        # Створюємо екземпляр парсера
        parser = ExpenseParser()
        
        # Тестуємо парсинг перекладеного тексту
        result = parser.parse_expense(translated)
        
        # Перевіряємо результат
        self.assertIsNotNone(result)
        self.assertEqual(result["amount"], 125.50)
        self.assertEqual(result["category"], "Foods")
        self.assertEqual(result["description"], "Grocery shopping at ATB")
        self.assertEqual(result["transcript"], ukrainian_text)

    def test_expense_parsing_with_translation_failure(self):
        """Тест парсингу витрат при помилці перекладу."""
        # Мокуємо помилку перекладу
        ukrainian_text = "Витратив 100 грн на каву"
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
        # Перевіряємо, що переклад повертає None
        translated = translate_to_english(ukrainian_text)
        self.assertIsNone(translated)
        
        # Перевіряємо, що парсер повертає None при помилці перекладу
        parser = ExpenseParser()
        result = parser.parse_expense(ukrainian_text)
        self.assertIsNone(result)

    def test_expense_parsing_with_translation_and_invalid_json(self):
        """Тест парсингу витрат з перекладом та невалідним JSON."""
        # Мокуємо відповідь перекладу
        ukrainian_text = "Витратив 200 грн на обід"
        english_text = "Spent 200 UAH on lunch"
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
        # Перевіряємо переклад
        translated = translate_to_english(ukrainian_text)
        self.assertEqual(translated, english_text)
        
        # Мокуємо невалідну JSON відповідь
        self.mock_message.content = "Invalid JSON"
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
        # Створюємо екземпляр парсера
        parser = ExpenseParser()
        
        # Тестуємо парсинг
        result = parser.parse_expense(translated)
        
        # Перевіряємо результат
        self.assertIsNone(result)

    def test_expense_parsing_with_translation_and_missing_amount(self):
        """Тест парсингу витрат з перекладом та відсутньою сумою."""
        # Мокуємо відповідь перекладу
        ukrainian_text = "Ходив у кіно"
        english_text = "Went to the cinema"
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
        # Перевіряємо переклад
        translated = translate_to_english(ukrainian_text)
        self.assertEqual(translated, english_text)
        
        # Мокуємо відповідь без суми
        json_response = '{"category": "Entertainment", "description": "Cinema visit"}'
        self.mock_client.chat.completions.create.return_value = self.mock_response
        
        # Створюємо екземпляр парсера
        parser = ExpenseParser()
        
        # Тестуємо парсинг
        result = parser.parse_expense(translated)
        
        # Перевіряємо результат
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main() 