import os
from dotenv import load_dotenv

from aiogram import Router, types

from aiogram.fsm.context import FSMContext

from apps.database.models import Gallery
from apps.database.requests import get_user_with_settings, get_session
from apps.keyboards import keyboards as kb
from apps.services.image_generattion import generate_image
from apps.states import ImageState

router = Router()
load_dotenv('.env')

GEN_API_KEY = os.getenv('GEN_API_KEY')

@router.message(ImageState.waiting_for_prompt)
async def process_prompt(message: types.Message, state: FSMContext):
    session = await get_session()
    user = await get_user_with_settings(session, message.from_user.id)

    # Проверка промта на валидность
    prompt_text = message.text.strip()

    if not prompt_text or len(prompt_text) <= 2:
        await message.answer("❌ Введено слишком короткое описание. Пожалуйста, введите более длинный промт.")
        return
    if user and user.settings:
        model = user.settings.selected_style
        size = user.settings.image_size

        processing_message = await message.answer("⏳ Изображение генерируется, подождите...")
        image_url = await generate_image(
            prompt = message.text,
            model = model,
            size = size,
            user_id = user.id
        )
        if image_url == 'write_off_error':
            await processing_message.edit_text("❌ Произошла ошибка при списании кредитов. Попробуйте снова.")
            return
        if image_url == 'insufficient_credits':
            await processing_message.edit_text(
                f"❌ **У вас недостаточно кредитов для генерации изображения.**\n"
                f"🔴 *Количество ваших кредитов*: {user.credits}\n\n"
                f"💳 Пополните баланс, чтобы продолжить!"
                , parse_mode="Markdown", reply_markup=kb.back
            )

            return
        if image_url:
            await processing_message.edit_text("✔️ Изображение успешно сгенерировано!")
            await message.answer_photo(image_url, caption=f"Ваша генерация!")
            new_gallery_item = Gallery(
                user_id=user.id,
                image_url=image_url,
                prompt=message.text,
            )

            if not session.in_transaction():
                async with session.begin():
                    session.add(new_gallery_item)
                await session.commit()
            else:
                session.add(new_gallery_item)

            await session.commit()
        else:
            await processing_message.edit_text("❌ Произошла ошибка при генерации изображения. Попробуйте снова.")
    else:
        await message.answer("❌ Не удалось загрузить настройки пользователя. Попробуйте снова.")

    await session.close()
    await state.clear()
    await message.answer(text="Хотите создать ещё?", reply_markup=kb.generate_new_image)