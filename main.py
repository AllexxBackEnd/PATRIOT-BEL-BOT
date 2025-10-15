"""
Главный модуль бота PATRIOT BOT.
Обрабатывает команды, кнопки меню и управляет состояниями викторины.
"""

import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# Импорт модулей проекта
from configurations.callbacks import (
    handle_hero_quiz_selection,
    handle_main_menu,
    handle_heroes_pagination,
    start_hero_quiz_mode
                                      )
from configurations.quiz_manager import HeroQuizStates
from config import BOT_TOKEN
from logs.logging_setup import setup_logger
from user_panel.heroes import heroes_button
from user_panel.information import information_button
from user_panel.leaderboard import show_leaderboard
from user_panel.quiz_handler import (
    quiz_button,
    handle_quiz_answer,
    cancel_quiz,
    start_practice_mode,
    start_competitive_mode,
    process_first_name,
    process_last_name,
    process_educational_info,
    QuizStates,
)
from user_panel.hero_quiz_handler import (
    handle_hero_quiz_answer,
    cancel_hero_quiz,
)
from commands.start import process_start_command
from commands.unknown_message import unknown_message
from commands.main_menu_command import show_main_menu


# Настройка логирования
logger = setup_logger()

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


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
async def command_main_menu(message):
    """Обработчик команды mein_menu"""
    await show_main_menu(message)


@dp.message(Command("start"))
async def command_start(message: types.Message):
    """Обработчик команды /start."""
    await process_start_command(message)


@dp.message(Command("help"))
async def command_help(message: types.Message):
    """Обработчик команды /help."""
    help_text = (
        "🤖 *Помощь по боту:*\n\n"
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


# ==================== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ====================


@dp.message(lambda message: message.text == "⏹️ Назад в меню")
async def back_handler(message: types.Message):
    """Обработчик кнопки Назад - возврат в главное меню."""
    await show_main_menu(message)


@dp.message(lambda message: message.text == "👸 Таблица лидеров")
async def leaderboard_handler(message: types.Message):
    """Обработчик кнопки Таблица лидеров."""
    await show_leaderboard(message)


@dp.message(lambda message: message.text == "💪 Узнать о героях")
async def heroes_handler(message: types.Message):
    """Обработчик кнопки Узнать о героях."""
    await heroes_button(message)


@dp.message(lambda message: message.text == "⚙️ Информация о проекте")
async def information_handler(message: types.Message):
    """Обработчик кнопки Информация о проекте."""
    await information_button(message)


@dp.message(lambda message: message.text == "🎯 Викторина")
async def quiz_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки Викторина - переход к выбору режима."""
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


@dp.message(lambda message: message.text == "⏹️ Назад в меню",
            QuizStates.choosing_mode)
async def back_to_menu_handler(message: types.Message, state: FSMContext):
    """Обработчик возврата в меню из выбора режима викторины."""
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


# ==================== ОБРАБОТЧИКИ ОТМЕНЫ ВИКТОРИНЫ ====================

@dp.message(
    lambda message: message.text == "⏹️ Завершить викторину",
    QuizStates.in_practice_quiz
)
async def cancel_practice_quiz_handler(message: types.Message,
                                       state: FSMContext):
    """Обработчик отмены пробной викторины."""
    await cancel_quiz(message, state)


@dp.message(
    lambda message: message.text == "⏹️ Завершить викторину",
    QuizStates.in_competitive_quiz,
)
async def cancel_competitive_quiz_handler(message: types.Message,
                                          state: FSMContext):
    """Обработчик отмены соревновательной викторины."""
    await cancel_quiz(message, state)


# ==================== ОБРАБОТЧИК НЕИЗВЕСТНЫХ СООБЩЕНИЙ ====================


@dp.message()
async def unknown_message_handler(message: types.Message):
    """Обработчик неизвестных сообщений."""
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
        await dp.start_polling(bot,
                               allowed_updates=dp.resolve_used_update_types())

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
