from aiogram.types import Message

from configurations.keyboards import get_main_keyboard


async def show_main_menu(message: Message):
    """Возращение в главное меню."""

    await message.answer_photo(
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
