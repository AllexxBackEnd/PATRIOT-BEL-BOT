from aiogram.types import Message, ReplyKeyboardRemove

import storage
from configurations.keyboards import heroes_keyboard


async def heroes_button(message: Message):
    """Обработчик кнопки 'Узнать о героях'."""
    total_heroes = len(
        storage.HERO_URLS) if hasattr(storage, "HERO_URLS") else 0 - 1

    await message.answer(
        f"🎖️ *Герои Великой Отечественной войны*\n\n"
        f"📚 Доступно {total_heroes} героев\n",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown",
    )

    await message.answer(
        "📖 Используйте кнопки навигации для просмотра всех героев\n\n"
        "Выберите героя для просмотра информации:",
        reply_markup=heroes_keyboard
    )
