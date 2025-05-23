# Voice Expense Tracker

A voice expense tracker using a Telegram bot. Allows you to record expenses by voice or text, analyze your budget, and receive reports.

## Key Features

- Record expenses via voice or text messages in Ukrainian
- Automatic recognition of amount, category, and description of expenses
- Analysis of expenses by categories and periods
- Budget limit checks
- Convenient Telegram interface

## Technologies

- Python 3.12+
- Telegram Bot API
- OpenAI Whisper API for speech recognition
- OpenAI API for intent classification
- PostgreSQL for data storage
- SQLAlchemy ORM
- LangChain to simplify integration with AI services

## Setup

### 1. Clone the repository
git clone https://github.com/Vitalii-Liashenko/youtube-checker-agent.git

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create .env file

Create a `.env` file in the root directory of the project and specify the following variables:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_expense_tracker
DB_USER=postgres
DB_PASSWORD=your_password

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
AUTHOR_USER_ID=your_telegram_user_id

OPENAI_API_KEY=your_openai_api_key
```

### 4. Obtain API keys

- **Telegram Bot Token**: Create a bot via [@BotFather](https://t.me/BotFather) and get the token
- **Telegram User ID**: Use [@userinfobot](https://t.me/userinfobot) to get your ID
- **OpenAI API Key**: Obtain it on the [OpenAI platform](https://platform.openai.com/)


### 5. Start the database

```bash
docker-compose up -d
```

### 6. Run

```bash
python run.py
```

## Project Structure

- `ai_agent/` - Modules for AI logic processing and interaction with LLM
  - `analytics_agent.py` - Agent for processing analytical queries (uses LangChain SQL tool)
  - `expenses_agent.py` - Agent for parsing expense details from messages
- `db/` - Modules for working with the database
  - `database.py` - Database connection settings (e.g., SQLAlchemy engine, session)
  - `models.py` - SQLAlchemy ORM models for database tables (e.g., expenses, users, limits)
  - `queries.py` - CRUD operations and other functions for database queries
- `telegram_bot/` - Modules for the Telegram bot
  - `bot.py` - Main logic of the Telegram bot, including dispatcher setup
  - `handlers.py` - Message handlers for various commands and message types
  - `message_processor.py` - Processes incoming messages before passing them to AI agents
- `tools/` - Auxiliary tools and utilities
  - `intent_classifier.py` - LLM-based intent classifier (expense, query, etc.)
  - `transcriber.py` - Transcription of voice messages into text (e.g., using Whisper API)
  - `translator.py` - Text translation capabilities

## Using the OpenAI API

The project uses OpenAI to classify user intents and parse expenses. Key points:

1. To use the OpenAI API, you need to obtain an API key from the [OpenAI Console](https://platform.openai.com/)
2. Add the key to the `.env` file as `OPENAI_API_KEY=your_key_here`

### Expenses_agent

Expenses_agent uses OpenAI to analyze text messages and extract expense information:

1. **Operating principle**: the agent sends a text message to the OpenAI API, which analyzes it and returns a structured JSON
2. **Response format**: JSON with `amount`, `category`, `description` fields
3. **Advantages**: high accuracy in recognizing texts, flexibility in understanding different phrasings
4. **Error handling**: validation of the received JSON, handling of missing or invalid fields, fallback to the "Others" category

Example usage:
```python
# Use the parser to analyze an expense
result = parse_expense("Bought groceries at ATB for 235.50 UAH")

# Example result
# {
#   "amount": 235.5,
#   "category": "Foods",
#   "description": "Grocery shopping at ATB",
#   "transcript": "Bought groceries at ATB for 235.50 UAH"
# }
```
### Analytics_agent

The `analytics_agent` is responsible for handling user queries related to expense analysis. It leverages the LangChain SQL tool to interact with the database and provide insights based on the stored expense data. This allows users to ask questions like "How much did I spend on food last month?" or "Show my expenses by category for this week."

### Message processor:

1. Receiving text or voice message from the user
2. Transcribing voice message to text if it is voice message
3. Sending a request to intent_classifier with a clear prompt for classification
4. Processing the response and determining the intent: "expense", "analytics", or "unknown"
5. Logging classification results
6. If the intent is "expense", the parser sends a request to expenses_agent with a clear prompt for expense parsing
7. If the intent is "analytics", the parser sends a request to analytics_agent with a clear prompt for analitics or limits used retrieval

## Testing

The project contains unit tests to validate functionality:

```bash
# Run tests
python -m unittest discover tests
```

## Future plans

1. Add tracking expenses from mobile app
2. Add tracking expenses from banking apps
3. Add posibility of integration with other personal finance apps
4. Add possibility to switch between different currencies
5. Add posiibility to change expense categories, limits, build more advanced analytical reports
6. Switch between different LLMs
7. Add multilanguage support
8. Improve security and extend support for many users
9. Add metrics tracking
