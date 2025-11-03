from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

import storage


def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚙️ Просмотреть статистику")],
            [KeyboardButton(text="Начать рассылку")],
        ],
        resize_keyboard=True,
    )


def get_main_keyboard():
    """Основная клавиатура главного меню."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💪 Узнать о героях"),
                KeyboardButton(text="🎯 Викторина"),
            ],
            [KeyboardButton(text="🤖 Поговорить с ИИ")],
            [
                KeyboardButton(text="👸 Таблица лидеров"),
                KeyboardButton(text="⚙️ Информация о проекте"),
            ],
        ],
        resize_keyboard=True,
    )


def get_quiz_mode_keyboard(can_play_competitive=True):
    """Клавиатура для выбора режима викторины."""
    competitive_button = (
        [KeyboardButton(text="🏆 Соревновательный режим")]
        if can_play_competitive
        else []
    )

    keyboard_rows = [
        [KeyboardButton(text="🎖️ Викторины по героям")],
        competitive_button,
        [KeyboardButton(text="🎯 Пробный режим")],
        [KeyboardButton(text="⏹️ Назад в меню")],
    ]

    keyboard_rows = [row for row in keyboard_rows if row]
    return ReplyKeyboardMarkup(keyboard=keyboard_rows, resize_keyboard=True)


def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏹️ Назад в меню")]], resize_keyboard=True
    )


def get_quiz_question_keyboard(options):
    """
    Создает клавиатуру для вопросов викторины.
    Варианты ответов распределяются по 4 строкам, 5-я строка - отмена.
    """
    keyboard = []

    # Распределяем варианты ответов по 4 строкам
    total_options = len(options)

    if total_options <= 4:
        # Если вариантов 4 или меньше - по одному в ряд
        for option in options:
            keyboard.append([KeyboardButton(text=option)])
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
                    KeyboardButton(text=options[i])
                    for i in range(index, index + row_items)
                ]
                keyboard.append(row_buttons)
                index += row_items

    # Добавляем кнопку отмены в отдельный ряд
    keyboard.append([KeyboardButton(text="⏹️ Завершить викторину")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# Клавиатуры для героев
def create_heroes_keyboard(page: int = 0):
    """Создание клавиатуры героев с пагинацией"""
    heroes_per_page = 5
    total_heroes = len(storage.HERO_URLS)

    # Защита от выхода за границы массива
    if page < 0:
        page = 0

    total_pages = (total_heroes + heroes_per_page - 1) // heroes_per_page
    if page >= total_pages:
        page = total_pages - 1

    start_index = page * heroes_per_page
    end_index = min(start_index + heroes_per_page, total_heroes)

    keyboard = []

    # Добавляем кнопки героев для текущей страницы с именами из HERO_NAMES
    for i in range(start_index, end_index):
        hero_id = i + 1
        hero_name = storage.HERO_NAMES.get(hero_id, f"Герой №{hero_id}")
        keyboard.append(
            [InlineKeyboardButton(text=hero_name, url=storage.HERO_URLS[i])]
        )

    # Добавляем кнопки навигации
    navigation_buttons = []

    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад", callback_data=f"heroes_page_{page - 1}"
            )
        )

    # Показываем номер текущей страницы
    if total_pages > 1:
        navigation_buttons.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}", callback_data="heroes_current_page"
            )
        )

    if page < total_pages - 1:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Далее ➡️", callback_data=f"heroes_page_{page + 1}"
            )
        )

    if navigation_buttons:
        keyboard.append(navigation_buttons)

    # Добавляем кнопку возврата в главное меню
    keyboard.append(
        [InlineKeyboardButton(text="⏹️ Назад в меню", callback_data="main_menu")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Оригинальная клавиатура для первой страницы
# (сохранено для обратной совместимости)
heroes_keyboard = create_heroes_keyboard(0)
