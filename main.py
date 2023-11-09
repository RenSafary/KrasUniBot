from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, InputFile
from peewee import *
import io
import emoji
import asyncio
from datetime import *

from keyboards import *
from models import *

TOKEN_API = "6677193949:AAEGvtUogiiZewOqdw8OxEIbI8hC4CqI3U8"

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

class ProfileStatesGroup(StatesGroup):
    name = State()
    sex = State()
    age = State()
    inf = State()
    photo = State()
    choice = State()
    complaint = State()

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

        text = "1. Заполнить анкету заново " + emoji.emojize(":writing_hand:") + "\n2. Изменить фото " + emoji.emojize(":sunglasses:") + "\n3. Изменить текст анкеты " + emoji.emojize(":pencil:") + "\n4. Смотреть анкеты " + emoji.emojize(":man_detective:")
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

    else:
        global k

        async with state.proxy() as data:
            data['choice'] = message.text
            if data['choice'] == "1":
                await message.answer("Введи своё имя:")
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
    elif message.text == "/notifications":
        await notifications(message)
    else:
        async with state.proxy() as data:
            data['name'] = message.text

            user = Users.delete().where(Users.id == message.from_user.id)
            user.execute()

            name = Users.create(id=int(message.from_user.id), name_tg=message.from_user.full_name, name=data['name'])
            name.save()

            await message.answer(text=f"Сколько тебе лет?")
            user_step[message.from_user.id] = "age"
            await ProfileStatesGroup.age.set()


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "age", state=ProfileStatesGroup.age)
async def user_age(message: types.Message, state: FSMContext):
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        async with state.proxy() as data:
            data['age'] = message.text
            user_age = data['age']
            try:
                if int(user_age) >= 16 & int(user_age) <= 26:
                    Users.update(age=user_age).where(Users.id == int(message.from_user.id)).execute()

                    user_step[message.from_user.id] = "sex"
                    await message.answer(text=f'Твой пол:', reply_markup=sex)
                    await ProfileStatesGroup.sex.set()
            except:
                await message.answer(text='Возраст был введён неверно..\nПопробуйте ещё раз:')
                user_step[message.from_user.id] = "age"
                await ProfileStatesGroup.age.set()


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "sex", state=ProfileStatesGroup.sex)
async def user_sex(message: types.Message, state: FSMContext):
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        async with state.proxy() as data:
            data['sex'] = message.text
            user_sex = data['sex']
            k = 0

            if user_sex.lower() == 'м' or user_sex.lower() == 'm' or user_sex == emoji.emojize(":man:"):
                Users.update(sex="М").where(Users.id == int(message.from_user.id)).execute()
                k+=1

            elif user_sex.lower() == 'ж' or user_sex == emoji.emojize(":woman:"):
                Users.update(sex="Ж").where(Users.id == int(message.from_user.id)).execute()
                k+=1

            else:
                await message.answer(text='Пол был введён неверетно..\nПопробуйте ещё раз:')
                user_step[message.from_user.id] = "sex"
                await ProfileStatesGroup.sex.set()
                
            if k == 1:
                skip = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                skip.add(KeyboardButton(text="Пропустить"))
                await message.answer(text=f"Напиши что-нибудь о себе", reply_markup=skip)
                user_step[message.from_user.id] = "inf"
                await ProfileStatesGroup.inf.set()


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "inf", state=ProfileStatesGroup.inf)
async def user_inf(message: types.Message, state: FSMContext):
    global k
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        async with state.proxy() as data:
            data['inf'] = message.text
            user_inf = data['inf']
            if user_inf != "Пропустить":
                Users.update(information=user_inf).where(Users.id == int(message.from_user.id)).execute()

            if k == 3:
                await state.finish()
                await message.answer(text="Вернуться к анкете..", reply_markup=my_profile)
            else:
                await message.answer(text=f'{message.from_user.full_name}, осталось прикрепить твоё фото', reply_markup=types.ReplyKeyboardRemove())
                user_step[message.from_user.id] = "photo"
                await ProfileStatesGroup.photo.set()


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "photo", state=ProfileStatesGroup.photo, content_types=ContentType.PHOTO)
async def user_photo(message: types.Message, state: FSMContext):
    global k
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        async with state.proxy() as data:
            if message.content_type == "photo":
                photo_binary = io.BytesIO()
                await message.photo[-1].download(photo_binary)
                data['photo'] = photo_binary.getvalue()

                name = Users.update(photo=data['photo']).where(Users.id == int(message.from_user.id)).execute()

                await message.answer(text="Ваша фотография успешно загружена")
                user_step[message.from_user.id] = None
                await state.finish()

                if k == 2:
                    await state.finish()
                    await message.answer(text="Вернуться к анкете..", reply_markup=my_profile)
                if k == 1:
                    await message.answer(text="Теперь нужно ввести информацию по вузу..")
                    text = emoji.emojize(":warning:") + emoji.emojize(":warning:") + emoji.emojize(":warning:") + '\n' + "Пропуская выбор факультета, направления или курса, уменьшается шанс нахождения вашей анкеты другими пользователями." 
                    await message.answer(text=text)
                    await message.answer(text="Для начала выбери свой вуз:", reply_markup=university)
                    user_step[message.from_user.id] = "university"
            

