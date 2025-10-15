"""
Модуль обработки викторины для бота.
Управляет состояниями викторины, обработкой ответов и
взаимодействием с Google Sheets.
"""

import asyncio
import logging
from aiogram import types
from aiogram.fsm.context import FSMContext

from configurations.quiz_manager import QuizManager, QuizStates
import storage as storage
from data.google_sheets import sheets_manager
from configurations.keyboards import (
    get_main_keyboard,
    get_quiz_mode_keyboard,
    get_cancel_keyboard,
    get_quiz_question_keyboard,
)


logger = logging.getLogger("bot_logger")


quiz_manager = QuizManager(storage.quiz_questions)
quiz_data = {}


def calculate_grade(score, total_questions):
    """Определяет оценку на основе процента правильных ответов."""
    percentage = (score / total_questions) * 100

    if percentage >= 90:
        return "🎉 Отлично!", "🏆"
    elif percentage >= 75:
        return "👍 Очень хорошо!", "⭐"
    elif percentage >= 60:
        return "🙂 Хорошо!", "✅"
    elif percentage >= 40:
        return "😐 Удовлетворительно", "📘"
    else:
        return "💪 Попробуйте еще раз!", "📚"


async def quiz_button(message: types.Message, state: FSMContext):
    """Обработчик кнопки викторины - показывает выбор режима."""
    await state.set_state(QuizStates.choosing_mode)
    user_id = message.from_user.id

    can_play_competitive = not sheets_manager.is_competitive_completed(user_id)

    if not can_play_competitive:
        message_text = (
            "🎯 Выберите режим викторины:\n\n"
            "🏆 Соревновательный режим - ❌ ПРОЙДЕН\n"
            "• 10 вопросов\n"
            "• Можно пройти только один раз\n"
            "• Результат сохраняется\n\n"
            "🎖️ Викторины по героям\n"
            "• Тесты по конкретным героям\n"
            "• Для углубленного изучения\n\n"
            "🎯 Пробный режим\n"
            "• 5 случайных вопросов\n"
            "• Можно проходить много раз\n"
            "• Для тренировки"
        )
    else:
        message_text = (
            "🎯 Выберите режим викторины:\n\n"
            "🏆 Соревновательный режим\n"
            "• 10 вопросов\n"
            "• Можно пройти только один раз\n"
            "• Результат сохраняется\n\n"
            "🎖️ Викторины по героям\n"
            "• Тесты по конкретным героям\n"
            "• Для углубленного изучения\n\n"
            "🎯 Пробный режим\n"
            "• 5 случайных вопросов\n"
            "• Можно проходить много раз\n"
            "• Для тренировки"
        )

    await message.answer(
        message_text, reply_markup=get_quiz_mode_keyboard(can_play_competitive)
    )


async def start_practice_mode(message: types.Message, state: FSMContext):
    """Запускает пробный режим викторины."""
    await state.set_state(QuizStates.in_practice_quiz)
    user_id = message.from_user.id

    random_questions = quiz_manager.get_random_questions(5)

    quiz_data[user_id] = {
        "current_question": 0,
        "score": 0,
        "total_questions": 5,
        "questions": random_questions,
        "mode": "practice",
    }

    await message.answer(
        "🎯 *Начался пробный режим!*\n"
        "• 5 случайных вопросов\n"
        "• Можно проходить много раз\n"
        "• Удачи! 🍀",
        parse_mode="Markdown",
    )

    await asyncio.sleep(1.5)
    await send_question(message, user_id)


