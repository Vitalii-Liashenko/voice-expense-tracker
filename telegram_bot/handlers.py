"""
Обробники команд та повідомлень для Telegram бота.
"""
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from db.database import get_db_session
from db.queries import save_expense, check_budget_limit, get_remaining_budget, seed_test_data
from ai_agent.open_ai_intent_classifier import classify_intent
from ai_agent.open_ai_expense_parser import parse_expense, ExpenseParser
from ai_agent.open_ai_analytics_agent import generate_analytics
from whisper_transcriber import download_voice_message, transcribe_audio
from config import AUTHOR_USER_ID

AUTHOR_USER_ID = AUTHOR_USER_ID

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /start."""
    user_id = update.effective_user.id
    
    # Перевірка авторизації
    if user_id != AUTHOR_USER_ID:
        await update.message.reply_text(
            "Вибачте, але ви не маєте доступу до цього бота."
        )
        return
    
    # Ініціалізація бази даних з тестовими даними
    db = get_db_session()
    try:
        seed_test_data(db, user_id)
        await update.message.reply_text(
            "Привіт! Я - ваш AI-бухгалтер. Ви можете:\n"
            "- Відправляти голосові повідомлення про витрати\n"
            "- Запитувати аналітику витрат\n"
            "- Отримувати сповіщення про перевищення лімітів\n"
            "\n"
            "Спробуйте відправити голосове повідомлення з витратою, наприклад:\n"
            "'Купив продукти за 300 гривень'"
        )
    finally:
        db.close()

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /help."""
    await update.message.reply_text(
        "Доступні команди:\n"
        "/start - Почати роботу з ботом\n"
        "/help - Ця допомога\n\n"
        "Ви можете:\n"
        "- Відправляти голосові повідомлення про витрати\n"
        "- Запитувати аналітику витрат голосом або текстом\n"
        "- Отримувати сповіщення про перевищення лімітів"
    )

async def process_text_with_nlp(update: Update, text: str):
    """
    Обробляє текст через NLP пайплайн.
    
    1. Класифікація наміру
    2. Розпізнавання витрат або генерація аналітики
    3. Збереження витрат або відправка аналітики користувачу
    
    Args:
        update: Об'єкт повідомлення Telegram
        text: Текст для обробки
    """
    user_id = update.effective_user.id
    
    # 1. Класифікація наміру
    logger.info(f"Класифікуємо намір: '{text}'")
    intent = classify_intent(text)
    logger.info(f"Розпізнаний намір: {intent}")
    
    if intent == "expense":
        # 2. Парсинг витрати
        logger.info("Обробляємо як витрату")
        expense = parse_expense(text)
        
        if expense:
            # 3. Збереження витрати в базу даних
            logger.info(f"Розпізнана витрата: {expense}")
            db = get_db_session()
            try:
                # Отримуємо дані з парсингу
                amount = expense["amount"]
                category = expense["category"]
                description = expense["description"]
                
                # Перевіряємо перевищення ліміту
                is_over, remaining = check_budget_limit(db, user_id, category, amount)
                
                # Зберігаємо витрату
                saved_expense = save_expense(
                    db, 
                    user_id, 
                    category, 
                    amount, 
                    description,
                    text  # transcript - оригінальний текст
                )
                
                # Повідомляємо користувача
                message = f"✅ Збережено витрату: <b>{amount:.2f} грн</b> ({category})\n"
                message += f"📝 Опис: {description}\n"
                
                # Додаємо інформацію про ліміт
                if is_over:
                    message += f"\n⚠️ <b>Увага!</b> Ви перевищили ліміт у категорії <b>{category}</b>.\n"
                    message += f"Перевищення: <b>{abs(remaining):.2f} грн</b>"
                else:
                    message += f"\n💰 Залишок у категорії <b>{category}</b>: <b>{remaining:.2f} грн</b>"
                
                await update.message.reply_text(message, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Помилка при збереженні витрати: {e}")
                await update.message.reply_text(f"Сталася помилка при збереженні витрати: {str(e)}")
            finally:
                db.close()
        else:
            await update.message.reply_text(
                "Не вдалося розпізнати інформацію про витрату. "
                "Будь ласка, вкажіть суму та опис витрати ясніше."
            )
    elif intent == "analytics":
        # 2. Генерація аналітики
        logger.info("Обробляємо як запит на аналітику")
        try:
            analytics_response = generate_analytics(text)
            await update.message.reply_text(analytics_response, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Помилка при генерації аналітики: {e}")
            await update.message.reply_text(
                "Вибачте, сталася помилка при обробці запиту на аналітику. Спробуйте пізніше."
            )
    else:
        # Невідомий намір
        logger.info("Невідомий намір")
        await update.message.reply_text(
            "Вибачте, я не зрозумів ваше повідомлення. Ви можете:\n"
            "- Записати витрату (наприклад, 'Купив продукти за 300 грн')\n"
            "- Запитати аналітику (наприклад, 'Скільки я витратив на їжу цього місяця?')"
        )

async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник голосових повідомлень."""
    user_id = update.effective_user.id
    
    # Перевірка авторизації
    if user_id != AUTHOR_USER_ID:
        return
    
    # Отримання голосового повідомлення
    voice_file = await update.message.voice.get_file()
    
    # Повідомити користувача про початок обробки
    processing_message = await update.message.reply_text("🔄 Обробляю ваше голосове повідомлення...")
    
    try:
        # 1. Завантаження голосового повідомлення
        logger.info("Завантажуємо голосове повідомлення")
        audio_path = await download_voice_message(voice_file)
        
        # 2. Транскрипція голосу в текст
        logger.info("Транскрибуємо аудіо у текст")
        transcribed_text = await transcribe_audio(audio_path)
        
        # Показати користувачу розпізнаний текст
        await processing_message.edit_text(f"🔤 Розпізнаний текст: \"{transcribed_text}\"")
        
        # 3. Обробка тексту через NLP пайплайн
        await process_text_with_nlp(update, transcribed_text)
        
    except Exception as e:
        logger.error(f"Помилка при обробці голосового повідомлення: {e}")
        await update.message.reply_text(
            "Вибачте, сталася помилка при обробці голосового повідомлення. Спробуйте ще раз."
        )

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник текстових повідомлень."""
    user_id = update.effective_user.id
    
    # Перевірка авторизації
    if user_id != AUTHOR_USER_ID:
        return
    
    message = update.message.text
    
    # Обробка тексту через NLP пайплайн
    await process_text_with_nlp(update, message)