@dp.message_handler(lambda message: message.text == "Пропустить")
async def skip_university(message: types.Message):
    step = user_step[message.from_user.id]
    if step == "fav_faculty":
        Users.update(fav_faculty=None, fav_direction=None, fav_course=None).execute()
        await message.answer(text='Анкета успешно заполнена.', reply_markup=types.ReplyKeyboardRemove())
        await message.answer(text="Открыть анкету..", reply_markup=my_profile)
    if step == "fav_direction":
        Users.update(fav_direction=None, fav_course=None).execute()
        await message.answer(text='Анкета успешно заполнена.', reply_markup=types.ReplyKeyboardRemove())
        await message.answer(text="Открыть анкету..", reply_markup=my_profile)
    if step == "fav_course":
        Users.update(fav_direction=None, fav_course=None).execute()
        await message.answer(text='Анкета успешно заполнена.', reply_markup=types.ReplyKeyboardRemove())
        await message.answer(text="Открыть анкету..", reply_markup=my_profile)


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "university")
async def choose_university(message: types.Message):
    global selected_university

    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        user_id = message.from_user.id
        selected_university = message.text
        
        universities = University.select().where(University.university == selected_university).exists()

        if universities:
            uni = University.get(University.university == selected_university)
            if selected_university.upper() == uni.university:
                user_step[user_id] = "faculty"

                Users.update(university=uni.id).where(Users.id == user_id).execute()

                faculties = Faculty.select().where(Faculty.university_id == uni.id)
                faculties_arr = [i.faculty for i in faculties]
                fac = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                for i in faculties_arr:
                    fac.add(KeyboardButton(text=i))
                await message.answer(text="Теперь выбери факультет:", reply_markup=fac)
        else:
            await message.answer(text=f'<b>{selected_university}</b> не найден, попробуйте еще раз:', parse_mode="HTML")


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "faculty")
async def choose_faculty(message: types.Message):
    global selected_university, selected_faculty
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        user_id = message.from_user.id
        selected_faculty = message.text
        selected_faculty = selected_faculty.lower()

        universities = University.get(University.university == selected_university)
        faculties = Faculty.select().where((Faculty.university_id == universities.id) 
        & (Faculty.faculty == selected_faculty)).exists()

        if faculties:
            fac = Faculty.get((Faculty.university_id == universities.id) 
            & (Faculty.faculty == selected_faculty))
            user_step[user_id] = "direction"

            Users.update(faculty=fac.id).where(Users.id == user_id).execute()

            directions = Direction.select().where(Direction.faculty_id == fac.id) 
            directions_arr = [i.direction for i in directions]
            dir = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            for i in directions_arr:
                dir.add(types.KeyboardButton(text=i))
            await message.answer(text="Теперь выбери направление:", reply_markup=dir)
        else:
            await message.answer(text=f'<b>{selected_faculty}</b> не найден, попробуйте еще раз:', parse_mode="HTML")


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "direction")
async def choose_direction(message: types.Message):
    global selected_university, selected_faculty, selected_direction
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        user_id = message.from_user.id
        selected_direction = message.text
        selected_direction = selected_direction.lower()

        universities = University.get(University.university == selected_university)
        faculties = Faculty.get((Faculty.faculty == selected_faculty) & (Faculty.university_id == universities.id))
        directions = Direction.select().where((Direction.direction == selected_direction) & (Direction.faculty_id == faculties.id)).exists()
                
        if directions:
            dir = Direction.get((Direction.direction == selected_direction) & (Direction.faculty_id == faculties.id))
            user_step[user_id] = "course"

            Users.update(direction=dir.id).where(Users.id == user_id).execute()

            courses = Course.select().where(Course.direction_id == dir.id)
            courses_arr = [i.course for i in courses]
            cour = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            for i in courses_arr:
                cour.add(types.KeyboardButton(text=i))
            #cour.add(KeyboardButton(text="Пропустить"))
            await message.answer(text="Теперь выберите курс:", reply_markup=cour)
        else:
            await message.answer(text=f'Направление <b>{selected_direction}</b> не найдено, попробуйте еще раз:', parse_mode="HTML")


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "course")
async def choose_course(message: types.Message, state: FSMContext):
    global selected_university, selected_faculty, selected_direction, selected_course

    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        user_id = message.from_user.id
        selected_course = message.text

        universities = University.get(University.university == selected_university)
        faculties = Faculty.get((Faculty.faculty == selected_faculty) & (Faculty.university_id == universities.id))
        directions = Direction.get((Direction.direction == selected_direction) & (Direction.faculty_id == faculties.id))
        courses = Course.select().where((Course.course == selected_course) & (Course.direction_id == directions.id)).exists()

        if courses:
            cour = Course.get((Course.course == selected_course) & (Course.direction_id == directions.id))

            Users.update(course=cour.id).where(Users.id == user_id).execute()

            await message.answer(text="Осталось настроить параметры поиска...")
            user_step[user_id] = "user_sex"
            await message.answer(text="Кто тебе интересен?", reply_markup=another_user_sex)
        else:
            await message.answer(text=f"<b>{selected_course}</b> курс не найден, попробуйте снова:", parse_mode="HTML")


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "user_sex")
async def choose_user_sex(message: types.Message):
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        sex = message.text
        sex_arr = ["Парни", "Девушки", "Всё равно", "м", "m", "ж"]
        k = 0
        for i in range(0, len(sex_arr)):
            if sex.lower() == sex_arr[i].lower():
                if i == 0 or i == 3 or i == 4:
                    sex = "М"
                elif i == 1 or i == 5:
                    sex = "Ж"
                elif i == 2:
                    sex = "В"

                Users.update(fav_sex=sex).where(Users.id == message.from_user.id).execute()
                universities = University.select()
                university = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                for i in universities:
                    university.add(KeyboardButton(i.university))
                await message.answer("Выберите университет:", reply_markup=university)
                user_step[message.from_user.id] = "fav_uni"
                k+=1
                break
        if k == 0:
            await message.answer("Пол введён неверно. Повторите попытку.")


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "fav_uni")
async def fav_uni_(message: types.Message):
    global fav_selected_university
    fav_selected_university = message.text
    user_id = message.from_user.id

    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        universities = University.select()

        for i in universities:
            if fav_selected_university.upper() == i.university:
                user_step[user_id] = "fav_faculty"

                uni = University.get(University.university == fav_selected_university)
                Users.update(fav_university=uni.id).where(Users.id == user_id).execute()

                faculties = Faculty.select().where(Faculty.university_id == uni.id)
                faculties_arr = [i.faculty for i in faculties]
                fac = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                fac.add(KeyboardButton(text="Пропустить"))
                for i in faculties_arr:
                    fac.add(KeyboardButton(text=i))
                await message.answer(text="Теперь выберите факультет:", reply_markup=fac)
                user_step[user_id] = "fav_faculty"
                break
        else:
            await message.answer(text=f'<b>{fav_selected_university}</b> не найден, попробуйте еще раз:', parse_mode="HTML")


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "fav_faculty")
async def fav_faculty_(message: types.Message):
    global fav_selected_university, fav_selected_faculty

    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        user_id = message.from_user.id
        fav_selected_faculty = message.text
        fav_selected_faculty.lower()

        universities = University.get(University.university == fav_selected_university)
        faculties = Faculty.select().where((Faculty.university_id == universities.id) 
        & (Faculty.faculty == fav_selected_faculty)).exists()

        if faculties:
            user_step[user_id] = "fav_direction"

            fac = Faculty.get((Faculty.university_id == universities.id) & (Faculty.faculty == fav_selected_faculty))
            Users.update(fav_faculty=fac.id).where(Users.id == user_id).execute()

            directions = Direction.select().where(Direction.faculty_id == fac.id) 
            directions_arr = [i.direction for i in directions]
            dir = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            dir.add(KeyboardButton(text="Пропустить"))
            for i in directions_arr:
                dir.add(types.KeyboardButton(text=i)) 
            await message.answer(text="Теперь выберите направление:", reply_markup=dir)
            user_step[user_id] = "fav_direction"
        else:
            await message.answer(text=f'<b>{fav_selected_faculty}</b> не найден, попробуйте еще раз:', parse_mode="HTML")


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "fav_direction")
async def choose_direction(message: types.Message):
    global fav_selected_university, fav_selected_faculty, fav_selected_direction

    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        user_id = message.from_user.id
        fav_selected_direction = message.text
        fav_selected_direction = fav_selected_direction.lower()

        universities = University.get(University.university == fav_selected_university)
        faculties = Faculty.get((Faculty.faculty == fav_selected_faculty) & (Faculty.university_id == universities.id))
        directions = Direction.select().where((Direction.direction == fav_selected_direction) & (Direction.faculty_id == faculties.id)).exists()
            
        if directions:

            user_step[user_id] = "fav_course"

            dir = Direction.get((Direction.direction == fav_selected_direction) & (Direction.faculty_id == faculties.id))
            Users.update(fav_direction=dir.id).where(Users.id == user_id).execute()

            courses = Course.select().where(Course.direction_id == dir.id)
            courses_arr = [i.course for i in courses]
            cour = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            cour.add(KeyboardButton(text="Пропустить"))
            for i in courses_arr:
                cour.add(types.KeyboardButton(text=i))
            user_step[user_id] = "fav_course"
            await message.answer(text="Выбери курс:", reply_markup=cour)
        else:
            await message.answer(text=f'Направление <b>{fav_selected_direction}</b> не найдено, попробуйте еще раз:', parse_mode="HTML")            


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "fav_course")
async def choose_course(message: types.Message):
    global fav_selected_university, fav_selected_faculty, fav_selected_direction, fav_course

    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)
    else:
        user_id = message.from_user.id
        fav_selected_course = message.text

        universities = University.get(University.university == fav_selected_university)
        faculties = Faculty.get((Faculty.faculty == fav_selected_faculty) & (Faculty.university_id == universities.id))
        directions = Direction.get((Direction.direction == fav_selected_direction) & (Direction.faculty_id == faculties.id))
        courses = Course.select().where((Course.course == fav_selected_course) & (Course.direction_id == directions.id)).exists()

        if courses:
            await message.answer(text='Вы успешно прошли регистрацию.', reply_markup=types.ReplyKeyboardRemove())
            user_step[user_id] = None

            cour = Course.get((Course.course == fav_selected_course) & (Course.direction_id == directions.id))
            Users.update(fav_course=cour.id).where(Users.id == user_id).execute()

            await message.answer(text="Вернуться к выбору действия..", reply_markup=my_profile)
        else:
            await message.answer(text=f"<b>{fav_selected_course}</b> курс не найден, попробуйте снова:", parse_mode="HTML")


