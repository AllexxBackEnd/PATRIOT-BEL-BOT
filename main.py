import asyncio
import os
from openai import OpenAI
import logging
import requests
import sqlite3
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ContentType
from configurations.keyboards import get_admin_keyboard
from storage import admin_IDs
import storage
from admin_panel.see_statistick import stat_button
from commands.main_menu_command import show_main_menu
from commands.start import process_start_command
from commands.unknown_message import unknown_message
from config import BOT_TOKEN, GROQ_KEY
from configurations.callbacks import (
    handle_hero_quiz_selection,
    handle_heroes_pagination,
    handle_main_menu,
    start_hero_quiz_mode,
)
from configurations.quiz_manager import HeroQuizStates
from logs.logging_setup import setup_logger
from user_panel.hero_quiz_handler import (
    cancel_hero_quiz,
    handle_hero_quiz_answer,
)
from user_panel.heroes import heroes_button
from user_panel.information import information_button
from user_panel.leaderboard import show_leaderboard
from user_panel.quiz_handler import (
    QuizStates,
    cancel_quiz,
    handle_quiz_answer,
    process_educational_info,
    process_first_name,
    process_last_name,
    quiz_button,
    start_competitive_mode,
    start_practice_mode,
)

# Настройка логирования
logger = setup_logger()

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==================== СОСТОЯНИЯ ДЛЯ ИИ ЧАТА ====================


class ChatState(StatesGroup):
    main_menu = State()
    chat_with_ai = State()


# ==================== РАБОТА С БАЗОЙ ДАННЫХ ИИ ====================


def init_database():
    """Инициализация базы данных и создание таблицы, если её нет"""
    try:
        conn = sqlite3.connect("knowledge_base.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                fact_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")


def get_all_knowledge():
    """Получение всей базы знаний из SQLite"""
    try:
        conn = sqlite3.connect("knowledge_base.db")
        cursor = conn.cursor()

        cursor.execute("SELECT topic, fact_text FROM historical_facts")
        results = cursor.fetchall()

        conn.close()

        # Формируем текстовую базу знаний в нужном формате
        knowledge_text = ""
        for topic, fact_text in results:
            knowledge_text += f"{topic} — {fact_text}\n\n"

        logger.info(f"Загружено {len(results)} записей из базы данных")
        return knowledge_text.strip()

    except Exception as e:
        logger.error(f"Ошибка получения данных из базы: {e}")
        return ""


# ==================== ФУНКЦИИ РАБОТЫ С GROQ API ====================


def ask_groq(question):
    """Groq API через SDK OpenAI с данными из SQLite базы"""

    try:
        client = OpenAI(api_key=GROQ_KEY, base_url="https://api.groq.com/openai/v1")

        # Получаем актуальные данные из базы
        knowledge_base = get_all_knowledge()

        prompt = f"""
Ты — исторический ИИ ассистент, часть Telegram-Bot "PATRIOT BOT". Отвечая на вопросы, используй только приведённую базу знаний.

База знаний:
{knowledge_base}

Вопрос: {question}

Если пользователь спрашивает информацию, относящуюся к истории, но информации нет в базе знаний, скажи "Простите, я не могу ответить на ваш вопрос. Пожалуйста, попробуйте переформулировать ваш вопрос и поробовать ещё раз!".
Если вопрос не относится к истории, скажи "Прошу прощения, но я могу отвечать только на вопросы, связанные с героями ВОВ, в честь которых названы улицы г. Гродно. Хотите, раскажу вам о (Случайное имя из базы данных о героях)?".
Не бойся выполнять дополнительные вычисления и/или действия, если это необходимо для ответа на вопрос.
Отвечай кратко и емко:"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Ошибка Groq API: {e}")
        return f"Ошибка при обращении к API: {e}"


# ==================== КЛАВИАТУРЫ ДЛЯ ИИ ЧАТА ====================


def get_ai_conversation_keyboard():
    """Клавиатура во время чата с ИИ"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Вернуться в главное меню")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard


# ==================== РЕГИСТРАЦИЯ CALLBACK ОБРАБОТЧИКОВ ====================


def register_callbacks():
    """Регистрация всех callback обработчиков."""
    # Кнопка главного меню
    dp.callback_query.register(
        handle_main_menu,
        lambda callback: callback.data == "main_menu",
    )

    # Пагинация списка героев
    dp.callback_query.register(
        handle_heroes_pagination,
        lambda callback: callback.data.startswith("heroes_page_"),
    )

    # Выбор викторины по героям
    dp.callback_query.register(
        handle_hero_quiz_selection, HeroQuizStates.choosing_hero_quiz
    )


# ==================== ОБРАБОТЧИКИ КОМАНД ====================


