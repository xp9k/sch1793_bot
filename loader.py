from aiogram import Bot, Dispatcher, Router
import config

router = Router()
bot = Bot(token=config.TELEGRAM_TOKEN, parse_mode="HTML")

dp = Dispatcher()
dp.include_router(router)    
dp.bot = bot