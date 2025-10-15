from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from data.google_sheets import sheets_manager

leaderboard_router = Router()


def get_score_text(score):
    """Склонение слова 'балл' в зависимости от числа"""
    if score % 10 == 1 and score % 100 != 11:
        return f"{score} балл"
    elif score % 10 in [2, 3, 4] and score % 100 not in [12, 13, 14]:
        return f"{score} балла"
    else:
        return f"{score} баллов"


def format_leaderboard():
    """Форматирование таблицы лидеров из Google Sheets"""
    try:
        # Получаем все результаты
        all_results = sheets_manager.get_all_results()

        if not all_results:
            return "🏆 <b>Топ пять лучших учеников:</b>\n\n1."
        " —\n2. —\n3. —\n4. —\n5. —"

        # Сортируем по количеству правильных ответов (по убыванию)
        sorted_results = sorted(
            all_results, key=lambda x: int(x.get("Correct Answers", 0)),
            reverse=True
        )

        # Берем топ-5 результатов
        top_results = sorted_results[:5]

        # Формируем текст таблицы лидеров
        leaderboard_text = "🏆 <b>Топ пять лучших учеников:</b>\n\n"

        for i, result in enumerate(top_results, 1):
            last_name = result.get("Last Name", "").strip()
            first_name = result.get("First Name", "").strip()
            correct_answers = int(result.get("Correct Answers", 0))

            # Форматируем имя
            if last_name and first_name:
                name = f"{last_name} {first_name}"
            elif first_name:
                name = first_name
            elif last_name:
                name = last_name
            else:
                name = "Неизвестный"

            # Используем правильное склонение слова "балл"
            score_text = get_score_text(correct_answers)
            leaderboard_text += f"{i}. {name} - {score_text}\n"

        # Добавляем информацию об общем количестве участников
        total_participants = len(all_results)
        leaderboard_text += f"\n📊 Всего участников: {total_participants}"

        return leaderboard_text

    except Exception as e:
        # Логируем ошибку для отладки
        print(f"Ошибка при форматировании таблицы лидеров: {e}")
        return "❌ Ошибка при загрузке таблицы лидеров. Попробуйте позже."


@leaderboard_router.message(Command("leaders"))
async def show_leaderboard(message: Message):
    """Показать таблицу лидеров"""
    leaderboard_text = format_leaderboard()
    await message.answer(leaderboard_text, parse_mode="HTML")
