from aiogram.dispatcher.filters.state import StatesGroup, State


class ProfileStatesGroup(StatesGroup):
    name = State()
    sex = State()
    age = State()
    inf = State()
    photo = State()
    choice = State()
    complaint = State()
    support = State()