import asyncio
import os

import aiohttp
from aiogram import Router, F, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder

from sqlalchemy import select, func


from apps.database.database import async_session
from apps.database.models import Gallery
from apps.database.requests import update_user_size, add_credits, get_user_db_id, create_transaction, \
     get_transaction_by_order_id
from apps.keyboards import keyboards as kb
from apps.database import requests
from apps.keyboards.keyboards import get_styles_keyboard, get_quality_keyboard, back, \
    get_next_page_keyboard, get_payment_keyboard
from apps.services.payments import generate_payment_link
from apps.states import ImageState, BuyingState
from dotenv import load_dotenv

router = Router()
load_dotenv('.env')


DJANGO_PAYMENT_URL = os.getenv("DJANGO_PAYMENT_URL", "http://web:8000")

# Если бот запущен вне Docker
if os.getenv("DOCKER_RUNNING") != "true":
    SERVER_IP = os.getenv("SERVER_IP", "127.0.0.1")
    DJANGO_PAYMENT_URL = f"http://{SERVER_IP}:8000"


DJANGO_API_URL = f"{DJANGO_PAYMENT_URL}/api/check_payment/"
def get_profile_text(user) -> str:
    return (
        "✨ *Добро пожаловать в Личный кабинет* ✨\n\n"
        f"👤 Имя: *{user.first_name or 'Не указано'}*\n"
        f"🌐 Username: *@{user.username or 'Не указано'}*\n"
        f"📌 Telegram ID: `{user.telegram_id}`\n\n"
        f"🖼 Качество изображения: *{user.settings.image_size or 'Не указано'}*\n"
        f"🎨 Выбранный стиль: *{user.settings.selected_style or 'Не выбран'}*\n\n"
        
        f"💰 Кредиты: *{user.credits or 'Не указано'}* шт.\n\n"
        
        "=======================\n"
        "Выберите действие:\n"
    )

@router.callback_query(F.data == 'generate_image')
async def generate_image_handler(callback: CallbackQuery, state: FSMContext):
    user = await requests.get_user(callback.from_user.id)
    await callback.message.edit_text(f'Введите текстовое описание изображения...\n**Ваши кредиты:** `{user.credits}`',
                                     parse_mode="Markdown",
                                     reply_markup=kb.back,
                                   )
    await state.set_state(ImageState.waiting_for_prompt)

async def show_profile(message: Message):
    user = await requests.get_user(message.from_user.id)

    if user is None:
        await message.answer(
            text='Ошибка, пользователь не найден\nПопробуйте перезапустить бота с помощью команды /start',
            reply_markup=kb.back
        )
        return
    profile_text = get_profile_text(user)

    await message.answer(
        text=profile_text,
        parse_mode="Markdown",
        reply_markup=kb.profile
    )

@router.callback_query(F.data == 'profile')
async def profile_handler(callback: CallbackQuery):
    user = await requests.get_user(callback.from_user.id)

    if user is None:
        await callback.message.edit_text(
            text='Ошибка, пользователь не найден\nПопробуйте перезапустить бота с помощью команды /start',
            reply_markup=kb.back
        )
        return
    profile_text = get_profile_text(user)

    await callback.message.edit_text(
        text=profile_text,
        parse_mode="Markdown",
        reply_markup=kb.profile
    )

@router.callback_query(F.data == 'update_data')
async def update_data_handler(callback: CallbackQuery):
    user = await requests.get_user(callback.from_user.id)
    if user is None:
        await callback.answer("❌ Пользователь не найден. Попробуйте перезапустить бота с помощью команды /start.")
        return

    try:
        await requests.update_user(
            tg_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
        )

        updated_user = await requests.get_user(callback.from_user.id)
        if updated_user is None:
            await callback.answer("❌ Не удалось получить обновленные данные.")
            return

        profile_text = get_profile_text(updated_user)

        try:
            await callback.message.edit_text(
                text=profile_text,
                parse_mode="Markdown",
                reply_markup=kb.profile
            )
            await callback.answer("✅ Ваши данные успешно обновлены.")

        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                await callback.answer("ℹ️ Ваши данные уже актуальны.")
            else:
                await callback.answer("❌ Ошибка: сообщение слишком длинное.")
        else:
            await callback.answer(f"❌ Ошибка при обновлении")
    except Exception as e:
        await callback.answer(f"❌ Не удалось обновить данные: {str(e)}")

    await asyncio.sleep(0.5)

@router.callback_query(F.data == 'credits')
async def credits_handler(callback: CallbackQuery, state: FSMContext):
    sent_message = await callback.message.edit_text(
        'Выберите сумму для пополнения 💸',
        reply_markup=kb.credits
    )
    # Сохраняем message_id в состоянии
    await state.set_state(BuyingState.waiting_for_transaction)
    # Сохраняем message_id
    await state.update_data(message_id=sent_message.message_id)

