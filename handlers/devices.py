from aiogram import Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile, InputMediaPhoto
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, Filter
import time

from config import *
from helpers.cameras import IsAdmin

import json
import os

from loader import router, bot

print(__file__, router)

devices = {
    # inv_number: {
    #     type: str,
    #     name: str,
    #     serial: str,
    #     ou: str,
    #     cab: person,
    #     person: str,    
    # }
}

def save_devices():
    with open("devices.json", "w", encoding='utf-8') as fp:
        json.dump(devices, fp, sort_keys=True, indent=4, ensure_ascii=False) 


def load_devices():
    global devices
    if os.path.isfile("devices.json"):
        with open("devices.json", "r", encoding='utf-8') as fp:
            devices = json.load(fp)


def find_images(inv: str):
    if os.path.exists(images_path):
        files = os.listdir(images_path)
        result = []
        for file in [filtered for filtered in files if filtered.startswith(inv)]:
            result.append(os.path.join(images_path, file))
        return result
    else:
        return []
    
    
def parse_device(device: str):
    fields = list(item.strip() for item in device.split(','))
    if len(fields) <= 1:
        return False
        
    inv_no = fields[0]

    if not inv_no.isnumeric():
        return False
    if inv_no == None:
        return False
    
    if devices.get(inv_no) is None:
        devices[inv_no] = {
            'type': None,
            'name': None,
            'serial': None,
            'person': None,
            'ou': None,  
            'updated_by': None,        
        }
    
    counter = 0
    for field in fields:
        field = field.strip()
        if '=' in field:
            params = field.split('=')
            if len(params) == 2:
                if params[0] == 'type':
                    devices[inv_no]['type'] = params[1]
                if params[0] == 'name':
                    devices[inv_no]['name'] = params[1]
                if params[0] == 'serial':
                    devices[inv_no]['serial'] = params[1]
                if params[0] == 'ou':
                    devices[inv_no]['ou'] = params[1]
                if params[0] == 'cab':
                    devices[inv_no]['cab'] = params[1]
                if params[0] == 'person':
                    devices[inv_no]['person'] = params[1]
                
        else:
            try:
                match counter:
                    case 1:
                        devices[inv_no]['type'] = field
                    case 2:
                        devices[inv_no]['name'] = field
                    case 3:
                        devices[inv_no]['serial'] = field
                    case 4:
                        devices[inv_no]['ou'] = field
                    case 5:
                        devices[inv_no]['cab'] = field
                    case 6:
                        devices[inv_no]['person'] = field
                    
            except Exception as Ex:
                print(Ex)        
        counter += 1
    # dblite.update_device_info(inv_no, devices[inv_no])
    return True


def get_device_info(inv_no):
    data = devices.get(inv_no)

    if data is not None:
        return f"Инвентарный номер: {inv_no}\nУстройство: {data.get('type') or '-'} {data.get('name') or '-'}\nСерийный номер: {data.get('serial') or '-'}\nНаходится: {data.get('ou') or '-'}, кабинет {data.get('cab') or '-'}\nЗаписан на: {data.get('person') or '-'}"
    else:
        return "Устройство не существует"
    
    
@router.message(Command(commands=['info']), IsAdmin())
async def info_command(message: Message, bot: Bot):
    try:
        # await message.delete()     
        request = ", ".join(message.text.split(' ')[1:])

        data = devices.get(request)

        text = ''
        if data is not None:
            text = get_device_info(request)
        else:
            await message.answer('Устройство не найдено\nИспользование:\n/info инвентарный номер')
            return

        # try:
        #     text = sqldb.inv_info(request)
        # except:
        #     text = request

        images = find_images(request)
        photos = []
        for image in images:
            photo = FSInputFile(image, image)
            media = InputMediaPhoto(type='photo', media=photo, caption=text)
            photos.append(media)

        if len(images) > 0:
            await bot.send_media_group(chat_id=message.chat.id, media=photos)
        else:
            await message.answer(text)
    except Exception as ex:
        print(ex)


@router.message(Command(commands=['import']), F.content_type.in_({'document'}), IsAdmin())
async def handle_docs_text(message: Message, bot: Bot):
    
    def import_file_generator(filename: str):
        for line in open(filename, "r"):
            yield line

    filename = f"{os.path.join(tmp_path, message.document.file_name)}"
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, filename)
    count = 0
    for line in import_file_generator(filename):        
        if parse_device(line.strip()):
            count += 1
    await message.answer(f"Обработано записей: {count}")
    os.remove(filename)
    save_devices()


@router.message(Command(commands=['update']), IsAdmin())
async def update_command(message: Message):
    args = message.text.replace('/update ', '').split('\n')
    text = f"Использование команды /update:\n" \
            "/update инв. номер, тип устройства, название, серийник, школьное отделение, кабинет, сотрудник\n" \
            "Или можно редактировать поля отдельно (в комбинациях):\n" \
            "/update инв. номер, type=тип устройства, name=Название, serial=серийник, ou=школьное отделение, cab=кабинет, person=сотрудник"

    if message.text.strip() == '/update':
        await message.answer(text)
        return
    
    for arg in args:
        if (arg.strip() == '/update'):
            continue
        if not parse_device(arg):
            await message.answer(text)
        else:
            inv_no = arg.split(',')[0].strip()
            devices[inv_no]['updated_by'] = f"{message.from_user.full_name}_{message.from_user.id}"
            await message.reply(f'Устройство добавлено/изменено: {arg}')
            time.sleep(1)
    save_devices()