last_user = None
step_form = None
previous_step = None
@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "search", state=ProfileStatesGroup.choice)
async def search_form(message: types.Message, state: FSMContext):
    global last_user, step_form, previous_step
    if message.text == "/myprofile": await profile(message)
    if message.text == "/notifications": await notifications(message)    
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
            

            if step_form == "love_letter":
                step_form = None
                data['choice'] = message.text
                me = Users.get(Users.id == message.from_user.id)
                user = Users.get(Users.id == last_user)

                date = datetime.now().date()
                user = Users.get(Users.id == last_user)
                liked_user = Liked_Users.create(user=me.id, liked_id=user.id, message=data['choice'], date=date)
                liked_user.save()
                data['choice'] = "search"
            
            if data['choice'] == "Поиск по предпочтениям":
                pass

            if data['choice'] == emoji.emojize(":red_heart:"):
                date = datetime.now().date()
                user = Users.get(Users.id == last_user)
                like = Liked_Users.create(user=message.from_user.id, liked_id=user.id, watched=False, mutually=False, date=date)
                like.save()

                data['choice'] = "search"

            if data['choice'] == "search" or data['choice'] == emoji.emojize(":thumbs_down:"):
                me = Users.get(id=message.from_user.id)
                fav_university = University.get(University.id == me.fav_university)
                fav_faculty = Faculty.get(Faculty.university_id == fav_university.id)
                fav_direction = Direction.get(Direction.faculty_id == fav_faculty.id)
                fav_course = Course.get(Course.direction_id == fav_direction.id)

                mine_university = University.get(University.id == me.university)
                mine_faculty = Faculty.get(Faculty.university_id == mine_university.id)
                mine_direction = Direction.get(Direction.faculty_id == mine_faculty.id)
                mine_course = Course.get(Course.direction_id == mine_direction.id)
   
                watched_user = Watched_Users.select().where(Watched_Users.user == me.id)
                liked_user = Liked_Users.select().where(Liked_Users.user == me.id)

                watched_user_ids = [i.watched_user.id for i in watched_user]
                liked_user_ids = [i.liked_id.id for i in liked_user]

                if previous_step == "global_search":
                    if me.fav_sex == "В":
                        user_query = Users.select().where((Users.id != me.id) & ~Users.id.in_(watched_user_ids)
                        & ~Users.id.in_(liked_user_ids) & ((Users.fav_sex == me.sex) | (Users.fav_sex == "В")) 
                        & ((Users.sex == "М") | (Users.sex == "Ж"))).exists()
                    else:
                        user_query = Users.select().where((Users.id != me.id) & ~Users.id.in_(watched_user_ids)
                        & ~Users.id.in_(liked_user_ids) & (Users.sex == me.fav_sex) & (Users.fav_sex == me.sex)).exists()
                if previous_step == "by_university":
                    if me.fav_sex == "В":
                        user_query = Users.select().where((Users.id != me.id) & ~Users.id.in_(watched_user_ids)
                        & ~Users.id.in_(liked_user_ids) & (Users.university == fav_university.id) 
                        & ((Users.fav_sex == me.sex) | (Users.fav_sex == "В")) & ((Users.sex == "М") | (Users.sex == "Ж"))
                        & ((Users.age <= me.age + 3) | (Users.age >= me.age - 3))).exists()
                    else:
                        user_query = Users.select().where((Users.id != me.id) & ~Users.id.in_(watched_user_ids)
                        & ~Users.id.in_(liked_user_ids) & (Users.university == fav_university.id) 
                        & (Users.sex == me.fav_sex) & (Users.fav_sex == me.sex)
                        & ((Users.age <= me.age + 3) | (Users.age >= me.age - 3))).exists()
                if previous_step == "narrow_search":
                    if me.fav_sex == "В":
                        user_query = Users.select().where((Users.id != me.id) & ~Users.id.in_(watched_user_ids)
                        & ~Users.id.in_(liked_user_ids) & (Users.university == fav_university.id) 
                        & (Users.fav_university == mine_university.id) 
                        & (Users.faculty == fav_faculty.id) & (Users.fav_faculty == mine_faculty.id)
                        & (Users.direction == fav_direction.id) & (Users.fav_direction == mine_direction.id)
                        & (Users.course == fav_course.id) & (Users.fav_course == mine_course.id) 
                        & (Users.sex == me.fav_sex) & (Users.fav_sex == me.sex)
                        & ((Users.fav_sex == me.sex) | (Users.fav_sex == "В")) & ((Users.sex == "М") | (Users.sex == "Ж"))).exists()
                    else:
                        user_query = Users.select().where((Users.id != me.id) & ~Users.id.in_(watched_user_ids)
                        & ~Users.id.in_(liked_user_ids) & (Users.university == fav_university.id) 
                        & (Users.fav_university == mine_university.id) 
                        & (Users.faculty == fav_faculty.id) & (Users.fav_faculty == mine_faculty.id)
                        & (Users.direction == fav_direction.id) & (Users.fav_direction == mine_direction.id)
                        & (Users.course == fav_course.id) & (Users.fav_course == mine_course.id) 
                        & (Users.sex == me.fav_sex) & (Users.fav_sex == me.sex)).exists()
                # |-__-|-__-|-__-|-__-|-__-|-__-|-__-|-__-|-__-|-__-|-__-|-__-|-__-|-__-|-__-|-__-|
                if user_query:
                    if previous_step == "global_search":
                        if me.fav_sex == "В":
                            user = Users.get((Users.id != me.id) & ~Users.id.in_(watched_user_ids)
                            & ~Users.id.in_(liked_user_ids) & ((Users.fav_sex == me.sex) | (Users.fav_sex == "В")) 
                            & ((Users.sex == "М") | (Users.sex == "Ж")))
                        else:
                            user = Users.get((Users.id != me.id) & ~Users.id.in_(watched_user_ids)
                            & ~Users.id.in_(liked_user_ids) & (Users.sex == me.fav_sex) & (Users.fav_sex == me.sex))
                    if previous_step == "by_university":
                        if me.fav_sex == "В":
                            user = Users.get((Users.id != me.id) & ~Users.id.in_(watched_user_ids)
                            & ~Users.id.in_(liked_user_ids) & (Users.university == fav_university.id) 
                            & ((Users.fav_sex == me.sex) | (Users.fav_sex == "В")) & ((Users.sex == "М") | (Users.sex == "Ж"))
                            & ((Users.age <= me.age + 3) | (Users.age >= me.age - 3)))
                        else:
                            user = Users.get((Users.id != me.id) & ~Users.id.in_(watched_user_ids)
                            & ~Users.id.in_(liked_user_ids) & (Users.university == fav_university.id) 
                            & (Users.sex == me.fav_sex) & (Users.fav_sex == me.sex)
                            & ((Users.age >= me.age - 2) | (Users.age <= me.age + 2)))
                    if previous_step == "narrow_search":
                        if me.fav_sex == "В":
                            user = Users.get((Users.id != me.id) & ~Users.id.in_(watched_user_ids)
                            & ~Users.id.in_(liked_user_ids) & (Users.university == fav_university.id) 
                            & (Users.fav_university == mine_university.id) 
                            & (Users.faculty == fav_faculty.id) & (Users.fav_faculty == mine_faculty.id)
                            & (Users.direction == fav_direction.id) & (Users.fav_direction == mine_direction.id)
                            & (Users.course == fav_course.id) & (Users.fav_course == mine_course.id) 
                            & (Users.sex == me.fav_sex) & (Users.fav_sex == me.sex)
                            & ((Users.fav_sex == me.sex) | (Users.fav_sex == "В")) & ((Users.sex == "М") | (Users.sex == "Ж")))
                        else:
                            user = Users.get((Users.id != me.id) & ~Users.id.in_(watched_user_ids)
                            & ~Users.id.in_(liked_user_ids) & (Users.university == fav_university.id) 
                            & (Users.fav_university == mine_university.id) 
                            & (Users.faculty == fav_faculty.id) & (Users.fav_faculty == mine_faculty.id)
                            & (Users.direction == fav_direction.id) & (Users.fav_direction == mine_direction.id)
                            & (Users.course == fav_course.id) & (Users.fav_course == mine_course.id) 
                            & (Users.sex == me.fav_sex) & (Users.fav_sex == me.sex))

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

                    date = datetime.now().date()
                    watched_user = Watched_Users.create(user=me.id, watched_user=user.id, date=date)
                    watched_user.save()
                    last_user = user.id
                        
                    await message.answer(text="Выбери действие:", reply_markup=like_dislike)
                else:
                    await message.answer(text="Анкеты закончились..", reply_markup=my_profile)

            if data['choice'] == emoji.emojize(":warning:"):
                await message.answer(text="Твоя жалоба на пользователя:")
                user_step[message.from_user.id] = "complaint"
                await ProfileStatesGroup.choice.set()

            if data['choice'] == emoji.emojize(":love_letter:"):
                await message.answer("Напиши сообщение, которое хочешь отправить пользователю..")
                await ProfileStatesGroup.choice.set()
                step_form = "love_letter"


