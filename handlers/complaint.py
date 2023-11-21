from aiogram import types
from peewee import *


from keyboards import *
from models import *


async def comp(message: types.Message, last_user):
    user = Users.get(Users.id == message.from_user.id)
    intruder = Users.get(Users.id == last_user)

    comp = Complaint.create(user=user.id, intruder=intruder.id, message=message.text)
    comp.save()
    await message.answer(text="<b>Жалоба успешно добавлена.</b>", parse_mode="HTML", reply_markup=my_profile)