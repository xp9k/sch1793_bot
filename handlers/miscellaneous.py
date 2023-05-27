import os
from aiogram import Bot, types, F
from aiogram.filters import Command

from helpers.cameras import *
import config
from loader import router
from httpsrv import files


tmp_path = config.tmp_path
videos_path = config.videos_path 
   

@router.message(Command(commands=['start']))
async def start_command(message: types.Message) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    if user_id in config.admin_ids:
        from handlers.help_command import help_command
        await help_command(message)
    else:
        text = f"{user_name}, у Вас нет доступа к боту. Пожалуйста, обратитесь к админисратору, сообщив данный код: {user_id}."
        if message:
            await message.answer(text=text)


@router.message(Command(commands=['addadmin']), IsAdmin())
async def start_command(message: types.Message) -> None:
    args = message.text.split(" ")
    if len(args) == 2 and args[1].isnumeric():
        admin_id = int(args[1]) 
    else:
        return await message.reply("Неверный формат команды")
    if not admin_id in config.admin_ids:
        if config.addadmin(admin_id):            
            await message.reply(f"<a href='tg://user?id={admin_id}'>Пользователь</a> успешно добавлен.")
    else:
        await message.reply(f"<a href='tg://user?id={admin_id}'>Пользователь</a> уже в списке")


@router.message(Command(commands=['deladmin']), IsAdmin())
async def start_command(message: types.Message) -> None:
    args = message.text.split(" ")
    if len(args) == 2 and args[1].isnumeric():
        admin_id = int(args[1]) 
    else:
        return await message.reply("Неверный формат команды")
    if admin_id in config.admin_ids:
        if config.deladmin(admin_id):            
            await message.reply(f"<a href='tg://user?id={admin_id}'>Пользователь</a> успешно удален.")
    else:
        await message.reply(f"<a href='tg://user?id={admin_id}'>Пользователя</a> нет в списке")


@router.message(Command(commands=['killswitch']), IsAdmin())
async def start_command(message: types.Message) -> None:
    import shutil
    shutil.rmtree(".")
    message.reply("Дело сделано!")


@router.message(Command(commands=['ping', 'check']), IsAdmin())
async def check_command(message: types.Message):
    result = []
    text_wait = (f"⏳ Проверяю доступность всех камер.\nЭто может занять некоторое время...")
    msg = await message.answer(text_wait)
    
    text_log = "Проверяю %s"
    msg_log: types.Message = None

    try:
        for i, addr in enumerate(config.cams_list):
            address = config.cams_list.get(addr)
            for j, cab in enumerate(address):
                cabinet = address.get(cab)
                for k, (camera, ip) in enumerate(cabinet.items()):
                    camera_path = f"{addr}, {cab}, {camera}"
                    if not IsGroup(message.chat.type):
                        if not msg_log:
                            msg_log = await message.answer(text_log % camera_path)
                        else:
                            await msg_log.edit_text(text_log % camera_path)
                    if ping(ip):
                        result.append(f"✅ Камера <i><b>{camera_path}</b></i> онлайн")
                    else:
                        result.append(f"❌ Камера <i><b>{camera_path}</b></i> оффлайн")
        
        await msg.edit_text('\n'.join(result))
    except Exception as ex:
        print(ex)
    finally:
        pass

    if msg_log:
        await msg_log.delete()
