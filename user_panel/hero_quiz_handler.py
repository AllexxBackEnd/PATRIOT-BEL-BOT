from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from configurations.quiz_manager import HeroQuizManager
import storage
from configurations.keyboards import get_main_keyboard


hero_quiz_manager = HeroQuizManager()


def create_heroes_quiz_keyboard(page: int = 0,):
    """Создание клавиатуры для выбора викторины по героям с пагинацией"""
    total_heroes = 35
    heroes_per_page = 5
    total_pages = (total_heroes + heroes_per_page - 1) // heroes_per_page

    # Защита от выхода за границы
    if page < 0:
        page = 0
    if page >= total_pages:
        page = total_pages - 1

    keyboard = []

    # Добавляем кнопки героев для текущей страницы
    start_hero = page * heroes_per_page + 1
    end_hero = min((page + 1) * heroes_per_page, total_heroes)

    for hero_id in range(start_hero, end_hero + 1):
        hero_name = storage.HERO_NAMES.get(hero_id, f"Герой {hero_id}")
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"🎯 {hero_name}", callback_data=f"hero_quiz_{hero_id}"
                )
            ]
        )

    # Добавляем кнопки навигации
    navigation_buttons = []

    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад", callback_data=f"hero_quiz_page_{page - 1}"
            )
        )

    # Показываем номер текущей страницы
    if total_pages > 1:
        navigation_buttons.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="hero_quiz_current_page"
            )
        )

    if page < total_pages - 1:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Далее ➡️", callback_data=f"hero_quiz_page_{page + 1}"
            )
        )

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    # Кнопка возврата
    keyboard.append(
        [InlineKeyboardButton(text="⏹️ Назад в меню",
                              callback_data="hero_quiz_back")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def send_hero_question(message: types.Message, user_id: int):
    """Отправка вопроса викторины по героям"""

    if user_id not in hero_quiz_manager.quiz_data:
        print(f"DEBUG: User {user_id} not in quiz_data")
        await message.answer("❌ Викторина не активна",
                             reply_markup=get_main_keyboard())
        return

    quiz_data = hero_quiz_manager.quiz_data[user_id]
    current_question_idx = quiz_data["current_question"]
    questions_list = quiz_data["questions"]

    if current_question_idx >= len(questions_list):
        await finish_hero_quiz(message, user_id)
        return

    question_data = hero_quiz_manager.get_question(questions_list,
                                                   current_question_idx)

    if not question_data:
        await finish_hero_quiz(message, user_id)
        return

    # Создаем 4 ряда с вариантами ответов
    options = question_data["options"]
    options_rows = []

    # Распределяем варианты по 4 рядам
    total_options = len(options)
    if total_options <= 4:
        # Если вариантов 4 или меньше - по одному в ряд
        for option in options:
            options_rows.append([KeyboardButton(text=option)])
    else:
        # Распределяем поровну по 4 рядам
        base_per_row = total_options // 4
        remainder = total_options % 4

        index = 0
        for row in range(4):
            # Определяем сколько кнопок будет в этом ряду
            row_items = base_per_row + (1 if row < remainder else 0)
            if index < total_options:
                row_buttons = [
                    KeyboardButton(
                        text=options[i]) for i in range(
                            index, index + row_items)]
                options_rows.append(row_buttons)
                index += row_items

    # Добавляем кнопку завершения в отдельный ряд
    options_rows.append([KeyboardButton(text="⏹️ Завершить викторину")])

    keyboard = ReplyKeyboardMarkup(
        keyboard=options_rows,
        resize_keyboard=True,
    )

    await message.answer(
        f"🎖️ *{quiz_data['hero_name']}*\n"
        "❓ "
        f"Вопрос {current_question_idx + 1}/{quiz_data['total_questions']}\n\n"
        f"{question_data['question']}",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def handle_hero_quiz_answer(message: types.Message, state: FSMContext):
    """Обработчик ответов в викторине по героям"""
    user_id = message.from_user.id

    if user_id not in hero_quiz_manager.quiz_data:
        await message.answer("❌ Викторина не активна")
        await state.clear()
        return

    if message.text == "⏹️ Завершить викторину":
        await cancel_hero_quiz(message, state)
        return

    quiz_data = hero_quiz_manager.quiz_data[user_id]
    current_question_idx = quiz_data["current_question"]
    questions_list = quiz_data["questions"]

    question_data = hero_quiz_manager.get_question(questions_list,
                                                   current_question_idx)

    if not question_data:
        await finish_hero_quiz(message, user_id)
        return

    # Проверяем, что ответ является одним из вариантов
    if message.text not in question_data["options"]:
        await message.answer(
            "❌ Пожалуйста, выберите один из предложенных вариантов ответа."
        )
        return

    # Проверяем ответ и увеличиваем счетчик, если правильно
    is_correct = hero_quiz_manager.check_answer(question_data, message.text)
    if is_correct:
        quiz_data["score"] += 1

    # Переходим к следующему вопросу
    quiz_data["current_question"] += 1

    # Сразу отправляем следующий вопрос
    await send_hero_question(message, user_id)


async def finish_hero_quiz(message: types.Message, user_id: int):
    """Завершение викторины по героям"""
    if user_id not in hero_quiz_manager.quiz_data:
        return

    quiz_data = hero_quiz_manager.quiz_data[user_id]
    score = quiz_data["score"]
    total = quiz_data["total_questions"]
    hero_name = quiz_data["hero_name"]

    # Определяем оценку
    percentage = (score / total) * 100 if total > 0 else 0
    if percentage >= 90:
        grade = "🎉 Отлично!"
    elif percentage >= 75:
        grade = "👍 Очень хорошо!"
    elif percentage >= 60:
        grade = "🙂 Хорошо!"
    elif percentage >= 40:
        grade = "😐 Удовлетворительно"
    else:
        grade = "💪 Не очень..."

    result_text = (
        f"🎖️ *Викторина завершена: {hero_name}*\n\n"
        f"📊 *Ваш результат:*\n"
        f"• Правильных ответов: {score}/{total}\n"
        f"• Процент: {percentage:.1f}%\n"
        f"• Оценка: {grade}\n\n"
        f"🔄 Можете пройти викторину еще раз или выбрать другого героя!"
    )

    await message.answer(result_text, reply_markup=get_main_keyboard(),
                         parse_mode="Markdown")

    # Очищаем данные пользователя
    if user_id in hero_quiz_manager.quiz_data:
        del hero_quiz_manager.quiz_data[user_id]


async def cancel_hero_quiz(message: types.Message, state: FSMContext):
    """Отмена викторины по героям"""
    user_id = message.from_user.id

    if user_id in hero_quiz_manager.quiz_data:
        quiz_data = hero_quiz_manager.quiz_data[user_id]
        score = quiz_data["score"]
        current = quiz_data["current_question"]
        hero_name = quiz_data["hero_name"]

        await message.answer(
            f"🎖️ *Викторина отменена: {hero_name}*\n\n"
            f"📊 *Ваш результат:*\n"
            f"• Правильных ответов: {score}/{current}",
            reply_markup=get_main_keyboard,
            parse_mode="Markdown",
        )

        del hero_quiz_manager.quiz_data[user_id]

    await state.clear()
