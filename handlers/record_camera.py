from aiogram import Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InputMediaPhoto, FSInputFile
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, Filter

import asyncio

from datetime import datetime, timedelta
from pytz import timezone
import time

from config import *
from helpers.cameras import *
from loader import router, bot

from httpsrv import files

print(__file__, router)

help_text = \
""" 
/record - Запись видео с камеры
 """

ffmpeg_jobs = {}

class callback_actions(CallbackData, prefix='cams'):
    action: str
    item_id: int 


class callback_record(CallbackData, prefix='record'):
    action: str
    cam_id: int
    time: int


class callback_cancel(CallbackData, prefix='cancel'):
    action: str
    id: int


async def print_main_menu(chat_id: int, bot: Bot):
    builder = InlineKeyboardBuilder()
    for i, ou in config.cams_list.items():
        action = 'list_cabs'
        ou_id = id(ou)
        cbd = callback_actions(action=action, item_id=ou_id).pack()
        button = InlineKeyboardButton(text=i, callback_data=cbd)
        builder.add(button)
    builder.adjust(2)
    try:
        await bot.send_message(chat_id=chat_id, text='Пожалуйста, выберите корпус:', reply_markup=builder.as_markup())
    except Exception as ex:
        print(ex) 


@router.message(Command(commands=['record', 'list']), IsAdmin())
async def cam_command(message: Message, bot: Bot):
    try:
        await print_main_menu(message.chat.id, bot)
    except Exception as ex:
        print(ex)


@router.callback_query(callback_actions.filter(F.action == 'list_cabs'), IsAdmin())
async def cams_list_cabs(query: CallbackQuery, callback_data: callback_actions, bot: Bot):
    chat_id = query.message.chat.id
    ou = obj_by_id(callback_data.item_id)
    builder = InlineKeyboardBuilder()       
    for i, cab in ou.items():
        cab_id = id(cab)
        cbd = callback_actions(action='list_cams',
                               item_id=cab_id
                ).pack()
        button = InlineKeyboardButton(text=i, callback_data=cbd)
        builder.add(button)
    builder.adjust(2)
    try:
        await query.message.edit_text("Выберите кабинет:", reply_markup=builder.as_markup())
    except:
        await print_main_menu(chat_id, bot=bot)



@router.callback_query(callback_actions.filter(F.action == 'list_cams'), IsAdmin())
async def cams_list_cams(query: CallbackQuery, callback_data: callback_actions, bot: Bot):
    try:
        chat_id = query.message.chat.id
        cab = obj_by_id(callback_data.item_id)
        builder = InlineKeyboardBuilder()        
        for i, cam in cab.items():
            cam_id = id(cam)
            cbd = callback_actions(action='cams_otps',
                                item_id=cam_id).pack()
            button = InlineKeyboardButton(text=i, callback_data=cbd)
            builder.add(button) 
        builder.adjust(2)
        try:
            await query.message.edit_text("Выберите камеру:", reply_markup=builder.as_markup())  
        except:
            await print_main_menu(chat_id, bot=bot)
    except:
        await print_main_menu(chat_id, bot=bot)


@router.callback_query(callback_actions.filter(F.action == 'cams_otps'), IsAdmin())
async def cams_opts(query: CallbackQuery, callback_data: callback_actions, bot: Bot):  
    chat_id = query.message.chat.id
    builder = InlineKeyboardBuilder()        
  
    for i in range(30, 121, 30):
        btn = InlineKeyboardButton(text=f'Записать {i} минут', callback_data=callback_record(action='record', cam_id=callback_data.item_id, time=i).pack())
        builder.add(btn)
    
    builder.adjust(2)
    try:
        await query.message.edit_text("Выбеите опцию:", reply_markup=builder.as_markup()) 
    except:
        await print_main_menu(chat_id)


@router.callback_query(callback_record.filter(F.action == 'record'), IsAdmin())
async def cams_record(query: CallbackQuery, callback_data: callback_record, bot: Bot):     
    try:        
        ip = obj_by_id(callback_data.cam_id)
        video_url = f"rtsp://{config.cam_login}:{config.cam_password}@{ip}"   

        rec_time = callback_data.time * 60    
        cam_path_list = path_list_by_item_id(config.cams_list, callback_data.cam_id)[:-1] 
        file_prefix = '_'.join(cam_path_list).replace(' ', '_')  
        nowMSK = datetime.now(timezone('Europe/Moscow'))
        path = os.path.join(videos_path, time.strftime("%Y\\%B\\%d"), *cam_path_list)
        filename = nowMSK.strftime(f"{path}\\{file_prefix}_%Y.%m.%d_%H.%M.%S.mkv")
        if ping(ip):
            os.makedirs(path, exist_ok=True)            
            ffmpeg_command = "ffmpeg", "-rtsp_transport", "tcp", "-i", video_url, "-t", f"{rec_time}", "-codec", "copy", filename,
            process = await asyncio.create_subprocess_exec(
                *(ffmpeg_command),
                stdout=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )  
            job_id = id(process)

            job = {
                'process': process,
                # 'message': query,
                'timestamp': datetime.now()
            }

            ffmpeg_jobs[job_id] = job 
            # print(ffmpeg_jobs) 

            builder = InlineKeyboardBuilder()        
            btn_cancel= InlineKeyboardButton(text='Завершить запись', callback_data=callback_cancel(action='cancel', id=job_id).pack())
            builder.add(btn_cancel)
            msg = await bot.send_message(query.from_user.id, f"⏳ Запись начата\n<i><b>{os.path.basename(filename)}</b></i>\nПродолжительность: {callback_data.time} минут", reply_markup=builder.as_markup()) 
            
            try:
                res = await asyncio.wait_for(process.communicate(), rec_time + 10) 
            except asyncio.TimeoutError as e:
                await query.message.answer(text=f"Ошибка отклика камеры: {os.path.basename(filename)}")
                return
            finally: 
                await msg.delete() 

            if process.returncode == 0:                
                hash = generate_hash(16)
                files[hash] = filename
                href = f'<a href="http://{config.base_url}:{config.base_port}/{hash}">Скачать</a>?'  
                time_diff = datetime.now() - job.get('timestamp')                           
                await query.message.answer(f"Файл <i><b>{os.path.basename(filename)}</b></i> записан\nПродолжительность: {timedelta(seconds=int(time_diff.total_seconds()))}\n{href}")
                ffmpeg_jobs.pop(job_id)
            else:
                await query.message.answer(f"Во время записи <i><b>{os.path.basename(filename)}</b></i> произошла ошибка")
                file_stats = os.stat(filename)
                if file_stats.st_size == 0:
                    os.remove(filename)
        else:
            camera = path_by_item_id(config.cams_list, callback_data.cam_id)
            await bot.answer_callback_query(query.id, text=f"Камера недоступна:\n{camera}", show_alert=True)
    except Exception as Ex:
        print(Ex)
    finally:
        try:
            await query.message.delete() 
        except:
            pass


@router.callback_query(callback_cancel.filter(F.action == 'cancel'), IsAdmin())
async def cams_record(query: CallbackQuery, callback_data: callback_cancel, bot: Bot):
    try:
        job = ffmpeg_jobs.get(callback_data.id)
        if job:
            process = job.get('process')
            if process:
                # print(datetime.now() - timestamp)
                process.stdin.write('q'.encode("GBK"))        
                # await process.communicate()
                # process.terminate()
        else:
            await query.message.reply("Данная запись уже завершена")
    except Exception as Ex:
        print(Ex)