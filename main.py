from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import InputFile, ContentType
from peewee import *
import io
import emoji
import asyncio
from datetime import *

from keyboards import *
from models import *
from handlers.complaint import comp
from handlers.registration import us_name, us_age, us_sex, us_inf, sk_uni, ch_uni, ch_fac, ch_dir, ch_cour, ch_us_sex, ph
from handlers.support import sup
from ProfileStatesGroup import *


TOKEN_API = "6748179824:AAFqobdbDqdYVzuMZLLFWY9RbAeADeAO610"

bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=MemoryStorage())


user_step = {}
selected_university = ""
selected_faculty = ""
selected_direction = ""
selected_course = ""

#___ ___ ___ ___ ___ ___ ___
fav_selected_university = ""
fav_selected_faculty = ""
fav_selected_direction = ""
fav_selected_course = ""

#___ ___ ___ ___ ___ ___ ___ 
user_id = None

db.connect()
@dp.message_handler(commands=['myprofile', 'start'])
async def profile(message: types.Message):
    global user_id

    user_id = message.from_user.id
    user_exists = Users.select().where((Users.id == user_id) & (Users.fav_university.is_null(False))).exists()
    if user_exists:
        asyncio.create_task(send_notification(user_id))
        asyncio.create_task(delete_watched_and_liked_forms())

        user = Users.get(Users.id == message.from_user.id)
        university = University.get(University.id == user.university)

        faculty = Faculty.select().where((Faculty.id == user.faculty) & (Faculty.university_id == university.id)).exists()
        faculty = Faculty.get((Faculty.id == user.faculty) & (Faculty.university_id == university.id))
        direction = Direction.get((Direction.id == user.direction) & (Direction.faculty_id == faculty.id))
        course = Course.get((Course.id == user.course) & (Course.direction_id == direction.id))
        photo = user.photo
        input_file = InputFile(io.BytesIO(photo), filename="user_photo.jpg")
        if user.information != None:
            form = f"{user.name}, {user.age}\n{university.university} - {faculty.faculty} - {direction.direction} - {course.course} курс\n\n{user.information}"
        else:
            form = f"{user.name}, {user.age}\n{university.university} - {faculty.faculty} - {direction.direction} - {course.course} курс"
        await bot.send_photo(chat_id=message.from_user.id, photo=input_file, caption=form)        

        text = "1. Заполнить анкету заново " + emoji.emojize(":writing_hand:") + "\n2. Изменить фото " + emoji.emojize(":sunglasses:") + "\n3. Изменить текст анкеты " + emoji.emojize(":pencil:") + "\n4. Смотреть анкеты " + emoji.emojize(":red_heart:")
        await message.answer(text=text, reply_markup=edit_form)
        user_step[user_id] = "choice"
        await ProfileStatesGroup.choice.set()
    else:
        await message.answer(text="Нужно заполнить анкету" + emoji.emojize(":bust_in_silhouette:") + "\nВведите ваше имя:")
        user_step[user_id] = "name"
        await ProfileStatesGroup.name.set()

async def send_notification(user_id):
    while True:
        if user_id is not None:
            liked_user = Liked_Users.select().where((Liked_Users.liked_id == user_id) & (Liked_Users.watched == False)).exists()
            if liked_user:
                await bot.send_message(chat_id=user_id, text="Вами кто-то заинтересовался! <b>/notifications</b>", parse_mode='HTML')
                await bot.send_sticker(user_id, sticker="CAACAgIAAxkBAAJmwmV2_yoeM5djzCP_Rg1ssho3ZPrHAAJtJQAC9LgoSjiBlNxAD-u8MwQ")
                Liked_Users.update(watched=True).where(Liked_Users.liked_id == user_id).execute()
        await asyncio.sleep(5)

async def delete_watched_and_liked_forms():
    while True:
        today = datetime.now().date()
        two_days = timedelta(days=2)
        d = today-two_days
        l_user = Liked_Users.select().where(Liked_Users.date == d).exists()
        w_user = Watched_Users.select().where(Watched_Users.date == d).exists()
        if l_user:
            Liked_Users.delete().where(Liked_Users.date == d).execute()
        if w_user:    
            Watched_Users.delete().where(Watched_Users.date == d).execute()
        await asyncio.sleep(5)


