from aiogram.fsm.state import StatesGroup, State

class ImageState(StatesGroup):
    waiting_for_prompt = State()

class BuyingState(StatesGroup):
    waiting_for_transaction = State()