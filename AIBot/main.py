import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from apps.handlers.commands import router as commands_router
from apps.handlers.callbacks import router as callbacks_router
from apps.handlers.states import router as states_router
from apps.commands import set_bot_commands
from apps.handlers.invoice_handlers import router as invoice_router


async def main():
    load_dotenv('.env')
    bot = Bot(token=os.getenv("TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(commands_router)
    dp.include_router(callbacks_router)
    dp.include_router(states_router)
    dp.include_router(invoice_router)


    try:
        await set_bot_commands(bot)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        print('error', e)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting...")