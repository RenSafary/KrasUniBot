from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from models import *
import emoji

university = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

db.connect()
universities = University.select()
for i in universities:
    university.add(KeyboardButton(text=i.university))
db.close()

sex = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
sex.add(KeyboardButton(text=emoji.emojize(":man:"), callback_data="name"))
sex.add(KeyboardButton(text=emoji.emojize(":woman:")))

another_user_sex = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
another_user_sex.add(
    KeyboardButton(text="Парни"),
    KeyboardButton(text="Девушки"),
    KeyboardButton(text="Всё равно")
)


edit_form = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
edit_form.add(
    KeyboardButton(text="1"),#заново
    KeyboardButton(text="2") #фото
)
edit_form.add(
    KeyboardButton("3"), #текст анкеты
    KeyboardButton("4") #Продолжить поиск
)

my_profile = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
my_profile.add(KeyboardButton(text="/myprofile"))

like_dislike = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
like_dislike.add(
    KeyboardButton(text=emoji.emojize(":thumbs_down:")),
    KeyboardButton(text=emoji.emojize(":red_heart:"))
)
like_dislike.add(
    KeyboardButton(text=emoji.emojize(":warning:")),
    KeyboardButton(text=emoji.emojize(":love_letter:"))
)


count_users = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
count_users.add(KeyboardButton(text="Кол-во пользователей"))