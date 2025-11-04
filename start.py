import logging

from aiogram.types import Message

import storage
from configurations.keyboards import get_main_keyboard, get_admin_keyboard

# Инициализация логгера
logger = logging.getLogger("bot_logger")


async def process_start_command(message: Message):
    """Обработчик команды /start."""
    # Регистрируем пользователя в системе
    storage.user_chat_ids.add(message.chat.id)

    logger.info(f"Новый пользователь: {message.chat.id}. "
                f"Всего пользователей: {len(storage.user_chat_ids)}")

    if message.chat.id not in storage.admin_IDs:
        await message.answer_photo(
            photo="https://i.postimg.cc/nc3m01gT/IMG-1791.jpg",
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
    else:
        await message.anwer('Вы находитесь в админ панели.', reply_markup=get_admin_keyboard())
