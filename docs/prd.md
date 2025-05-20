# 📄 Product Requirements Document (PRD)

## 📌 Project Title  
**"Voice Expense Tracker" – AI-бухгалтер у Telegram (UA Edition)**

---

## 🧭 Purpose

Розробити AI-додаток у вигляді Telegram-бота, який дозволяє одному користувачу записувати свої особисті витрати голосом, класифікувати їх за категоріями, зберігати в базу даних, аналізувати витрати по категоріях та повідомляти про перевищення бюджетів.

---

## 👤 Target User

Один індивідуальний користувач, який:
- хоче голосом вносити витрати у зручному форматі;
- бажає бачити статистику витрат по категоріях;
- використовує українську мову у спілкуванні;
- не потребує планування витрат, але хоче бачити залишок по лімітах.

---

## 🧩 Product Features

### 🎙️ 1. Голосове введення
- Голосові повідомлення у Telegram обробляються та конвертуються в текст українською.
- Whisper API використовується для транскрипції.
- Текст зберігається у базу даних для подальшого аналізу.

### 🧠 2. AI-аналіз повідомлень
- LLM (Claude 3) аналізує текст:
  - Витрата — сума, категорія, опис, дата.
  - Запит на аналітику — генерація звіту.
  - Інше — чемна відмова з поясненням.

### 🗃️ 3. Збереження даних
- Зберігаються транзакції та ліміти користувача у PostgreSQL (через Docker). Основні таблиці: `expenses` (для витрат) та `limits` (для місячних бюджетів по категоріях).
- Поля `expenses`: user_id, category, amount, description, transcript, timestamp.

### 🧾 4. Категоризація витрат
- Категорії (англійською): `Foods`, `Shopping`, `Housing`, `Transportation`, `Entertainment`, `Others`.

### 📊 5. Аналітика
- Відповіді на запити типу:
  - "Скільки я витратив на транспорт цього місяця?"
  - "Чи перевищив я ліміт на розваги?"
- Повідомлення про:
  - Перевищення бюджету по категорії.
  - Залишок в рамках заданого ліміту.
- Аналітика базується на даних з таблиць `expenses` та `limits`.

### 🔁 6. Telegram-інтеграція
- Всі запити та відповіді проходять лише через Telegram.
- Користувач взаємодіє з ботом, який підтримує лише українську мову в комунікації.

---

## 🧠 AI/ML Components

| Завдання                  | Інструмент / Модель       |
|---------------------------|---------------------------|
| Голос → текст             | OpenAI Whisper API        |
| Інтерпретація наміру      | OpenAI                    |
| Класифікація витрат       | LangChain Agent           |
| Аналітика та відповіді    | LangChain + SQL Tool      |

---

## ⚙️ Технології

| Компонент             | Технологія                |
|------------------------|---------------------------|
| Telegram Integration   | `python-telegram-bot`     |
| AI інфраструктура      | LangChain                 |
| Голосове розпізнавання | Whisper API (via OpenAI)  |
| База даних             | PostgreSQL у Docker       |
| Backend                | Python                    |
| Хостинг                | Локальний запуск          |

---

## 🗃️ База даних

```sql
CREATE TABLE expenses (
  id SERIAL PRIMARY KEY,
  user_id BIGINT,                -- Telegram user ID
  category TEXT,                 -- Expense category (e.g., Foods, Shopping)
  amount NUMERIC,                -- Amount of the expense
  description TEXT,              -- User-provided description or parsed details
  transcript TEXT,               -- Original or processed voice transcript
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp of expense creation
);

CREATE TABLE limits (
  id SERIAL PRIMARY KEY,
  user_id BIGINT,                -- Telegram user ID, links to the user who set the limit
  category TEXT,                 -- Category for which the limit is set (matches expense categories)
  monthly_limit NUMERIC,         -- The monthly spending limit for this category
  UNIQUE (user_id, category)     -- Ensures one limit per category for each user
);
```

---