@router.callback_query(F.data == 'back')
async def back_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='🏠 Вы на главной странице. Чем могу помочь?', reply_markup=kb.main)
    await state.clear()

@router.callback_query(F.data == 'settings')
async def settings_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='⚙️ Конфигурация и настройки ⚙️', reply_markup=kb.settings)

@router.callback_query(F.data == 'back_to_settings')
async def back_to_settings_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='⚙️ Конфигурация и настройки ⚙️', reply_markup=kb.settings)

@router.callback_query(F.data == 'image_style')
async def image_style_handler(callback: CallbackQuery):
    user = await requests.get_user(callback.from_user.id)
    styles_keyboard = await get_styles_keyboard(user.telegram_id)
    await callback.message.edit_text(
        text=(
            '🎨 *Выбери стиль* для генерации изображения.\n\n'
            '💡 Стиль и размер изображения будут влиять на стоимость.\n'
            '💵 Убедись, что у тебя достаточно кредитов для выбранного варианта.'
        ),
        reply_markup=styles_keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == 'image_quality')
async def image_quality_handler(callback: CallbackQuery):
    user = await requests.get_user(callback.from_user.id)
    quality_keyboard = await get_quality_keyboard(user.telegram_id)
    await callback.message.edit_text(text='Выбери качество изображения:', reply_markup=quality_keyboard)

@router.callback_query(F.data.startswith('style_'))
async def set_style(callback: CallbackQuery):
    """Обрабатывает выбор стиля и обновляет клавиатуру."""
    new_style = callback.data.replace("style_", "", 1)
    await requests.update_user_style(callback.from_user.id, new_style)
    new_keyboard = await get_styles_keyboard(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)

@router.callback_query(F.data.startswith('size_'))
async def size_callback_handler(callback: CallbackQuery):
    new_size = callback.data.split("_")[1]
    await update_user_size(callback.from_user.id, new_size)
    new_keyboard = await get_quality_keyboard(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)

@router.callback_query(F.data == 'gallery')
async def gallery_handler(callback: CallbackQuery):
    await show_gallery(callback.message, callback.from_user.id)

async def show_gallery(message: types.Message, user_id: int, offset: int = 0):
    loading_message = await message.answer("⏳ Идёт запрос в базу данных, подождите...")
    # Получение изображения пользователя
    async with async_session() as session:
        '''Получение первичного ключа'''
        user_id_db = await get_user_db_id(session, user_id)

        if user_id_db is None:
            await loading_message.edit_text('❌ Пользователь не найден.')
            return

        gallery_items = await session.execute(
            select(Gallery)
            .where(Gallery.user_id == user_id_db)
            .order_by(Gallery.created_at.desc())
            .limit(10)
            .offset(offset)
        )
        gallery_items = gallery_items.scalars().all()


    if gallery_items:
        media_group = MediaGroupBuilder()

        for item in gallery_items:
            caption = f"Промт: {item.prompt or 'Без описания'}\n📅 {item.created_at.strftime('%d %m %Y %H:%M:%S')}"
            try:
                media_group.add(type="photo", media=item.image_url, caption=caption)
            except Exception as e:
                await loading_message.edit_text("❌ Ошибка при загрузке изображения.")

        await message.answer_media_group(media_group.build())
        await loading_message.edit_text("Галерея загружена!")

        total_images = await session.scalar(
            select(func.count(Gallery.id)).where(Gallery.user_id == user_id_db)
        )
        next_offset = offset + 10
        if next_offset < total_images:
            _reply_markup = get_next_page_keyboard(next_offset)
            _text = "📷 Вы просмотрели 10 изображений. Хотите увидеть больше?"
            await message.answer(text=_text, reply_markup=_reply_markup)
        else:
            _text = "Вы просмотрели все изображения"
            await message.answer(text=_text, reply_markup=back)
    else:
        await loading_message.edit_text("Ваша галерея пуста.", reply_markup=back)

@router.callback_query(F.data.startswith('more_images_'))
async def load_more_images(callback: CallbackQuery):
    loading_message = await callback.message.answer("⏳ Идёт запрос в базу данных, подождите...")
    offset = int(callback.data.split('_')[-1])

    async with (async_session() as session):
        user_id_db = await get_user_db_id(session, callback.from_user.id)
        if user_id_db is None:
            await loading_message.edit_text('❌ Пользователь не найден.')
            return

        gallery_items = await session.execute(
            select(Gallery)
            .where(Gallery.user_id == user_id_db)
            .order_by(Gallery.created_at.desc())
            .limit(8)
            .offset(offset)
        )
        gallery_items = gallery_items.scalars().all()

        if gallery_items:
            media_group = MediaGroupBuilder()

            for index, item in enumerate(gallery_items):
                image_url = item.image_url
                if not image_url.startswith('http'):
                    await loading_message.edit_text("❌ Недопустимый URL у изображения.")
                    return
                try:
                    caption = f"Ваш промт: {item.prompt or 'Без описания'}\n📅 {item.created_at.strftime('%d %m %Y %H:%M:%S')}"
                    media_group.add(type="photo", media=image_url, caption=caption)
                except Exception as e:
                    await loading_message.edit_text("❌ Ошибка при загрузке изображения.")

            await callback.message.answer_media_group(media_group.build())
            await loading_message.edit_text("Данные загружены!")

            total_images = await session.scalar(
                select(func.count(Gallery.id)).where(Gallery.user_id == user_id_db)
            )

            next_offset = offset + 8

            if next_offset < total_images:
                _reply_markup = get_next_page_keyboard(next_offset)
                _text = "📷 Есть ещё изображения. Хотите продолжить?"
                await callback.message.answer(text=_text, reply_markup=_reply_markup)
            else:
                _text = "Вы просмотрели все изображения"
                await callback.message.answer(text=_text, reply_markup=back)
        else:
            await loading_message.edit_text("❌ Нет изображений для отображения.")


