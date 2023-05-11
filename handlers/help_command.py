from aiogram import Bot
from aiogram.types import Message
from aiogram.filters import Command

from helpers.cameras import IsAdmin
from loader import router


help_text = \
""" 
/start - Начало
/ping - Проверка доступности камер
/record - Запись видео с камеры
/campic - Скриншоты с выбранных камер
/camvid - Видео с выбранных камер
/browse - Просмотр и загрузка записанных видео с камер
/help - Справка
 """


@router.message(Command(commands=['help']), IsAdmin())
async def help_command(message: Message):
    await message.answer(help_text)