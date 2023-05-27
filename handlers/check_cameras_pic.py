from aiogram import Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InputMediaPhoto, FSInputFile
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, Filter
import shutil
import cv2
from config import *
from helpers.cameras import *
from loader import router, bot

help_text = \
""" 
/campic - Фото с выбранных камер
 """


class callback_check_camera(CallbackData, prefix='campic'):
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
    

async def check_cam(cam_data_list: list, message: Message):
    output_dir = os.path.join(tmp_path, str(message.from_user.id))
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    offline_cameras = []
    text_wait = (f"⏳ Проверяю доступность камер.\nЭто может занять некоторое время...")
    msg = await message.answer(text_wait)

    text_log = "Проверяю %s"
    msg_log: Message = None

    cameras_info = []

    for cam in cam_data_list:
        cam_data = path_list_by_item_id(cams_list, id(cam))
        camera_path = ", ".join(cam_data[:-1])
        ip = cam_data[-1]
        if not msg_log:
            msg_log = await message.answer(text_log % camera_path)
        else:
            await msg_log.edit_text(text_log % camera_path)
        if ping(ip):
            rtsp_url = f"rtsp://{cam_login}:{cam_password}@{ip}:554"
            cap = cv2.VideoCapture(rtsp_url)
            ret, frame = cap.read()
            if ret:
                filename = f"{ip}.jpg"
                filepath = os.path.join(output_dir, filename)
                cv2.imwrite(filepath, frame)  
                cameras_info.append({
                    'filename': filename,
                    'description': camera_path,
                })              
            else:
                offline_cameras.append(f"{camera_path}, {ip}")
            cap.release()
        else:
            offline_cameras.append(f"{camera_path}, {ip}")

    try:
        await msg.delete()
        await msg_log.delete()
    except:
        pass

    photos = []
    for i, info in enumerate(cameras_info):
        filename = os.path.join(output_dir, info.get('filename'))
        photo = FSInputFile(filename, filename)
        online_text = info.get("description")
        media = InputMediaPhoto(type='photo', media=photo, caption=online_text)
        photos.append(media)
        if (i + 1) % 10 == 0:
            await message.answer_media_group(media=photos)
            photos = []
    if len(photos) > 0:
        await message.answer_media_group(media=photos)

    if offline_cameras != []:
        offline_text = '\n'.join(offline_cameras)
        await message.answer(f"Отключенные камеры:\n{offline_text}")  

    shutil.rmtree(output_dir)


@router.message(Command(commands=['campic']), IsAdmin())
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
        await message.answer(text='<b>Фото с камер</b>:', reply_markup=builder.as_markup())
    except Exception as ex:
        print(ex) 
    

@router.callback_query(callback_check_camera.filter(F.action == 'browse_cam'))
async def cams_browse(query: CallbackQuery, callback_data: callback_check_camera, bot: Bot):
    item_id = callback_data.item_id
    item = obj_by_id(item_id)
    if isinstance(item, dict):
        builder = build_buttons(item_id)
        if builder is not None:
            await query.message.edit_text(text='<b>Фото с камер</b>:', reply_markup=builder.as_markup())
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
        await query.message.edit_text(text='<b>Фото с камер</b>:', reply_markup=builder.as_markup())


@router.callback_query(callback_check_camera.filter(F.action == 'check'))
async def cams_browse_check(query: CallbackQuery, callback_data: callback_check_camera, bot: Bot):
    item_id = callback_data.item_id
    item = obj_by_id(item_id)
    check_list = []
    if isinstance(item, dict):
        check_list = get_check_list(item)
    else:
        check_list.append(item)

    await check_cam(cam_data_list=check_list, message=query.message)

    shutil.rmtree(tmp_path)