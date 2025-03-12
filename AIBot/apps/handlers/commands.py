from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from aiogram.fsm.context import FSMContext
from aiogram.utils import markdown

from apps.keyboards import keyboards as kb
from apps.database import requests
from apps.handlers.callbacks import show_profile
from apps.states import ImageState, BuyingState
router = Router()

@router.message(Command('start'))
async def start_handler(message: Message):
    await requests.set_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer("🌟 Привет! Рад тебя видеть в Flux AI! 🎉\nНаш бот поможет тебе создавать потрясающие изображения. Выбирай, что хочешь, и давай начнем! 👇😊",
                         reply_markup=kb.main)

@router.message(Command('help'))
async def help_handler(message: Message):
    await message.answer(
        "*🤖 О боте Flux AI*\n\n"
        "Flux AI — это бот для создания изображений по текстовому описанию! 🖼️\n\n"
        "💰 *Система кредитов*\n"
        "— Для генерации изображений требуются кредиты.\n"
        "— Для пополнения баланса, вы можете использовать *систему оплаты через FreeKassa*.\n\n"
        "📌 *Как использовать Flux AI?*\n"
        "1️⃣ Для начала выберите параметры для создания изображения:\n"
        "   — *Стиль*\n"
        "   — *Качество*\n"
        "Эти настройки можно выбрать в меню или через меню быстрого доступа.\n"
        "2️⃣ Когда параметры настроены, выберите функцию создания изображения.\n"
        "3️⃣ Введите текстовое описание (промт) для генерации изображения.\n\n"
        "🖱️ *Меню быстрого доступа*\n"
        "В любое время вы можете использовать меню для быстрого выбора нужной опции: создать изображение, перейти в личный кабинет или пополнить баланс.\n\n"
        "🔄 *Перезапуск бота*\n"
        "Если возникли проблемы, просто используйте команду /start для перезапуска бота. 🔁\n\n"
        "*Пусть ваша креативность не имеет границ с Flux AI!* 🚀",
        parse_mode="Markdown"
    )

@router.message(Command('profile'))
async def profile_handler(message: Message):
    await show_profile(message)

@router.message(Command('generate'))
async def generate_handler(message: Message, state: FSMContext):
    user = await requests.get_user(message.from_user.id)
    await message.answer(f'Введите текстовое описание изображения...\n**Ваши кредиты:** `{user.credits}`',  parse_mode="Markdown",)
    await state.set_state(ImageState.waiting_for_prompt)


@router.message(Command('buy'))
async def buy_handler(message: Message, state: FSMContext):

    sent_message = await message.answer(
        'Выберите сумму для пополнения 💸',
        reply_markup=kb.credits
    )
    await state.set_state(BuyingState.waiting_for_transaction)
    await state.update_data(message_id=sent_message.message_id)

@router.message(Command('settings'))
async def settings_handler(message: Message):
    await message.answer(text='⚙️ Конфигурация и настройки ⚙️', reply_markup=kb.settings)

@router.message(Command('styles'))
async def styles_handler(message: Message):
    user = await requests.get_user(message.from_user.id)

    if not user:
        await message.answer("❌ Ошибка: пользователь не найден.")
        return

    keyboard = await kb.get_styles_keyboard(user.telegram_id)
    await message.answer(text=(
            '🎨 *Выбери стиль* для генерации изображения.\n\n'
            '💡  Стиль и размер изображения будут влиять на стоимость.\n'
            '💵 Убедись, что у тебя достаточно кредитов для выбранного варианта.'
        ),
        reply_markup=keyboard,
        parse_mode="Markdown")

@router.message(Command('quality'))
async def size_handler(message: Message):
    user = await requests.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Ошибка: пользователь не найден.")
        return
    keyboard = await kb.get_quality_keyboard(user.telegram_id)
    await message.answer("🎨 Выберите размер изображения:", reply_markup=keyboard)

@router.message(Command('support'))
async def support_handler(message: Message):
    await message.answer(
        'В случае каких-то вопросов обратитесь к [@Qwertyuqiwie]',
        parse_mode="Markdown"
    )