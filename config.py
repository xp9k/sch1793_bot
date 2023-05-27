import json
import os
from dotenv import load_dotenv, find_dotenv, set_key

def addadmin(admin_id: int) -> bool:
    try:
        admin_ids.append(admin_id)
        value: str = ", ".join(map(str, admin_ids))
        set_key(dotenv_path=find_dotenv(), key_to_set="admin_ids", value_to_set=value, quote_mode="never")
        return True
    except:
        return False
    

def deladmin(admin_id: int) -> bool:
    try:
        admin_ids.remove(admin_id)
        value: str = ", ".join(map(str, admin_ids))
        set_key(dotenv_path=find_dotenv(), key_to_set="admin_ids", value_to_set=value, quote_mode="never")
        return True
    except:
        return False


with open("cameras.json", encoding='utf-8') as config_file:
    cams_list = json.load(config_file)

load_dotenv(find_dotenv()) 

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") or ""

cam_login    = os.environ.get("cam_login") or "subaccount"
cam_password = os.environ.get("cam_password") or "SecurePassword"

base_url  = os.environ.get("base_url") or "127.0.0.1"
base_port = os.environ.get("base_port") or 8000

admin_ids = os.environ.get("admin_ids")
if admin_ids is not None:
    admin_ids = [int(admin.strip()) for admin in admin_ids.split(",")]

chat_ids  = os.environ.get("chat_ids")    
if chat_ids is not None:
    chat_ids = [int(chat.strip()) for chat in chat_ids.split(",")]


tmp_path  = os.environ.get("tmp_path") or "tmp"
if not os.path.isdir(tmp_path):
    os.makedirs(tmp_path)
images_path = os.environ.get("images_path") or "images"
if not os.path.isdir(images_path):
    os.makedirs(images_path)
videos_path = os.environ.get("videos_path") or "videos"
if not os.path.isdir(videos_path):
    os.makedirs(videos_path)