k = 1
@dp.message_handler(lambda message: user_step.get(message.from_user.id) == 'choice', state=ProfileStatesGroup.choice)
async def choice(message: types.Message, state: FSMContext):
    if message.text == "/myprofile": await profile(message)

    if message.text == "/notifications": await notifications(message)

    if message.text == "/support": await support(message)
    else:
        global k

        async with state.proxy() as data:
            data['choice'] = message.text
            if data['choice'] == "1":
                name = Users.get(Users.id == message.from_user.id)
                your_name = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                your_name.add(KeyboardButton(text=name.name))

                await message.answer("Введи своё имя:", reply_markup=your_name)
                user_step[message.from_user.id] = "name"
                await ProfileStatesGroup.name.set()
            if data['choice'] == "2":
                await message.answer("Отправь своё фото..")
                user_step[message.from_user.id] = "photo"
                k = 2
                await ProfileStatesGroup.photo.set()
            if data['choice'] == "3":
                await message.answer("Напиши что-нибудь о себе:")
                user_step[message.from_user.id] = "inf"
                k = 3
                await ProfileStatesGroup.inf.set()
            if data['choice'] == "4":
                user = Users.select().where(Users.fav_course.is_null(False)).exists()

                search = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                search.add(
                    KeyboardButton(text="Глобальный поиск"),
                    KeyboardButton(text="Поиск по университету")
                )
                if user:
                    search.add(KeyboardButton(text="Поиск по предпочтениям"))
                    await message.answer("1. Глобальный поиск\n2. Поиск по университету\n3. Поиск по предпочтениям", reply_markup=search)
                else:
                    await message.answer("1. Глобальный поиск\n2. Поиск по университету", reply_markup=search)

                user_step[message.from_user.id] = "search"
                await ProfileStatesGroup.choice.set()


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "name", state=ProfileStatesGroup.name)
async def user_name(message: types.Message, state: FSMContext):
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/support":
        pass
    else:
        async with state.proxy() as data:
            data['name'] = message.text
            await us_name(message)
            user_step[message.from_user.id] = "age"
            await ProfileStatesGroup.age.set()


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "age", state=ProfileStatesGroup.age)
async def user_age(message: types.Message, state: FSMContext):
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    elif message.text == "/support": await message.answer("Нельзя оставить обращение во время создания анкеты.")
    else:
        async with state.proxy() as data:
            data['age'] = message.text

            try:
                if (26 >= int(message.text) >= 16):
                        await us_age(message)

                        user_step[message.from_user.id] = "sex"
                        await ProfileStatesGroup.sex.set()
                else:
                    await message.answer(text='Извините, но вы не должны быть младше 16 и старше 26 лет.\nПопробуйте ещё раз:')
                    await ProfileStatesGroup.age.set()
            except:
                await message.answer(text='Возраст введён неверно..\nПопробуйте ещё раз:')


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "sex", state=ProfileStatesGroup.sex)
async def user_sex(message: types.Message, state: FSMContext):
    global k
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    elif message.text == "/support": await message.answer("Нельзя оставить обращение во время создания анкеты.")
    else:
        async with state.proxy() as data:
            data['sex'] = message.text
            i = 0
            i = await us_sex(message, i)
            if i == 0:
                await ProfileStatesGroup.sex.set() 
            if i == 1:
                user_step[message.from_user.id] = "inf"
                await ProfileStatesGroup.inf.set()
            k = i


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "inf", state=ProfileStatesGroup.inf)
async def user_inf(message: types.Message, state: FSMContext):
    global k
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    elif message.text == "/support": await message.answer("Нельзя оставить обращение во время создания анкеты.")
    else:
        async with state.proxy() as data:
            data['inf'] = message.text
            i = k

            k = await us_inf(message, i)
            if k == 3: await state.finish()
            else:
                user_step[message.from_user.id] = "photo"
                await ProfileStatesGroup.photo.set()
                await bot.send_sticker(message.from_user.id, sticker="CAACAgIAAxkBAAJmwGV2_pqEwnIwZbRG48BJSVCbVATkAAJfEwACLl7IS9mrvzBghJYzMwQ")
            

