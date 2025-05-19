# Voice Expense Tracker

Голосовий трекер витрат за допомогою Telegram бота. Дозволяє записувати витрати голосом, аналізувати бюджет і отримувати звіти.

## Основні можливості

- Запис витрат через голосові повідомлення
- Автоматичне розпізнавання суми, категорії та опису витрат
- Аналіз витрат за категоріями та періодами
- Перевірка лімітів бюджету
- Зручний Telegram-інтерфейс

## Технології

- Python 3.9+
- Telegram Bot API
- OpenAI Whisper API для розпізнавання мовлення
- Claude API для класифікації намірів
- PostgreSQL для зберігання даних
- SQLAlchemy ORM

## Налаштування

### 1. Створення .env файлу

Створіть файл `.env.local` в кореневій директорії проекту і вкажіть наступні змінні:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_expense_tracker
DB_USER=postgres
DB_PASSWORD=your_password

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
AUTHOR_USER_ID=your_telegram_user_id

OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 2. Отримання API ключів

- **Telegram Bot Token**: Створіть бота через [@BotFather](https://t.me/BotFather) і отримайте токен
- **Telegram User ID**: Використовуйте [@userinfobot](https://t.me/userinfobot) для отримання ID
- **OpenAI API Key**: Отримайте на [платформі OpenAI](https://platform.openai.com/)
- **Anthropic API Key**: Зареєструйтесь на [платформі Anthropic](https://console.anthropic.com/)

### 3. Запуск бази даних

```bash
docker-compose up -d
```

### 4. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 5. Запуск

```bash
python bot.py
```

## Структура проекту

- `ai_agent/` - Модулі для аналізу та класифікації повідомлень
  - `intent_classifier.py` - Класифікатор намірів (витрати vs аналітика)
  - `expense_parser.py` - Парсер інформації про витрати
  - `analytics_agent.py` - Генерація аналітики
- `db/` - Модулі для роботи з базою даних
- `telegram_bot/` - Модулі для роботи з Telegram ботом
- `whisper_transcriber/` - Обробка голосових повідомлень

## Використання Claude API

Проект використовує Claude 3.7 Sonnet для класифікації намірів користувача та парсингу витрат. Основні моменти:

1. Для використання Claude API необхідно отримати API ключ з [Anthropic Console](https://console.anthropic.com/)
2. Додати ключ у файл `.env.local` як `ANTHROPIC_API_KEY=your_key_here`
3. При відсутності ключа система автоматично перемикається на локальну класифікацію намірів

### Модуль expense_parser

Новий парсер витрат використовує Claude 3.7 Sonnet для аналізу текстових повідомлень та витягування інформації про витрати:

1. **Принцип роботи**: парсер передає текстове повідомлення в Claude API, який аналізує його та повертає структурований JSON
2. **Формат відповіді**: JSON з полями `amount`, `category`, `description`
3. **Переваги**: висока точність розпізнавання українських текстів, гнучкість у розумінні різних формулювань
4. **Обробка помилок**: валідація отриманого JSON, обробка відсутніх або невалідних полів, фоллбек на категорію "Others"

Приклад використання:
```python
from ai_agent.claude_expense_parser import ExpenseParser

# Створити екземпляр парсера
parser = ExpenseParser()

# Використати парсер для аналізу витрати
result = parser.parse_expense("Купив продукти в АТБ за 235,50 грн")

# Приклад результату
# {
#   "amount": 235.5,
#   "category": "Foods",
#   "description": "Купівля продуктів в АТБ",
#   "transcript": "Купив продукти в АТБ за 235,50 грн"
# }
```

### Внутрішній механізм роботи intent_classifier:

1. Отримання тексту від користувача
2. Відправка запиту до Claude API з чітким промптом для класифікації
3. Обробка відповіді та визначення наміру: "expense", "analytics" або "unknown"
4. Логування результатів класифікації
5. Використання fallback-класифікатора при помилках або відсутності ключа

## Тестування

Проект містить модульні та інтеграційні тести для валідації функціональності:

- `tests/test_claude_expense_parser.py` - юніт-тести для парсера витрат з моками Claude API
- `tests/integration_test_parser.py` - інтеграційні тести з реальними прикладами повідомлень

Для запуску тестів:

```bash
# Запуск юніт-тестів
python -m unittest tests/test_claude_expense_parser.py

# Запуск інтеграційних тестів (потрібен API ключ)
python tests/integration_test_parser.py
```
