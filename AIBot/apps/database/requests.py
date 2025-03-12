from datetime import datetime

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from apps.database.database import async_session
from apps.database.models import User, UserSettings, TokenTransaction, Transaction
from sqlalchemy import select, update
import pytz

moscow_tz = pytz.timezone('Europe/Moscow')

async def get_current_credit_balance(session: AsyncSession, user_id: int) -> int | None:
    res = await session.execute(select(User.credits).where(User.id == user_id))
    return res.scalar_one_or_none()

async def get_transaction_by_order_id(session: AsyncSession, order_id: str) -> Transaction | None:
    result = await session.execute(
        select(Transaction).where(Transaction.order_id == order_id)
    )
    return result.scalar_one_or_none()

async def spend_credits(session: AsyncSession, user_id: int, amount: int) -> bool:
    current_balance = await get_current_credit_balance(session, user_id)
    if current_balance is None:
        print(f"Ошибка: пользователь {user_id} не найден или кредиты отсутствуют.")
        return False
    if current_balance < amount:
        return False
    try:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(credits=current_balance - amount)
        )
        new_transaction = TokenTransaction(
            user_id=user_id,
            amount=-amount,
            transaction_date=datetime.now(moscow_tz).replace(tzinfo=None),
            transaction_type="spend_tokens",
        )
        session.add(new_transaction)
        await session.commit()
        return True
    except Exception as e:
        await session.rollback()
        print(f"Ошибка при списании кредитов: {e}")
        return False

async def get_user_db_id(session: AsyncSession, user_id: int) -> int | None:
    user = await session.execute(
        select(User.id).where(User.telegram_id == user_id)
    )
    return user.scalar()

async def add_credits(session: AsyncSession, user_id: int, amount: int) -> bool:
    current_balance = await get_current_credit_balance(session, user_id)
    try:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(credits=current_balance + amount)
        )
        new_transaction = TokenTransaction(
            user_id=user_id,
            amount=+amount,
            transaction_date=datetime.now(moscow_tz).replace(tzinfo=None),
            transaction_type="earn_tokens",
        )
        session.add(new_transaction)
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        return False

async def set_user(tg_id, username: str = None, first_name: str = None) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))

        if not user:
            new_user = User(
                telegram_id=tg_id,
                username=username,
                first_name=first_name,
                credits=50,
            )
            session.add(new_user)
            await session.flush()

            new_settings = UserSettings(user_id=new_user.id)
            session.add(new_settings)

            await session.commit()

async def update_user(tg_id: int, username: str = None, first_name: str = None) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if not user:
            raise ValueError(f"Пользователь с telegram_id {tg_id} не найден")

        if username is not None:
            user.username = username
        if first_name is not None:
            user.first_name = first_name

        await session.commit()

async def get_user(telegram_id: int) -> User | None:
    async with async_session() as session:
        return await session.scalar(
            select(User).options(joinedload(User.settings)).where(User.telegram_id == telegram_id)
        )

async def get_user_with_settings(session: AsyncSession, tg_id: int) -> User | None:
    return await session.scalar(
        select(User).options(joinedload(User.settings)).where(User.telegram_id == tg_id)
    )

async def create_transaction(session: AsyncSession, user_id: int, amount: int, order_id: str,
                             transaction_type: str = "recharge",
                             transaction_status: str = "pending", credits_amount: int = 0):
    """Создаёт запись о транзакции в базе данных."""
    transaction = Transaction(user_id=user_id, amount=amount, order_id=order_id, transaction_type=transaction_type,
                              transaction_status=transaction_status, credits_amount=credits_amount)
    session.add(transaction)
    await session.commit()
    return transaction


async def get_session() -> AsyncSession:
    async with async_session() as session:
        return session

#Вынести в отдельную функцию
async def get_or_create_user_settings(session, tg_id: int, field: str, value: str):
    """Получает настройки пользователя или создает новые."""
    user = await session.scalar(select(User).where(User.telegram_id == tg_id))
    if not user:
        raise ValueError(f'Пользователь с telegram_id {tg_id} - не найден')

    settings = await session.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    if not settings:
        settings = UserSettings(user_id=user.id, **{field: value})
        session.add(settings)
    else:
        setattr(settings, field, value)

    return settings

async def update_user_style(tg_id: int, new_style: str = None) -> None:
    async with async_session() as session:
        await get_or_create_user_settings(session, tg_id, 'selected_style', new_style)
        await session.commit()


async def check_payment_status(order_id: str) -> dict:
    url = f"https://your-server.com/check_payment/{order_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {"status": "error", "message": "Failed to retrieve payment status"}

async def update_user_size(tg_id: int, new_size: str = None) -> None:
    async with async_session() as session:
        await get_or_create_user_settings(session, tg_id, 'image_size', new_size)
        await session.commit()
