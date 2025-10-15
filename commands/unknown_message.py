from aiogram import types


async def unknown_message(message: types.Message):
    """Обработчик неизвестных сообщений."""
    await message.answer(
        "❓ <b>Неизвестная команда</b>\n\n"
        "Используйте кнопки меню или команды:\n"
        "• /main_menu - главное меню\n"
        "• /help - помощь\n",
        parse_mode="HTML",
    )
