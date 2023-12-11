from peewee import *
from aiogram import types


from models import *
from keyboards import my_profile


async def sup(message: types.Message, user_id):
    user = Users.get(Users.id == user_id)
    support = Support.create(user=user.id, text=message.text)
    support.save()

    await message.answer(text="Обращение отправлено!", reply_markup=my_profile)