async def start_competitive_mode(message: types.Message, state: FSMContext):
    """Запускает соревновательный режим викторины."""
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} запустил соревновательный режим.")

    if sheets_manager.is_competitive_completed(user_id):
        await message.answer(
            "❌ Вы уже прошли соревновательный режим!\n"
            "Этот режим можно пройти только один раз.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        return

    quiz_data[user_id] = {
        "current_question": 0,
        "score": 0,
        "total_questions": 10,
        "questions": [],
        "mode": "competitive",
    }

    await state.set_state(QuizStates.waiting_for_first_name)

    await message.answer(
        "🏆 *Для участия в соревновательном режиме"
        " нам нужна дополнительная информация:*\n\n"
        "👤 Пожалуйста, введите ваше *имя*:\n",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown",
    )


async def process_first_name(message: types.Message, state: FSMContext):
    """Обрабатывает ввод имени пользователя."""
    user_id = message.from_user.id

    if user_id not in quiz_data:
        await message.answer(
            "❌ Произошла ошибка. Начните викторину заново.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        return

    if message.text == "⏹️ Отмена":
        await cancel_quiz(message, state)
        return

    first_name = message.text.strip()

    quiz_data[user_id]["first_name"] = first_name

    await state.set_state(QuizStates.waiting_for_last_name)

    await message.answer(
        "✅ *Имя принято!*\n\n"
        "👤 Теперь введите вашу *фамилию*:\n",
        parse_mode="Markdown",
    )


async def process_last_name(message: types.Message, state: FSMContext):
    """Обрабатывает ввод фамилии пользователя."""
    user_id = message.from_user.id

    if user_id not in quiz_data:
        await message.answer(
            "❌ Произошла ошибка. Начните викторину заново.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        return

    if message.text == "⏹️ Отмена":
        await cancel_quiz(message, state)
        return

    last_name = message.text.strip()

    quiz_data[user_id]["last_name"] = last_name
    await state.set_state(QuizStates.waiting_for_educational_info)

    await message.answer(
        "✅ *Фамилия принята!*\n\n"
        "🎓 Теперь введите ваше *учебное заведение*:\n"
        "_(например: 'МГУ', 'Школа №123', 'Колледж информатики')_",
        parse_mode="Markdown",
    )


async def process_educational_info(message: types.Message, state: FSMContext):
    """Обрабатывает ввод информации об учебном заведении."""
    user_id = message.from_user.id

    if user_id not in quiz_data:
        await message.answer(
            "❌ Произошла ошибка. Начните викторину заново.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        return

    if message.text == "⏹️ Отмена":
        await cancel_quiz(message, state)
        return

    educational_institution = message.text.strip()

    quiz_data[user_id]["educational_institution"] = educational_institution
    quiz_data[user_id]["questions"] = quiz_manager.get_random_questions(10)

    await state.set_state(QuizStates.in_competitive_quiz)

    await message.answer(
        "✅ *Вся информация сохранена!*\n\n"
        "🏆 *Начался соревновательный режим!*\n"
        "• 10 вопросов\n"
        "• Только одна попытка\n"
        "• Результат будет сохранен.\n"
        "• Удачи! 🍀",
        parse_mode="Markdown",
    )
    await asyncio.sleep(2)
    await send_question(message, user_id)


async def send_question(message: types.Message, user_id: int):
    """Отправляет вопрос пользователю."""
    current_question_idx = quiz_data[user_id]["current_question"]
    questions_list = quiz_data[user_id]["questions"]
    mode = quiz_data[user_id]["mode"]

    if current_question_idx >= len(questions_list):
        await finish_quiz(message, user_id)
        return

    question_data = quiz_manager.get_question(questions_list,
                                              current_question_idx)

    # Проверка на None
    if question_data is None:
        await message.answer(
            "❌ Произошла ошибка при получении вопроса. Викторина завершена.",
            reply_markup=get_main_keyboard(),
        )
        if user_id in quiz_data:
            del quiz_data[user_id]
        return

    keyboard = get_quiz_question_keyboard(question_data["options"])

    total_questions = 10 if mode == "competitive" else 5

    await message.answer(
        f"❓ *Вопрос {current_question_idx + 1}/{total_questions}*\n\n"
        f"{question_data['question']}",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def handle_quiz_answer(message: types.Message, state: FSMContext):
    """Обработчик ответов на вопросы викторины."""
    user_id = message.from_user.id

    if user_id not in quiz_data:
        await message.answer(
            "❌ Викторина не активна. Начните заново.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        return

    if message.text == "⏹️ Завершить викторину":
        await cancel_quiz(message, state)
        return

    current_question_idx = quiz_data[user_id]["current_question"]
    questions_list = quiz_data[user_id]["questions"]

    question_data = quiz_manager.get_question(questions_list,
                                              current_question_idx)

    if message.text not in question_data["options"]:
        await message.answer(
            "❌ Пожалуйста, выберите один из предложенных вариантов ответа."
        )
        return

    is_correct = quiz_manager.check_answer(question_data, message.text)
    if is_correct:
        quiz_data[user_id]["score"] += 1

    quiz_data[user_id]["current_question"] += 1
    await send_question(message, user_id)


async def cancel_quiz(message: types.Message, state: FSMContext):
    """Завершает викторину досрочно."""
    user_id = message.from_user.id

    if user_id in quiz_data:
        score = quiz_data[user_id]["score"]
        current = quiz_data[user_id]["current_question"]
        mode = quiz_data[user_id]["mode"]

        if mode == "competitive":
            user_data = quiz_data[user_id]
            success = sheets_manager.save_competitive_result(
                {
                    "chat_id": user_id,
                    "first_name": user_data.get("first_name", ""),
                    "last_name": user_data.get("last_name", ""),
                    "educational_institution": user_data.get(
                        "educational_institution", "Не указано"
                    ),
                    "correct_answers": score,
                    "total_questions": current,
                }
            )

            if success:
                await message.answer(
                    f"🏆 *Соревновательный режим завершен досрочно!*\n\n"
                    f"📊 *Ваш результат:*\n"
                    f"• Правильных ответов: {score}/{current}\n\n"
                    f"✅ *Результат сохранен в Google Таблицу!*\n"
                    f"Больше нельзя пройти этот режим.",
                    reply_markup=get_main_keyboard(),
                    parse_mode="Markdown",
                )
            else:
                await message.answer(
                    f"🏆 *Соревновательный режим завершен досрочно!*\n\n"
                    f"📊 *Ваш результат:*\n"
                    f"• Правильных ответов: {score}/{current}\n\n"
                    f"❌ *Ошибка сохранения результата*\n"
                    f"Обратитесь к администратору.",
                    reply_markup=get_main_keyboard(),
                    parse_mode="Markdown",
                )
        else:
            await message.answer(
                f"🎯 *Пробный режим завершен досрочно!*\n\n"
                f"📊 *Ваш результат:*\n"
                f"• Правильных ответов: {score}/{current}",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown",
            )

        del quiz_data[user_id]

    await state.clear()


async def finish_quiz(message: types.Message, user_id: int):
    """Завершает викторину и выводит результаты."""
    score = quiz_data[user_id]["score"]
    total = quiz_data[user_id]["total_questions"]
    mode = quiz_data[user_id]["mode"]

    percentage = (score / total) * 100
    grade, emoji = calculate_grade(score, total)

    if mode == "competitive":
        user_data = quiz_data[user_id]
        success = sheets_manager.save_competitive_result(
            {
                "chat_id": user_id,
                "first_name": user_data.get("first_name", ""),
                "last_name": user_data.get("last_name", ""),
                "educational_institution": user_data.get(
                    "educational_institution", "Не указано"
                ),
                "correct_answers": score,
                "total_questions": total,
            }
        )

        if success:
            result_text = (
                f"{emoji} *Соревновательный режим завершен!* {emoji}\n\n"
                f"📊 *Ваш результат:*\n"
                f"• Правильных ответов: {score}/{total}\n"
                f"• Процент: {percentage:.1f}%\n"
                f"• Оценка: {grade}\n"
                "• Учебное заведение:"
                f"{user_data.get('educational_institution', 'Не указано')}\n\n"
                f"✅ *Результат сохранен!*\n"
                f"Спасибо за участие! 🎯"
            )
        else:
            result_text = (
                f"{emoji} *Соревновательный режим завершен!* {emoji}\n\n"
                f"📊 *Ваш результат:*\n"
                f"• Правильных ответов: {score}/{total}\n"
                f"• Процент: {percentage:.1f}%\n"
                f"• Оценка: {grade}\n\n"
                f"❌ *Ошибка сохранения результата*\n"
                f"Обратитесь к администратору."
            )
    else:
        result_text = (
            f"{emoji} *Пробный режим завершен!* {emoji}\n\n"
            f"📊 *Ваш результат:*\n"
            f"• Правильных ответов: {score}/{total}\n"
            f"• Процент: {percentage:.1f}%\n"
            f"• Оценка: {grade}\n\n"
            f"🔄 Можете попробовать еще раз!"
        )

    await message.answer(
        result_text, reply_markup=get_main_keyboard(), parse_mode="Markdown"
    )

    if user_id in quiz_data:
        del quiz_data[user_id]


def get_competitive_stats():
    """Возвращает статистику по соревновательному режиму."""
    try:
        stats = sheets_manager.get_statistics()
        results = sheets_manager.get_all_results()

        return {
            "total_participants": stats["total_participants"],
            "average_score": stats["average_score"],
            "best_score": stats["best_score"],
            "total_records": len(results),
            "storage_type": "Google Sheets",
        }
    except Exception:
        return {
            "total_participants": 0,
            "average_score": 0,
            "best_score": 0,
            "total_records": 0,
            "storage_type": "Google Sheets (ошибка)",
        }


def cleanup_quiz_data():
    """Очищает данные викторины ."""
    expired_users = []

    for user_id, data in quiz_data.items():
        # Логика очистки старых данных
        pass

    for user_id in expired_users:
        del quiz_data[user_id]

    return len(expired_users)
