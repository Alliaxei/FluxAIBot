from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apps.database import requests
from apps.services.image_generattion import calculate_total_price

main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🎨 Создать изображение', callback_data='generate_image')],
    [InlineKeyboardButton(text='👤 Личный кабинет', callback_data='profile'),
    InlineKeyboardButton(text='💳 Купить кредиты', callback_data='credits')],
    [InlineKeyboardButton(text='⚙️ Настройки', callback_data='settings'),
     InlineKeyboardButton(text='🖼️ Галерея', callback_data='gallery')]
])

generate_new_image = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🎨 Создать ещё одно изображение', callback_data='generate_image')],
    [InlineKeyboardButton(text='⬅️ Вернуться на главную', callback_data='back')],
])

credits = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💡 Пробный 25кр — 49₽', callback_data='credits_25:49')],
    [InlineKeyboardButton(text='💳 60 кредитов — 199₽ (-18%)', callback_data='credits_60:199')],
    [InlineKeyboardButton(text='💳 150 кредитов — 399₽ (-32%)', callback_data='credits_150:399')],
    [InlineKeyboardButton(text='💳 500 кредитов — 1190₽ (-40%)', callback_data='credits_500:1190')],
    [InlineKeyboardButton(text='💳 1200 кредитов — 2490₽ (-48%)', callback_data='credits_1200:2490')],
    [InlineKeyboardButton(text='🔥 3000 кредитов — 5490₽ (-54%)', callback_data='credits_3000:5490')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back')]
])

settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Стиль изображений', callback_data='image_style')],
    [InlineKeyboardButton(text='Качество изображений', callback_data='image_quality')],
    [InlineKeyboardButton(text='⬅️ Вернуться в меню', callback_data='back')],
])

profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔄 Обновить данные', callback_data='update_data')],
    [InlineKeyboardButton(text='⬅️ Вернуться в меню', callback_data='back')],
])

back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back')],
])

def add_checkmark_to_button(name, _callback_data, selected_value):
    """Добавляет галочку к кнопке, если она выбрана."""
    return f'✅ {name}' if _callback_data == selected_value else name

async def get_styles_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру с отметкой текущего выбранного стиля."""
    user = await requests.get_user(user_id)
    selected_style = user.settings.selected_style if user.settings else None
    selected_size = user.settings.image_size if user.settings else "512x512"
    _styles = [
        ("Schnell", "style_schnell"),
        ("Dev", "style_dev"),
        ("Realism", "style_realism"),
        ("PRO", "style_pro"),
        ("Ultra", "style_ultra"),
        ("Inpainting", "style_inpainting"),
    ]
    buttons = []
    for name, cb_data in _styles:
        model_key = name.lower()

        cost = await calculate_total_price(model_key, selected_size)
        cost_text = f'{cost} кредит.'  if cost is not None else "N/A"
        button_text = add_checkmark_to_button(f"{name} - {cost_text}", cb_data, f"style_{selected_style}")
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=cb_data)])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_settings")])
    return keyboard

async def get_quality_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру с отметкой текущего выбранного разрешения."""
    user = await requests.get_user(user_id)
    selected_size = user.settings.image_size if user.settings else "512x512"
    _sizes = [
        ("512x512", "size_512x512"),
        ("1024x1024", "size_1024x1024"),
        ("1536x1536", "size_1536x1536")
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=add_checkmark_to_button(name, cb_data, f'size_{selected_size}'),
                                  callback_data=cb_data)]
            for name, cb_data in _sizes
        ]
    )
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_settings")])
    return keyboard

def get_next_page_keyboard(offset: int) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру с кнопкой "Далее" для подгрузки изображений.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back'),
        InlineKeyboardButton(text="▶️ Продолжить", callback_data=f"more_images_{offset}")]
    ])

def get_payment_keyboard(url: str, order_id: int, amount: int) -> InlineKeyboardMarkup:
    payment = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 Оплатить', url=url)],
        [InlineKeyboardButton(text='🔄 Проверить', callback_data=f"check_payment:{order_id}_{amount}")],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_payment')],
    ])
    return payment