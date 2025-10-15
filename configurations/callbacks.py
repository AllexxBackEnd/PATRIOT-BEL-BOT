import asyncio
import logging

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

import storage
from configurations.keyboards import create_heroes_keyboard, get_main_keyboard
from configurations.quiz_manager import HeroQuizManager, HeroQuizStates
from user_panel.hero_quiz_handler import (create_heroes_quiz_keyboard,
                                          send_hero_question)


logger = logging.getLogger("bot_logger")


async def handle_main_menu(callback_query: types.CallbackQuery):
    """Обработчик возврата в главное меню"""
    # Сначала отправляем новое сообщение с главным меню
    await callback_query.message.answer_photo(
        photo="https://i.postimg.cc/Z5Gm3JZT/IMG-1540.jpg",
        caption=" Добро пожаловать в PATRIOT BOT!\n\n"
        "📚 В этом боте ты узнаешь:\n"
        "   • О героях, в честь кого названы улицы города Гродно\n"
        "   • Историю родного края\n\n"
        "🎯 А также сможешь:\n"
        "   • Пройти обучающую викторину\n"
        "   • Проверить свои знания\n"
        "   • Закрепить изученное\n\n"
        "🚀 Начнём наше путешествие в историю!\n\n"
        "👇 Выбери раздел:",
        reply_markup=get_main_keyboard(),
        )


async def handle_heroes_pagination(callback: types.CallbackQuery,
                                   state: FSMContext):
    """Обработчик пагинации героев"""
    if not callback.data.startswith("heroes_page_"):
        await callback.answer()
        return

    try:
        page = int(callback.data.split("_")[2])
        total_heroes = len(storage.HERO_URLS) if hasattr(storage,
                                                         "HERO_URLS") else 0

        if total_heroes == 0:
            await callback.answer("❌ Список героев не настроен",
                                  show_alert=True)
            return

        heroes_per_page = 5
        start_hero = page * heroes_per_page + 1
        end_hero = min((page + 1) * heroes_per_page, total_heroes)

        # Получаем имена героев для отображения в заголовке
        hero_names = []
        for hero_id in range(start_hero, end_hero + 1):
            hero_name = storage.HERO_NAMES.get(hero_id, f"Герой {hero_id}")
            hero_names.append(hero_name)

        # Обновляем сообщение с новой страницей
        await callback.message.edit_text(
            f"🎖️ *Герои Великой Отечественной войны*\n\n"
            f"📚 Доступно {total_heroes} героев\n"
            f"📖 Страница {page + 1}\n\n"
            f"Выберите героя для просмотра информации:",
            reply_markup=create_heroes_keyboard(page),
            parse_mode="Markdown",
        )
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Ошибка при переключении страницы {e}",
                              show_alert=True)


async def start_hero_quiz_mode(message: types.Message, state: FSMContext):
    """Запуск режима выбора викторины по героям"""
    await state.set_state(HeroQuizStates.choosing_hero_quiz)

    await message.answer(
        "🎖️ *Викторины по героям*\n\n"
        "Выберите героя для прохождения тренировочной викторины:\n"
        "• 5 случайных вопросов\n"
        "• Только тренировочный режим\n"
        "• Можно проходить много раз\n\n",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown",
    )

    # Затем отправляем сообщение с клавиатурой выбора героев
    await message.answer(
        f"📖 *Всего героев: {len(storage.HERO_NAMES)}*\n"
        "📄 Используйте кнопки для навигации",
        reply_markup=create_heroes_quiz_keyboard(0),
        parse_mode="Markdown",
    )


async def handle_hero_quiz_selection(callback: types.CallbackQuery,
                                     state: FSMContext):
    """Обработчик выбора героя для викторины и пагинации"""
    if callback.data == "hero_quiz_back":
        await state.clear()
        await callback.message.answer_photo(
            photo="https://i.postimg.cc/Z5Gm3JZT/IMG-1540.jpg",
            caption=" Добро пожаловать в PATRIOT BOT!\n\n"
            "📚 В этом боте ты узнаешь:\n"
            "   • О героях, в честь кого названы улицы города Гродно\n"
            "   • Историю родного края\n\n"
            "🎯 А также сможешь:\n"
            "   • Пройти обучающую викторину\n"
            "   • Проверить свои знания\n"
            "   • Закрепить изученное\n\n"
            "🚀 Начнём наше путешествие в историю!\n\n"
            "👇 Выбери раздел:",
            reply_markup=get_main_keyboard(),
            )
        await callback.answer()
        return

    # Обработка пагинации
    if callback.data.startswith("hero_quiz_page_"):
        try:
            page = int(callback.data.split("_")[3])
            await callback.message.edit_reply_markup(
                reply_markup=create_heroes_quiz_keyboard(page)
            )
            await callback.answer()
            return
        except (ValueError, IndexError):
            await callback.answer("❌ Ошибка пагинации", show_alert=True)
            return

    # Обработка выбора героя
    if callback.data.startswith("hero_quiz_"):
        try:
            # Проверяем, что это не пагинация
            if "page" in callback.data:
                return

            hero_id = int(callback.data.split("_")[2])

            if hero_id < 1 or hero_id > 35:
                await callback.answer("❌ Герой не найден", show_alert=True)
                return

            hero_name = storage.HERO_NAMES.get(hero_id, f"Герой {hero_id}")

            # Начинаем викторину
            await state.set_state(HeroQuizStates.in_hero_quiz)
            user_id = callback.from_user.id

            # Создаем экземпляр менеджера викторин
            quiz_manager = HeroQuizManager()

            # Получаем вопросы для героя
            questions = quiz_manager.get_hero_questions(hero_id)

            if not questions:
                await callback.answer(
                    "❌ Вопросы для этого героя не найдены", show_alert=True
                )
                return

            # Сохраняем данные викторины
            quiz_manager.quiz_data[user_id] = {
                "current_question": 0,
                "score": 0,
                "total_questions": len(questions),
                "questions": questions,
                "hero_id": hero_id,
                "hero_name": hero_name,
            }

            await callback.message.edit_text(
                f"🎖️ *Викторина: {hero_name}*\n\n"
                f"Начинается тренировочная викторина!\n"
                f"• {len(questions)} вопросов\n"
                f"• Только обучение\n"
                f"• Удачи! 🍀",
                parse_mode="Markdown",
            )

            await asyncio.sleep(2)
            await send_hero_question(callback.message, user_id)
            await callback.answer()

        except Exception as e:
            print(f"Ошибка запуска викторины: {e}")
            await callback.answer("❌ Ошибка запуска викторины",
                                  show_alert=True)

    # Обработка клика на номер страницы
    elif callback.data == "hero_quiz_current_page":
        await callback.answer("Текущая страница")
