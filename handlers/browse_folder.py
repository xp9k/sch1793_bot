from aiogram import Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, Filter
from  aiogram.exceptions import TelegramEntityTooLarge

from helpers.cameras import *
from config import videos_path
from loader import router
from httpsrv import files

print(__file__, router)

folder_to_browse = {}

class callback_browse(CallbackData, prefix='browse'):
    action: str
    next_index: int


def get_subfolder_by_index(folder: str, index: int):
    i = 0
    content = os.listdir(folder)
    for item in content:
        if i == index:
            return item
        i += 1
    return ''


@router.message(Command(commands=['browse', 'explore']), IsAdmin())
async def browse_command(message: Message):
    try:
        if not os.path.isdir(videos_path):
            os.mkdir(videos_path)
        content = os.listdir(videos_path)
        builder = InlineKeyboardBuilder()
        if len(content) > 0:
            index = 0
            for item in content:
                if os.path.isdir(os.path.join(videos_path, item)):
                    text = f"📁 {item}"
                else:
                    text = item  
                folder_to_browse[message.chat.id] = videos_path # os.path.join(videos_path, item)  
                cbd = callback_browse(action="folder", 
                                      next_index=0
                                      ).pack()              
                button = InlineKeyboardButton(text=text, callback_data=cbd)
                builder.add(button) 
                index += 1
            builder.adjust(1)
            await message.answer('Пожалуйста, выберите папку:', reply_markup=builder.as_markup())
        else:
            await message.answer('Папка пуста')
    except Exception as ex:
        print(ex)


@router.callback_query(callback_browse.filter(F.action == 'folder'), IsAdmin())
async def browse_folders(query: CallbackQuery, callback_data: callback_browse, bot: Bot):
    try:
        chat_id = query.message.chat.id
        next_folder = get_subfolder_by_index(folder_to_browse.get(chat_id) or videos_path, int(callback_data.next_index))
        folder = os.path.join(folder_to_browse.get(chat_id) or videos_path, next_folder)
        folder_to_browse[chat_id] = folder
        next_index = callback_data.next_index
        try:
            if next_index == -1:                
                folder = "\\".join(folder.split("\\")[:-2])
                folder_to_browse[chat_id] = folder
        except:
            folder = videos_path
            folder_to_browse[chat_id] = folder
        
        if os.path.isfile(folder):
            filename = os.path.basename(folder)
            try:
                msg = await query.message.answer(f"⏳ Загружаю видео {filename}")
                await bot.send_chat_action(chat_id, 'upload_video')
                video = open(folder, 'rb')
                await bot.send_video(chat_id=chat_id, video=video, caption=filename)
            except TelegramEntityTooLarge:
                await query.message.answer(f"Файл {filename} слишком большой для отправки")
            except Exception as Ex:
                print(Ex)
            finally:
                await msg.delete()                    
        else:      
            content = os.listdir(folder)
            if len(content) != 0:
                builder = InlineKeyboardBuilder()
                index = 0
                for item in content:
                    if os.path.isdir(os.path.join(folder, item)):
                        text = f"📁 {item}"
                        callback_data = callback_browse(action='folder', next_index=f"{index}").pack()
                        button = InlineKeyboardButton(text=text, callback_data=callback_data)
                        builder.add(button)
                        builder.adjust(4)
                    else:
                        text = f"🎬 {item}"
                        hash = generate_hash(16)
                        files[hash] = os.path.join(folder, item)
                        button = InlineKeyboardButton(text=text, url=f'http://{config.base_url}:{config.base_port}/' + hash)
                        builder.add(button) 
                        builder.adjust(1)
                    index += 1   
                btn_back = InlineKeyboardButton(text='⬅️ Назад', callback_data=callback_browse(action='folder',
                                                                                               next_index=-1).pack())
                builder.row(btn_back)
                            
                await query.message.edit_text("Выберите папку/файл", reply_markup=builder.as_markup())  
            else:
                folder_to_browse[chat_id] = videos_path
                builder = InlineKeyboardBuilder()
                button = InlineKeyboardButton(text=f'⬅️ Назад', callback_data=callback_browse(action='folder',
                                                                                            next_index=-1).pack())
                builder.add(button)            
                await query.message.edit_reply_markup(query.message.message_id, reply_markup=builder.as_markup())
    except:
        await query.message.delete()
        await browse_command(query.message)