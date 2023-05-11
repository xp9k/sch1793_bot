from aiogram import Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, Filter
import asyncio
import subprocess
import shutil
from datetime import datetime, timedelta
from pytz import timezone
from config import *
from helpers.cameras import *
from loader import router, bot

print(__file__, router)

help_text = \
""" 
/camvid - Видео с выбранных камер
 """


class callback_check_camera(CallbackData, prefix='camvid'):
    action: str
    item_id: int


def build_buttons(_id) -> InlineKeyboardBuilder:
    array = obj_by_id(_id)
    
    if isinstance(array, dict):
        builder = InlineKeyboardBuilder()
        for key, item in array.items():
            if isinstance(item, dict):
                action = 'browse_cam'
            else:
                action = "check"
            item_id = id(item)            
            cbd = callback_check_camera(action=action, item_id=item_id).pack()
            button = InlineKeyboardButton(text=key, callback_data=cbd)
            builder.add(button)
            builder.adjust(2)
        btn_all = InlineKeyboardButton(text=f'Проверить все', callback_data=callback_check_camera(action='check', item_id=_id).pack())    
        builder.row(btn_all)
            
        if _id != id(cams_list):
            btn_back = InlineKeyboardButton(text=f'⬅️ Назад', callback_data=callback_check_camera(action='back', item_id=_id).pack())
            builder.row(btn_back)
        return builder
    else:
        return None
    

async def check_cam(cam_data: list, message: Message):
    try:

        if not os.path.isdir(tmp_path):
            os.makedirs(tmp_path)
        
        ip = cam_data[-1]
        video_url = f"rtsp://{cam_login}:{cam_password}@{ip}"
        
        caption = ", ".join(cam_data[:-1])
        if ping(ip):
            try:
                text_gif = (f"⏳ Подключаюсь к камере: {caption} \nЗапись может занять некоторое время...")
                msg = await message.answer(text_gif)
                nowMSK = datetime.now(timezone('Europe/Moscow'))
                timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                nowOut = nowMSK.strftime(f"{os.path.join(tmp_path, 'vid-%Y-%m-%d_%H-%M-%S.mp4')}")
                ffmpeg_command = ("ffmpeg", "-rtsp_transport", "tcp", "-i", video_url, "-t", "5", "-codec", "copy", nowOut)
                process = await asyncio.create_subprocess_exec(
                    *(ffmpeg_command),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,               
                )  
                try:
                    res = await asyncio.wait_for(process.communicate(), 10) 
                except asyncio.TimeoutError as e:
                    process.kill()
                    await message.answer(text=f"Ошибка отклика камеры: {caption}")
                    await msg.delete()
                    return
                probe_command = ("ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", nowOut)
                result = subprocess.run(
                    probe_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,             
                )  
                buffer = result.stdout
                data = json.loads(buffer)
                msg_text = 'Техданные:'
                for stream in data.get('streams'):
                    if stream.get('codec_type') == 'video':
                        msg_text += f"\nВидео: {stream.get('width')}x{stream.get('height')}, кодек: {stream.get('codec_long_name')}"  
                    if stream.get('codec_type') == 'audio':
                        msg_text += f"\nАудио: {stream.get('codec_long_name')}" 
                await msg.delete()
                if os.path.isfile(nowOut):
                    video = FSInputFile(nowOut, nowOut)
                    await message.answer_video(video, duration=5, caption=f"{caption}\n{timestamp}\n{msg_text}")
                    await message.answer()
                    os.remove(nowOut)
                else:
                    await message.answer(f"❌ Ошибка конвертизации")
            except Exception as _ex:
                if "Connection refused" in _ex.stderr.decode('utf8'):
                    await message.answer(f"❌ Ошибка подключения к камере:\nConnection refused")
                elif "401" in _ex.stderr.decode('utf8'):
                    await message.answer(f"❌ Ошибка подключения к камере:\nНеправильный логин или пароль")
        else:
            await message.answer(f"❌ Камера <i><b>{caption}</b></i> недоступна")
    except:
        pass


@router.message(Command(commands=['camvid']), IsAdmin())
async def camvid_command(message: Message):
    try:
        builder = InlineKeyboardBuilder()
        for i, ou in cams_list.items():
            action = 'browse_cam'
            ou_id = id(ou)
            cbd = callback_check_camera(action=action, item_id=ou_id).pack()
            button = InlineKeyboardButton(text=i, callback_data=cbd)
            builder.add(button)
        builder.adjust(2)
        btn_all = InlineKeyboardButton(text=f'Проверить все', callback_data=callback_check_camera(action='check', item_id=id(cams_list)).pack())
        builder.row(btn_all)
        await message.answer(text='<b>Видео с камер</b>:', reply_markup=builder.as_markup())
    except Exception as ex:
        print(ex)        


@router.callback_query(callback_check_camera.filter(F.action == 'browse_cam'))
async def cams_browse(query: CallbackQuery, callback_data: callback_check_camera, bot: Bot):
    item_id = callback_data.item_id
    item = obj_by_id(item_id)
    if isinstance(item, dict):
        builder = build_buttons(item_id)
        if builder is not None:
            await query.message.edit_text(text='<b>Видео с камер</b>:', reply_markup=builder.as_markup())
    else:
        print(item)


@router.callback_query(callback_check_camera.filter(F.action == 'back'))
async def cams_browse_back(query: CallbackQuery, callback_data: callback_check_camera, bot: Bot):
    item_id = callback_data.item_id
    parent_id = parent_by_item_id(cams_list, item_id, id(cams_list))
    if parent_id is None:
        parent_id = id(cams_list)
    builder = build_buttons(parent_id)
    if builder is not None:
        await query.message.edit_text(text='<b>Видео с камер</b>:', reply_markup=builder.as_markup())
        

@router.callback_query(callback_check_camera.filter(F.action == 'check'))
async def cams_browse_check(query: CallbackQuery, callback_data: callback_check_camera, bot: Bot):
    item_id = callback_data.item_id
    item = obj_by_id(item_id)
    check_list = []
    if isinstance(item, dict):
        check_list = get_check_list(item)
    else:
        check_list.append(item)

    for ip in check_list:
        cam_data = path_list_by_item_id(cams_list, id(ip))
        await check_cam(cam_data=cam_data, message=query.message)

    shutil.rmtree(tmp_path)