@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "photo", state=ProfileStatesGroup.photo, content_types=ContentType.PHOTO)
async def user_photo(message: types.Message, state: FSMContext):
    global k
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    elif message.text == "/support": await message.answer("Нельзя оставить обращение во время создания анкеты.")
    else:
        async with state.proxy() as data:
            if message.content_type == "photo":
                user_step[message.from_user.id] = None
                await state.finish()

                photo_binary = io.BytesIO()
                await message.photo[-1].download(photo_binary)
                data['photo'] = photo_binary.getvalue()
                photo = data['photo']

                j = k
                k = await ph(message, photo, j)

                if k == 1: user_step[message.from_user.id] = "university"
                if k == 2: 
                    await state.finish()
                    user_step[message.from_user.id] = None


@dp.message_handler(lambda message: message.text == "Пропустить")
async def skip_university(message: types.Message):
    step = user_step[message.from_user.id]
    await sk_uni(message, step)


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "university" or user_step.get(message.from_user.id) == "fav_university")
async def choose_university(message: types.Message):
    global selected_university

    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    elif message.text == "/support": await message.answer("Нельзя оставить обращение во время создания анкеты.")
    else:
        sel_uni = None
        step = user_step[message.from_user.id]

        selected_university = await ch_uni(message, sel_uni, step)

        if (selected_university != None) and (step == "university"): user_step[message.from_user.id] = "faculty"
        if (fav_selected_faculty != None) and (step == "fav_university"): user_step[message.from_user.id] = "fav_faculty"


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "faculty" or user_step.get(message.from_user.id) == "fav_faculty")
async def choose_faculty(message: types.Message):
    global selected_university, selected_faculty
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    elif message.text == "/support": await message.answer("Нельзя оставить обращение во время создания анкеты.")
    else:
        sel_uni = selected_university
        sel_fac = selected_faculty
        step = user_step[message.from_user.id]

        selected_faculty = await ch_fac(message, sel_uni, sel_fac, step)
        if (selected_faculty != None) & (step == "faculty"): user_step[message.from_user.id] = "direction"
        if (selected_faculty != None) & (step == "fav_faculty"): user_step[message.from_user.id] = "fav_direction"


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "direction" or user_step.get(message.from_user.id) == "fav_direction")
async def choose_direction(message: types.Message):
    global selected_university, selected_faculty, selected_direction
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    elif message.text == "/support": await message.answer("Нельзя оставить обращение во время создания анкеты.")
    else:
        sel_uni = selected_university
        sel_fac = selected_faculty
        sel_dir = None
        step = user_step[message.from_user.id]

        selected_direction = await ch_dir(message, sel_uni, sel_fac, sel_dir, step)
        if (selected_direction != None) and (step == "direction"): user_step[message.from_user.id] = "course"
        if (selected_direction != None) and (step == "fav_direction"): user_step[message.from_user.id] = "fav_course"


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "course" or user_step.get(message.from_user.id) == "fav_course")
async def choose_course(message: types.Message, state: FSMContext):
    global selected_university, selected_faculty, selected_direction, selected_course

    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    elif message.text == "/support": await message.answer("Нельзя оставить обращение во время создания анкеты.")
    else:
        sel_uni = selected_university
        sel_fac = selected_faculty
        sel_dir = selected_direction
        sel_cour = None
        step = user_step[message.from_user.id]

        selected_course = await ch_cour(message, sel_uni, sel_fac, sel_dir, sel_cour, step)
        if (selected_course != None) and (step == "course"): user_step[message.from_user.id] = "user_sex"
        if (selected_course != None) and (step == "fav_course"): 
            await bot.send_sticker(message.from_user.id, sticker="CAACAgIAAxkBAAJmxGV3AAGkN0qzoCp66xA_9O8Y9igXBgACzRMAAl6zyEvD5PzG428z7zME")
            user_step[message.from_user.id] = None


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "user_sex")
async def choose_user_sex(message: types.Message):
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    elif message.text == "/support": await message.answer("Нельзя оставить обращение во время создания анкеты.")
    else:
        k = 0
        k = await ch_us_sex(message, k)

        if k == 1: user_step[message.from_user.id] = "fav_university"