@router.callback_query(F.data == 'back_to_payment')
async def back_to_payment(callback: CallbackQuery, state: FSMContext):
    sent_message = await callback.message.edit_text(
        'Выберите сумму для пополнения 💸',
        reply_markup=kb.credits
    )

    await state.set_state(BuyingState.waiting_for_transaction)
    await state.update_data(message_id=sent_message.message_id)

@router.callback_query(F.data.startswith('credits_'))
async def buying_credits(callback: CallbackQuery, state: FSMContext):
    '''Удаление предыдущего сообщения'''
    user_data = await state.get_data()
    previous_message_id = user_data.get("message_id")

    # Если предыдущее сообщение существует, удаляем его
    if previous_message_id:
        await callback.message.bot.delete_message(chat_id=callback.message.chat.id, message_id=previous_message_id)

    loading_message = await callback.message.answer("⏳ Идёт подготовка ссылки для оплаты, подождите...")
    try:
        data = callback.data.split('_')[1]
        credits_amount, price = map(int, data.split(':'))

    except (IndexError, ValueError):
        await callback.message.answer("Ошибка обработки данных. Попробуйте ещё раз.")

    order_id, payment_url = generate_payment_link(callback.from_user.id, price)

    payment_keyboard = get_payment_keyboard(payment_url, order_id, price)

    async with async_session() as session:
        user_db_id = await get_user_db_id(session, callback.from_user.id)

        await create_transaction(session, user_db_id, price, order_id,
                                 "recharge", "pending", credits_amount)

    await state.update_data(message_id=loading_message.message_id)

    await loading_message.edit_text(f'Пополнение баланса на сумму {price}₽\nВ зависимости от способа оплаты может взиматься комиссия',
                                    reply_markup=payment_keyboard)


@router.callback_query(lambda c: c.data.startswith('check_payment'))
async def check_payment(callback: CallbackQuery, state: FSMContext):
    checking_message = await callback.message.answer("⏳ Идёт проверка, ожидайте...")
    data = callback.data.split(':')[-1]
    order_id, price = data.split('_')

    payload = {"order_id": order_id}

    async with aiohttp.ClientSession() as session:
        message = "❌ Ошибка проверки платежа. Попробуйте позже."
        try:
            async with session.get(f"{DJANGO_API_URL}", params=payload) as response:
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('application/json'):
                    return await checking_message.edit_text("❌ Некорректный ответ сервера. Попробуйте позже.")

                data = await response.json()

                if response.status != 200:
                    return await checking_message.edit_text(f"❌ Ошибка: {data.get('message', 'Неизвестная ошибка')}")

        except aiohttp.ClientError as e:
            return await checking_message.edit_text(f"❌ Ошибка сети: {e}")

    status = data.get("status")
    transaction_status = data.get("transaction_status")

    if status == "success" and transaction_status == "paid":
        async with async_session() as session:
            user_id_db = await get_user_db_id(session, callback.from_user.id)
            transaction = await get_transaction_by_order_id(session, order_id)

            if transaction:
                if transaction.credits_added:
                    message = "✅ Оплата уже была подтверждена ранее."
                else:
                    try:
                        await add_credits(session, user_id_db, transaction.credits_amount)
                        transaction.credits_added = True
                        await session.commit()

                        state_data = await state.get_data()
                        message_id = state_data.get('message_id')

                        if message_id:
                            await callback.message.bot.delete_message(callback.message.chat.id, message_id)
                        message = f"✅ Оплата подтверждена! Ваш баланс пополнен на {transaction.credits_amount} кредитов."
                    except Exception as e:
                        message = "❗Ошибка начисления кредитов, обратитесь в поддержку (команда /support)."


            elif transaction and transaction.transaction_status == "paid":
                message = "✅ Оплата уже была подтверждена ранее."
            else:
                message = "❌ Транзакция не найдена. Обратитесь в поддержку (команда /support)."
    elif status == "pending":
        message = "⏳ Оплата еще не прошла, попробуйте позже."

    await checking_message.edit_text(message)