@dp.message(Command("main_menu"))
async def command_main_menu(message: types.Message, state: FSMContext):
    """Обработчик команды main_menu"""
    await state.set_state(ChatState.main_menu)
    await show_main_menu(message)


@dp.message(Command("start"))
async def command_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start."""
    await state.set_state(ChatState.main_menu)
    await process_start_command(message)


@dp.message(Command("help"))
async def command_help(message: types.Message):
    """Обработчик команды /help."""
    help_text = (
        "🤖 *Помощь по боту:*\n\n"
        "🤖 *Поговорить с ИИ* - задайте вопрос историческому ассистенту о героях ВОВ\n\n"
        "🎯 *Викторина* - проверьте свои знания в двух режимах:\n"
        "   • 🏆 Соревновательный (10 вопросов, одна попытка)\n"
        "   • 🎯 Пробный (5 вопросов, много попыток)\n"
        "   • 🎖️ Викторины по героям - тесты по конкретным героям\n\n"
        "👤 *Узнать о героях* - информация о героях "
        "Великой Отечественной войны\n\n"
        "📊 *Таблица лидеров* - лучшие результаты в соревновательном режиме\n\n"
        "⚙️ *Информация о проекте* - общая информация о боте\n\n"
        "🔄 *Назад* - вернуться в главное меню\n\n"
        "📞 *Поддержка:* Если возникли проблемы, обратитесь к администратору."
    )
    await message.answer(help_text, parse_mode="Markdown")


# ==================== ОБРАБОТЧИКИ ИИ ЧАТА ====================


@dp.message(F.text == "🤖 Поговорить с ИИ", StateFilter(ChatState.main_menu))
async def start_ai_chat(message: types.Message, state: FSMContext):
    """Начало общения с ИИ"""
    await state.set_state(ChatState.chat_with_ai)
    chat_text = """
💬 *Режим общения с ИИ активирован!*

Теперь вы можете задавать вопросы о героях Великой Отечественной войны.

*Примеры вопросов:*
• Кто такой Агадил Сухомбаев?
• Что вы знаете об Алексее Антонове?
• Расскажи о подвиге Михаила Белуша
• Какие награды были у Ивана Болдина?

*ИИ использует базу знаний о героях ВОВ и отвечает только на основе проверенной информации.*

Для возврата в главное меню нажмите кнопку ниже.
"""
    await message.answer(
        chat_text, parse_mode="Markdown", reply_markup=get_ai_conversation_keyboard()
    )


@dp.message(
    F.text == "🔙 Вернуться в главное меню", StateFilter(ChatState.chat_with_ai)
)
async def back_from_ai_chat(message: types.Message, state: FSMContext):
    """Возврат из ИИ чата в главное меню"""
    await state.set_state(ChatState.main_menu)
    await show_main_menu(message)


@dp.message(StateFilter(ChatState.chat_with_ai))
async def handle_ai_questions(message: types.Message, state: FSMContext):
    """Обработчик вопросов к ИИ"""
    user_question = message.text.strip()

    # Игнорируем системные кнопки
    if user_question in ["🔙 Вернуться в главное меню", "🤖 Поговорить с ИИ"]:
        return

    # Показываем, что бот печатает
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Получаем ответ от ИИ
    answer = ask_groq(user_question)

    # Отправляем ответ пользователю
    await message.answer(
        f"🤖 *Ответ:*\n{answer}",
        parse_mode="Markdown",
        reply_markup=get_ai_conversation_keyboard(),
    )


# ==================== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ====================


@dp.message(F.text == "⏹️ Назад в меню", StateFilter(ChatState.main_menu))
async def back_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки Назад - возврат в главное меню."""
    await state.set_state(ChatState.main_menu)
    await show_main_menu(message)


@dp.message(F.text == "👸 Таблица лидеров", StateFilter(ChatState.main_menu))
async def leaderboard_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки Таблица лидеров."""
    await state.set_state(ChatState.main_menu)
    await show_leaderboard(message)


@dp.message(F.text == "💪 Узнать о героях", StateFilter(ChatState.main_menu))
async def heroes_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки Узнать о героях."""
    await state.set_state(ChatState.main_menu)
    await heroes_button(message)


@dp.message(F.text == "⚙️ Информация о проекте", StateFilter(ChatState.main_menu))
async def information_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки Информация о проекте."""
    await state.set_state(ChatState.main_menu)
    await information_button(message)


@dp.message(F.text == "⚙️ Просмотреть статистику", StateFilter(ChatState.main_menu))
async def stat_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки Просмотреть статистику."""
    if message.from_user.id not in admin_IDs:
        await message.answer("У вас нет доступа к этой команде.")
        return

    await state.set_state(ChatState.main_menu)
    await stat_button(message)


