from aiogram.types import Message
from storage import user_chat_ids
from configurations.keyboards import get_admin_keyboard


async def stat_button(message: Message):
    """Возращение в главное меню."""

    await message.answer(
        f"Число активных пользователей: {len(user_chat_ids)}",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML",
    )
