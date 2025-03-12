import os

import aiohttp
from dotenv import load_dotenv

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.database.models import User
from apps.database.requests import get_current_credit_balance, get_session, spend_credits
from apps.database.models import Gallery

load_dotenv('.env')

API_URL = 'https://api.gen-api.ru/api/v1/networks/flux'

MODEL_COSTS = {
    "schnell": 0.5,
    "dev": 4.5,
    "realism": 6.5,
    "pro": 9,
    "ultra": 13,
    "inpainting": 13.5,
}

MODEL_MULTIPLIERS = {
    "schnell": 8,
    "dev": 6.5,
    "realism": 5.5,
    "pro": 4.8,
    "ultra": 4.2,
    "inpainting": 3.9,
}

SIZE_COSTS = {
    "512x512": 1.0,
    "1024x1024": 2,
    "1536x1536": 3,
}

async def get_user_db_id(session: AsyncSession, user_id: int) -> int | None:
    user = await session.execute(
        select(User.id).where(User.telegram_id == user_id)
    )
    return  user.scalar()


async def save_image_do_db(session: AsyncSession, user_id: int, image_url: str) -> None:
    user_id_db: int = await get_user_db_id(session, user_id)

    if user_id_db is None:
        return

    new_image = Gallery(user_id=user_id_db, image_url=image_url)
    session.add(new_image)
    await session.commit()

async def calculate_total_price(model: str, size: str) -> int | None:
    """ Высчитывает итоговый ценник по формуле """
    if model not in MODEL_COSTS or model not in MODEL_MULTIPLIERS:
        return None
    if size not in SIZE_COSTS:
        return None
    base_cost = MODEL_COSTS[model]
    multiplier = MODEL_MULTIPLIERS[model]
    size_factor = SIZE_COSTS[size]

    discount = max(0.85, 1 - 0.03 * base_cost)
    total = base_cost * multiplier * size_factor * discount

    return int(total)

async def generate_image(prompt: str, model: str, size: str, user_id: int) -> str | None:
    """
    Отправляет запрос к API генерации изображений.
    Возвращает путь к загруженному изображению или None в случае ошибки.
    """
    total_cost = await calculate_total_price(model, size)
    if total_cost is None:
        return None

    session = await get_session()
    async with session:
        current_balance = await get_current_credit_balance(session, user_id)
        if current_balance is None or current_balance < total_cost:
            return "insufficient_credits"

    width, height = size.split('x')

    headers = {
        "Authorization": f"Bearer {os.getenv('GEN_API_KEY')}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "prompt": prompt,
        "model": model,
        "width": width,
        "height": height,
        "is_sync": True,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, headers=headers) as response:
                content_type = response.headers.get('Content-Type', '')

                if response.status == 200 and content_type.startswith('application/json'):
                    data = await response.json()

                    image_list = data.get('images', [])
                    if not image_list:
                        return None
                    image_url = image_list[0]

                    async with await get_session() as db_session:
                        print(image_url)
                        if not await spend_credits(db_session, user_id, total_cost):
                            return "write_off_error"
                        await save_image_do_db(db_session, user_id, image_url)
                    return image_url

                else:
                    error_text = await response.text()
    except Exception as e:
        return None
    # return 'https://images.app.goo.gl/8fEufZSQ2XnmTLVr7'