@dp.message(F.text == "🎯 Викторина", StateFilter(ChatState.main_menu))
async def quiz_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки Викторина - переход к выбору режима."""
    await state.set_state(ChatState.main_menu)
    await quiz_button(message, state)


# ==================== ОБРАБОТЧИКИ ВИКТОРИНЫ ====================

# Регистрация обработчиков викторины по героям
dp.message.register(
    start_hero_quiz_mode,
    lambda message: message.text == "🎖️ Викторины по героям",
    QuizStates.choosing_mode,
)

dp.message.register(handle_hero_quiz_answer, HeroQuizStates.in_hero_quiz)

dp.message.register(
    cancel_hero_quiz,
    lambda message: message.text == "⏹️ Назад в меню",
    HeroQuizStates.in_hero_quiz,
)


@dp.message(
    lambda message: message.text == "🎯 Пробный режим", QuizStates.choosing_mode
)
async def practice_mode_handler(message: types.Message, state: FSMContext):
    """Обработчик выбора пробного режима викторины."""
    await start_practice_mode(message, state)


@dp.message(
    lambda message: message.text == "🏆 Соревновательный режим",
    QuizStates.choosing_mode,
)
async def competitive_mode_handler(message: types.Message, state: FSMContext):
    """Обработчик выбора соревновательного режима викторины."""
    await start_competitive_mode(message, state)


@dp.message(lambda message: message.text == "⏹️ Назад в меню", QuizStates.choosing_mode)
async def back_to_menu_handler(message: types.Message, state: FSMContext):
    """Обработчик возврата в меню из выбора режима викторины."""
    await state.set_state(ChatState.main_menu)
    await show_main_menu(message)


# ==================== ОБРАБОТЧИКИ СБОРА ДАННЫХ ====================


@dp.message(QuizStates.waiting_for_first_name)
async def first_name_handler(message: types.Message, state: FSMContext):
    """Обработчик ввода имени для соревновательного режима."""
    await process_first_name(message, state)


@dp.message(QuizStates.waiting_for_last_name)
async def last_name_handler(message: types.Message, state: FSMContext):
    """Обработчик ввода фамилии для соревновательного режима."""
    await process_last_name(message, state)


@dp.message(QuizStates.waiting_for_educational_info)
async def educational_info_handler(message: types.Message, state: FSMContext):
    """Обработчик ввода учебного заведения для соревновательного режима."""
    await process_educational_info(message, state)


# ==================== ОБРАБОТЧИКИ ОТВЕТОВ В ВИКТОРИНЕ ====================


@dp.message(QuizStates.in_practice_quiz)
async def practice_quiz_handler(message: types.Message, state: FSMContext):
    """Обработчик ответов в пробном режиме викторины."""
    await handle_quiz_answer(message, state)


@dp.message(QuizStates.in_competitive_quiz)
async def competitive_quiz_handler(message: types.Message, state: FSMContext):
    """Обработчик ответов в соревновательном режиме викторины."""
    await handle_quiz_answer(message, state)


class BroadcastState(StatesGroup):
    waiting_for_broadcast_text = State()
    waiting_for_broadcast_photo = State()


# Обработчик кнопки "Начать рассылку"
@dp.message(F.text == "Начать рассылку", StateFilter(ChatState.main_menu))
async def start_broadcast(message: Message, state: FSMContext):
    """Начало процесса рассылки - только для админов"""
    if message.from_user.id not in admin_IDs:
        await message.answer("У вас нет доступа к этой команде.")
        return

    await state.set_state(BroadcastState.waiting_for_broadcast_text)
    await message.answer(
        "Введите текст для рассылки:", reply_markup=types.ReplyKeyboardRemove()
    )


# Обработчик текста рассылки
@dp.message(BroadcastState.waiting_for_broadcast_text)
async def process_broadcast_text(message: Message, state: FSMContext, bot: Bot):
    """Обработка текста рассылки и запрос фото"""
    await state.update_data(broadcast_text=message.text)
    await state.set_state(BroadcastState.waiting_for_broadcast_photo)

    await message.answer(
        "Текст сохранён. Теперь отправьте фото для рассылки "
        "(или отправьте 'пропустить' для рассылки без фото):",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="пропустить")]], resize_keyboard=True
        ),
    )


# Обработчик фото или пропуска
@dp.message(BroadcastState.waiting_for_broadcast_photo)
async def process_broadcast_photo(message: Message, state: FSMContext, bot: Bot):
    """Обработка фото и запуск рассылки"""
    data = await state.get_data()
    broadcast_text = data.get("broadcast_text", "")

    # Проверяем, отправил ли пользователь фото или решил пропустить
    if message.content_type == ContentType.PHOTO:
        photo_file_id = message.photo[-1].file_id
        await state.update_data(broadcast_photo=photo_file_id)
        await send_broadcast_to_users(bot, broadcast_text, photo_file_id)
    elif message.text and message.text.lower() == "пропустить":
        await send_broadcast_to_users(bot, broadcast_text)
    else:
        await message.answer("Пожалуйста, отправьте фото или нажмите 'пропустить'")
        return

    await state.clear()
    await state.set_state(ChatState.main_menu)
    await message.answer(
        "Рассылка завершена!",
        reply_markup=get_admin_keyboard,  # Ваша клавиатура главного меню
    )


async def send_broadcast_to_users(bot: Bot, text: str, photo_file_id: str = None):
    """
    Функция рассылки сообщений всем пользователям из storage.user_chat_ids
    """
    # Предполагаем, что у вас есть доступ к storage
    user_chat_ids = storage.user_chat_ids  # Это set или list с chat_id пользователей

    success_count = 0
    error_count = 0
    errors = []

    for chat_id in user_chat_ids:
        try:
            if photo_file_id:
                # Отправляем сообщение с фото
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file_id,
                    caption=text,
                    parse_mode="HTML",
                )
            else:
                # Отправляем текстовое сообщение
                await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            success_count += 1

            # Небольшая задержка чтобы не превысить лимиты Telegram
            await asyncio.sleep(0.1)

        except Exception as e:
            error_count += 1
            errors.append((chat_id, str(e)))

    # Отправляем отчет админу
    report_message = (
        f"📊 Отчет о рассылке:\n"
        f"✅ Успешно: {success_count}\n"
        f"❌ Ошибок: {error_count}\n"
        f"📝 Текст: {text[:100]}..."
    )

    # Отправляем отчет всем админам
    for admin_id in admin_IDs:
        try:
            await bot.send_message(admin_id, report_message)
            if errors:
                errors_text = "\n".join(
                    [f"{chat_id}: {error}" for chat_id, error in errors[:10]]
                )
                await bot.send_message(admin_id, f"Последние ошибки:\n{errors_text}")
        except Exception as e:
            print(f"Не удалось отправить отчет админу {admin_id}: {e}")


# ==================== ОБРАБОТЧИКИ ОТМЕНЫ ВИКТОРИНЫ ====================


@dp.message(
    lambda message: message.text == "⏹️ Завершить викторину", QuizStates.in_practice_quiz
)
async def cancel_practice_quiz_handler(message: types.Message, state: FSMContext):
    """Обработчик отмены пробной викторины."""
    await cancel_quiz(message, state)


@dp.message(
    lambda message: message.text == "⏹️ Завершить викторину",
    QuizStates.in_competitive_quiz,
)
async def cancel_competitive_quiz_handler(message: types.Message, state: FSMContext):
    """Обработчик отмены соревновательной викторины."""
    await cancel_quiz(message, state)


# ==================== ОБРАБОТЧИК НЕИЗВЕСТНЫХ СООБЩЕНИЙ ====================


@dp.message()
async def unknown_message_handler(message: types.Message, state: FSMContext):
    """Обработчик неизвестных сообщений."""
    current_state = await state.get_state()

    # Если пользователь в главном меню и пишет текст, предлагаем использовать кнопки
    if current_state == ChatState.main_menu:
        await message.answer(
            "🤖 Для взаимодействия с ботом используйте кнопки меню ниже.\n\n"
            "Если хотите задать вопрос ИИ, нажмите кнопку '🤖 Поговорить с ИИ'",
            reply_markup=get_ai_chat_keyboard(),
        )
    else:
        await unknown_message(message)


# ==================== ФУНКЦИИ ЗАПУСКА И ОСТАНОВКИ ====================


async def main():
    """
    Основная функция запуска бота.
    Регистрирует обработчики событий и запускает поллинг.
    """
    try:
        # Регистрация callback обработчиков
        register_callbacks()
        # Запуск бота с разрешенными типами обновлений
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        # Закрытие сессии бота при завершении
        await bot.session.close()


def check_required_files():
    """
    Проверяет наличие всех необходимых файлов перед запуском бота.

    Returns:
        bool: True если все файлы присутствуют, False в противном случае
    """
    required_files = [
        "config.py",
        "storage.py",
        "commands/start.py",
        "commands/unknown_message.py",
        "logs/logging_setup.py",
        "user_panel/heroes.py",
        "user_panel/information.py",
        "user_panel/leaderboard.py",
        "user_panel/quiz_handler.py",
        "user_panel/hero_quiz_handler.py",
    ]

    missing_files = []

    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        logger.error("❌ Отсутствуют необходимые файлы:")
        for file in missing_files:
            logger.error(f"   - {file}")
        return False

    return True


if __name__ == "__main__":
    # Проверка файлов перед запуском
    if not check_required_files():
        exit(1)

    logger.info("Запуск бота...")

    # Запуск асинхронной функции main
    asyncio.run(main())
