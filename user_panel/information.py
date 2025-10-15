"""Обработчик кнопки '⚙️ Информация о проекте'"""
from aiogram.types import Message

from configurations.keyboards import get_cancel_keyboard


async def information_button(message: Message):
    """Обработчик кнопки '⚙️ Информация о проекте'"""
    await message.answer(
        "🏛️ Проект разработан учащимися 9 'А' класса СШ №16 им."
        "Агадила Сухомбаева\n\n"
        "👨‍💻 Разработчик: Васильчиков Алексей Дмитриевич\n"
        "✍️ Текст: Ольшевская Анастасия Михайловна\n\n"
        "💻 Технологии:\n"
        "   • Язык программирования: Python\n"
        "   • Библиотеки: aiogram, python-dotenv, requests\n\n"
        "🎯 Цели проекта:\n"
        "   • Формирование патриотизма у молодого поколения посредством"
        " использования современных информационно-коммуникационных"
        " технологий.\n",
        reply_markup=get_cancel_keyboard()
        )
