from aiogram import Bot, Dispatcher, Router
import asyncio
from datetime import datetime
from loader import router, dp, bot
import handlers
import httpsrv


async def timer():
    while True:
        print(datetime.now())
        await asyncio.sleep(1)


async def on_startup(dispatcher: Dispatcher):
    from config import admin_ids
    print(f"Бот запущен в {datetime.now()}")
    # for admin in admin_ids:
    #     try:
    #         await dispatcher.bot.send_message(admin, "Бот вновь запущен")
    #     except Exception as Ex:
    #         print(Ex)
    

async def on_stop(dispatcher: Dispatcher):
    print(f"Бот отключен в {datetime.now()}")


async def start_bot():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_stop)   

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, skip_updates=dp.resolve_used_update_types())


def main() -> None:
    loop = asyncio.new_event_loop()
    # loop.create_task(timer())
    loop.create_task(start_bot())
    loop.create_task(httpsrv.main())
    loop.run_forever()


if __name__ == '__main__':    
    main()
    