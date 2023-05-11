import random
import string
import ctypes
import socket
import os
from aiogram.filters import Filter
from aiogram.types import Message
import config


class IsAdmin(Filter):
    # def __init__(self, my_text: str) -> None:
    #     self.my_text = my_text

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in config.admin_ids or message.chat.id in config.chat_ids
    

def IsGroup(chat_type: str):
    return chat_type in ('group', 'supergroup')


def generate_hash(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def obj_by_id(_id: int):
    try:
        result = ctypes.cast(_id, ctypes.py_object).value
        return result
    except:
        return None


def key_by_item_id(array: dict, _id: int):
    for k, v in array.items():
        if id(v) == _id:
            return k
        if isinstance(v, dict):
            item = key_by_item_id(v, _id)
            if item is not None:
                return item
            
            
def path_by_item_id(array: dict, _id: int, path: str = None) -> str:
    for k, v in array.items():
        if id(v) == _id:
            return ", ".join(filter(None, [path, k]))
        if isinstance(v, dict):
            item = path_by_item_id(v, _id, ", ".join(filter(None, [path, k])))
            if item is not None:
                return item
            

def path_list_by_item_id(array: dict, _id: int, path: list = None) -> list:
    if path == None:
        path = []
    for k, v in array.items():
        if id(v) == _id:  
            path.insert(0, k) 
            path.append(v)                  
            return path
        if isinstance(v, dict):                                          
            item = path_list_by_item_id(v, _id, path)
            if item is not None:
                path.insert(0, k)                 
                return item
            

def get_check_list(array: dict):
    result = []
    def FindValues(dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                FindValues(value)               
            else:
                result.append(value)  
    FindValues(array)             
    
    return result     


def parent_by_item_id(array: dict, _id: int, parent: int = None) -> int:
    for k, v in array.items():
        if id(v) == _id:
            return parent
        else:
            if isinstance(v, dict):
                item = parent_by_item_id(v, _id, id(v)) 
                if item is not None:
                    return item
            
            
def print_dict(array: dict):
    for i, j in array.items():
        print(id(i), i, id(j), j)
        if isinstance(j, dict):
            print_dict(j)


def ping(host):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)  
    try:
        result = sock.connect_ex((host, 554))
        return (result == 0)
    except:
        return False
    
def clear_videos():
    try:
        files = os.listdir(config.tmp_path)
        for file in [filtered for filtered in files if filtered.endswith('.mp4') or filtered.endswith('.jpg')]:
            os.remove(os.path.join(config.tmp_path, file))
            # print(file)
    except Exception as Ex:
        pass