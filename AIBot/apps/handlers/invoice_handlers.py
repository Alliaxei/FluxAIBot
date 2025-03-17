import uuid

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message

from apps.database.database import async_session
from apps.database.requests import add_credits, get_user_db_id, get_transaction_by_order_id, create_transaction
from apps.keyboards.keyboards import back_to_payment_stars

router = Router()
CURRENCY = "XTR"

@router.callback_query(F.data.startswith("stars_credits_"))
async def buy_with_stars(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    if len(data_parts) >= 4:
        credits = data_parts[2]
        stars = data_parts[3]
    else:
        await callback.message.answer('Произошла непредвиденная ошибка, повторите попытку позже.')
        return

    order_id = str(uuid.uuid4())


    '''Удаление предыдущего сообщения'''
    user_data = await state.get_data()
    previous_message_id = user_data.get("message_id")
    # Если предыдущее сообщение существует, удаляем его
    if previous_message_id:
        await callback.message.bot.delete_message(chat_id=callback.message.chat.id, message_id=previous_message_id)


    prices = [LabeledPrice(label=CURRENCY, amount=int(stars))]
    await callback.message.answer_invoice(
        title='Пополнение баланса',
        description=f'Пополнение баланса на {credits} кредитов',
        prices=prices,
        provider_token='',
        currency=CURRENCY,
        payload=f'{credits}_{order_id}',
    )
    async with async_session() as session:
        user_db_id = await get_user_db_id(session, callback.from_user.id)
        try:
            await create_transaction(session, user_db_id, None, order_id, "recharge",
                                 "pending", int(credits), stars_amount=int(stars))
            await session.commit()
        except:
            session.rollback()
            await callback.message.answer('Произошла непредвиденная ошибка, попробуйте оплатить позже.')
    await callback.message.answer("Вернуться к выбору пополнения", reply_markup=back_to_payment_stars)

@router.message(F.successful_payment)
async def successful_payment(message: Message):
    '''Логика для зачисления кредитов пользователю'''
    payload = message.successful_payment.invoice_payload
    credits, order_id = payload.split("_")

    credits_amount = int(credits)

    await message.answer('Идёт зачисление кредитов вам на счёт.')
    try:
        async with async_session() as session:
            user_id_db = await get_user_db_id(session, message.from_user.id)
            transaction = await get_transaction_by_order_id(session, order_id)
            if transaction.transaction_status == "paid":
                await message.answer(f'Платёж с order_id {order_id} уже был успешно завершён.')
                return
            await add_credits(session, user_id_db, credits_amount)
            transaction.credits_added = True
            transaction.transaction_status = "paid"
            await session.commit()
    except:
        session.rollback()
        await message.answer('Произошла ошибка при пополнении баланса, обратитесь в техподдержку /support')
        return
    await message.edit_text(f'Платёж успешно завершён, {credits_amount} поступило на ваш счёт.')
