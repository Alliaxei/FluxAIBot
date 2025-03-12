from aiogram import Bot
from aiogram.types import BotCommand


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command='start', description='Перезапустить бота'),
        BotCommand(command='help', description='Помощь'),
        BotCommand(command='buy', description='Покупка кредитов'),
        BotCommand(command='generate', description='Быстрая генерация'),
        BotCommand(command='profile', description='Информация о пользователе'),
        BotCommand(command='styles', description='Доступные стили'),
        BotCommand(command='quality', description='Разрешение изображения'),
        BotCommand(command='settings', description='Настройка параметров'),
        BotCommand(command='support', description='Техподдержка'),
    ]
    await bot.set_my_commands(commands)
