"""
Tests for the AI agent functionality
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from ai_agent.intent_classifier import classify_intent
from ai_agent.expense_parser import parse_expense

# Skip the first test that tries to use the real API
@pytest.mark.skip(reason="Requires real OpenAI API key")
def test_intent_classifier():
    """Test the intent classifier with various inputs"""
    # Test expense intents
    assert classify_intent("Купив продукти за 300 гривень") == "expense"
    assert classify_intent("Заплатив за таксі 150 грн") == "expense"
    assert classify_intent("Витратив 400 грн на одяг") == "expense"
    assert classify_intent("Сьогодні потратив 500 гривень на ресторан") == "expense"
    
    # Test analytics intents
    assert classify_intent("Покажи аналітику витрат") == "analytics"
    assert classify_intent("Скільки я витратив за цей місяць?") == "analytics"
    assert classify_intent("Який залишок бюджету?") == "analytics"
    assert classify_intent("Показати звіт за тиждень") == "analytics"
    
    # Test unknown intents
    assert classify_intent("Привіт, як справи?") == "unknown"
    assert classify_intent("Котра година?") == "unknown"

@patch('ai_agent.open_ai_intent_classifier.OPENAI_API_KEY', 'dummy_key')
def test_classify_intent_expense():
    """Тест класифікації повідомлення про витрату."""
    # Створюємо мок для клієнта OpenAI
    mock_client = MagicMock()
    
    # Налаштовуємо відповідь від OpenAI
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = '{"intention": "expense"}'
    mock_choice.message = mock_message
    mock_resp.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_resp
    
    # Застосовуємо мок клієнта
    with patch('ai_agent.open_ai_intent_classifier.client', mock_client):
        # Тестуємо класифікацію
        intent = classify_intent("Купив хліб за 25 грн")
        
        # Перевіряємо результат
        assert intent == "expense"

@patch('ai_agent.open_ai_intent_classifier.OPENAI_API_KEY', 'dummy_key')
def test_classify_intent_analytics():
    """Тест класифікації повідомлення про аналітику."""
    # Створюємо мок для клієнта OpenAI
    mock_client = MagicMock()
    
    # Налаштовуємо відповідь від OpenAI
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = '{"intention": "analytics"}'
    mock_choice.message = mock_message
    mock_resp.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_resp
    
    # Застосовуємо мок клієнта
    with patch('ai_agent.open_ai_intent_classifier.client', mock_client):
        # Тестуємо класифікацію
        intent = classify_intent("Скільки я витратив на їжу?")
        
        # Перевіряємо результат
        assert intent == "analytics"

@patch('ai_agent.open_ai_intent_classifier.OPENAI_API_KEY', None)
def test_classify_intent_no_api_key():
    """Тест класифікації повідомлення без API ключа."""
    # Тестуємо класифікацію без API ключа
    intent = classify_intent("Це тестове повідомлення")
    
    # Без API ключа має повертатися "unknown"
    assert intent == "unknown"

def test_expense_parser():
    """Test the expense parser with various inputs"""
    # Test basic expense parsing
    expense = parse_expense("Купив продукти в АТБ за 350 грн")
    assert expense is not None
    assert expense["amount"] == 350.0
    assert expense["category"] == "Foods"
    assert "АТБ" in expense["description"]
    
    # Test with different category
    expense = parse_expense("Заплатив за таксі 200 гривень")
    assert expense is not None
    assert expense["amount"] == 200.0
    assert expense["category"] == "Transportation"
    assert "таксі" in expense["description"]
    
    # Test with date
    expense = parse_expense("Вчора купив квитки до театру за 450 грн")
    assert expense is not None
    assert expense["amount"] == 450.0
    assert expense["category"] == "Entertainment"
    assert expense["date"] is not None  # Should recognize "вчора"
    
    # Test with low priority category (falls back to Others)
    expense = parse_expense("Витратив 300 грн на щось")
    assert expense is not None
    assert expense["amount"] == 300.0
    assert expense["category"] == "Others"

def test_expense_parser_negative_cases():
    """Test the expense parser with inputs that should not parse as expenses"""
    # No amount
    assert parse_expense("Купив продукти") is None
    
    # Conflicting categories (should still work but choose one)
    expense = parse_expense("Купив продукти та одяг за 1000 грн")
    assert expense is not None
    assert expense["amount"] == 1000.0
    # Should choose the category with higher score based on more keyword matches 