last_user = None
step_form = None
previous_step = None
@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "search", state=ProfileStatesGroup.choice)
async def search(message: types.Message, state: FSMContext):
    global last_user, step_form, previous_step
    if message.text == "/myprofile": await profile(message)
    elif message.text == "/notifications": await notifications(message)
    elif message.text == "/support": await support(message)    
    else:
        async with state.proxy() as data:
            data['choice'] = message.text

            if data['choice'] == "Глобальный поиск" or data['choice'] == "1":
                data['choice'] = "search"
                previous_step = "global_search"

            if data['choice'] == "Поиск по университету" or data['choice'] == "2":
                data['choice'] = "search"
                previous_step = "by_university"

            if data['choice'] == "Поиск по предпочтениям":
                data['choice'] = "search"
                previous_step = "narrow_search"


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "complaint", state=ProfileStatesGroup.choice)
async def complaint(message: types.Message, state: FSMContext):
    if message.text == "/myprofile": await profile(message)
    elif message.text == "/notifications": await notifications(message)
    elif message.text == "/support": await support(message)
    else:
        global last_user
        user_id = message.from_user.id
        data = await state.get_data()
        data['choice'] = message.text
        user_step[user_id] = "search"
        
        await comp(message, last_user)
        await state.finish()



lu = None # id лайкнувшего пользователя
step = None
@dp.message_handler(commands=['notifications'])
async def notifications(message: types.Message):
    global step
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/support": await support(message)    
    else:
        global lu
        liked_user = Liked_Users.select().where(Liked_Users.liked_id == message.from_user.id).exists()
        if liked_user:
            liked_user = Liked_Users.get(Liked_Users.liked_id == message.from_user.id)
            user = Users.get(Users.id == liked_user.user)

            photo = user.photo
            university = University.get(University.id == user.university)
            faculty = Faculty.get((Faculty.id == user.faculty) & (Faculty.university_id == university.id))
            direction = Direction.get((Direction.id == user.direction) & (Direction.faculty_id == faculty.id))
            course = Course.get((Course.id == user.course) & (Course.direction_id == direction.id))
            input_file = InputFile(io.BytesIO(photo), filename="user_photo.jpg")
            if user.information != None:
                form = f"{user.name}, {user.age}\n{university.university} - {faculty.faculty} - {direction.direction} - {course.course} курс\n\n{user.information}"
            else: 
                form = f"{user.name}, {user.age}\n{university.university} - {faculty.faculty} - {direction.direction} - {course.course} курс"
            await bot.send_photo(chat_id=message.from_user.id, photo=input_file, caption=form)
            if liked_user.message:
                await message.answer(text=f"<b>Сообщение от пользователя:</b>\n\n{liked_user.message}", parse_mode="HTML")

            lu = user.id

            user_step[message.from_user.id] = "notifications"

            if liked_user.mutually == False:
                l_d = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                l_d.add(
                    KeyboardButton(text=emoji.emojize(":thumbs_down:")),
                    KeyboardButton(text=emoji.emojize(":red_heart:"))
                )
                await message.answer(text="Выбери действие:", reply_markup=l_d)
                await ProfileStatesGroup.choice.set()
            else:
                chat_id = message.from_user.id
                link = f"https://t.me/{user.name_tg}"
                user_profile_link = f"Приятного общения с {link}!"
                await bot.send_message(chat_id, text=user_profile_link, parse_mode="HTML")

                Liked_Users.delete().where((Liked_Users.user == user.id) & (Liked_Users.liked_id == message.from_user.id)).execute()
                Liked_Users.delete().where((Liked_Users.user == message.from_user.id) & (Liked_Users.liked_id == user.id)).execute()
                step = "next_form"
        else:
            await message.answer(text="Пока что у тебя нет уведомлений", reply_markup=types.ReplyKeyboardRemove())
            await bot.send_sticker(message.from_user.id, sticker="CAACAgIAAxkBAAJmvmV2_K91_LwCwP_yQcYVqOKlYj8iAALGFAACckXQS2ucYVpYIo33MwQ")


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "notifications", state=ProfileStatesGroup.choice)
async def notification(message: types.Message, state=FSMContext):
    global lu, step
    step = None
    async with state.proxy() as data:
        data['choice'] = message.text

        if message.text == "/myprofile":
            await profile(message)
        elif message.text == "/notifications":
            await notifications(message)
        elif message.text == "/support": await support(message)
        else:
            if message.text == emoji.emojize(":thumbs_down:"):
                user = Users.get(Users.id == lu)
                Liked_Users.delete().where((Liked_Users.user == user.id) & (Liked_Users.liked_id == message.from_user.id)).execute()
                step = "next_form"
                lu = user.id

                
            if message.text == emoji.emojize(":red_heart:"):
                date = datetime.now().date()
                liked_user = Liked_Users.get((Liked_Users.user == lu) & (Liked_Users.liked_id == message.from_user.id))
                user = Users.get(Users.id == liked_user.user)
                me = Users.get(Users.id == message.from_user.id)

                liked_user = Liked_Users.create(user=me.id, liked_id=user.id, watched=False, mutually=True, date=date)
                liked_user.save()

                chat_id = message.from_user.id
                user_profile_link = f'Приятного общения с <a href="tg://openmessage?user_id={user.id}">@{user.name_tg}</a>!'
                await bot.send_message(chat_id, text=user_profile_link, parse_mode="HTML")

                Liked_Users.delete().where((Liked_Users.user == user.id) & (Liked_Users.liked_id == me.id)).execute()
                step = "next_form"


            if step == "next_form":
                liked_user = Liked_Users.select().where(Liked_Users.liked_id == message.from_user.id).exists()
                if liked_user:
                    liked_user = Liked_Users.get(Liked_Users.liked_id == message.from_user.id)
                    user = Users.get(Users.id == liked_user.user)

                    photo = user.photo
                    university = University.get(University.id == user.university)
                    faculty = Faculty.get((Faculty.id == user.faculty) & (Faculty.university_id == university.id))
                    direction = Direction.get((Direction.id == user.direction) & (Direction.faculty_id == faculty.id))
                    course = Course.get((Course.id == user.course) & (Course.direction_id == direction.id))
                    input_file = InputFile(io.BytesIO(photo), filename="user_photo.jpg")
                    if user.information != None:
                        form = f"{user.name}, {user.age}\n{university.university} - {faculty.faculty} - {direction.direction} - {course.course} курс\n\n{user.information}"
                    else: 
                        form = f"{user.name}, {user.age}\n{university.university} - {faculty.faculty} - {direction.direction} - {course.course} курс"
                    await bot.send_photo(chat_id=message.from_user.id, photo=input_file, caption=form)
                    if liked_user.message:
                        await message.answer(text=f"<b>Сообщение от пользователя:</b>\n\n{liked_user.message}", parse_mode="HTML")

                    lu = user.id

                    user_step[message.from_user.id] = "notifications"

                    if liked_user.mutually == False:
                        l_d = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                        l_d.add(
                            KeyboardButton(text=emoji.emojize(":thumbs_down:")),
                            KeyboardButton(text=emoji.emojize(":red_heart:"))
                        )
                        await message.answer(text="Выбери действие:", reply_markup=l_d)
                    else:
                        chat_id = message.from_user.id
                        user_profile_link = f'Приятного общения с <a href="tg://openmessage?user_id={user.id}">@{user.name_tg}</a>!'
                        await bot.send_message(chat_id, text=user_profile_link, parse_mode="HTML")
                else:
                    await message.answer(text="У тебя больше нет уведомлений", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands=['support'])
async def support(message: types.Message):
    await message.answer(text=f"Здесь ты можешь написать свои жалобу по тех.части или предложения по улучшению бота {emoji.emojize(':wrench:')}", reply_markup=types.ReplyKeyboardRemove())
    user_step[message.from_user.id] = "support"
    await ProfileStatesGroup.support.set()


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "support", state=ProfileStatesGroup.support)
async def support_(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['support'] = message.text
        if message.text == "/myprofile": await profile(message)
        elif message.text == "/notifications": await notifications(message)
        elif message.text == "/support": await support(message)

        else:
            user_id = message.from_user.id
            await sup(message, user_id)
            user_step[message.from_user.id] = None
            await state.finish()




if __name__ == "__main__":
    executor.start_polling(dp)


db.close()