@dp.message_handler(lambda message: user_step.get(message.from_user.id) == "complaint", state=ProfileStatesGroup.choice)
async def complaint(message: types.Message, state: FSMContext):
    if message.text == "/myprofile": await profile(message)
    if message.text == "/notifications": await notifications(message)
    else:
        global last_user
        user_id = message.from_user.id
        data = await state.get_data()
        data['choice'] = message.text
        user_step[user_id] = "search"
        user = Users.get(Users.id == user_id)
        intruder = Users.get(Users.id == last_user)

        comp = Complaint.create(user=user.id, intruder=intruder.id, message=data['choice'])
        comp.save()

        await message.answer(text="<b>Жалоба успешно добавлена.</b>", parse_mode="HTML", reply_markup=my_profile)
        await state.finish()



lu = None # id лайкнувшего пользователя
step = None
@dp.message_handler(commands=['notifications'])
async def notifications(message: types.Message):
    global step
    if message.text == "/myprofile":
        await profile(message)
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
                user_profile_link = f'Приятного общения с <a href="tg://openmessage?user_id={user.id}">{user.name_tg}</a>!'
                await bot.send_message(chat_id, text=user_profile_link, parse_mode="HTML")

                Liked_Users.delete().where((Liked_Users.user == user.id) & (Liked_Users.liked_id == message.from_user.id)).execute()
                Liked_Users.delete().where((Liked_Users.user == message.from_user.id) & (Liked_Users.liked_id == user.id)).execute()
                step = "next_form"
        else:
            await message.answer(text="У тебя нет уведомлений", reply_markup=types.ReplyKeyboardRemove())


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


if __name__ == "__main__":
    executor.start_polling(dp)


db.close()