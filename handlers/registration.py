from peewee import *
from aiogram import types


from keyboards import *
from models import *


async def us_name(message: types.Message): # name
    user = Users.delete().where(Users.id == message.from_user.id)
    user.execute()

    name = Users.create(id=int(message.from_user.id), name_tg=message.from_user.username, name=message.text)
    name.save()

    await message.answer(text=f"Сколько тебе лет?")


async def us_age(message: types.Message): # age
    Users.update(age=message.text).where(Users.id == int(message.from_user.id)).execute()
    await message.answer(text=f'Твой пол:', reply_markup=sex)


async def us_sex(message: types.Message, i): # sex
    if message.text.lower() == 'м' or message.text.lower() == 'm' or message.text == emoji.emojize(":man:"):
        Users.update(sex="М").where(Users.id == int(message.from_user.id)).execute()
        i+=1

    elif message.text.lower() == 'ж' or message.text == emoji.emojize(":woman:"):
        Users.update(sex="Ж").where(Users.id == int(message.from_user.id)).execute()
        i+=1

    else:
        await message.answer(text='Пол был введён неверно..\nПопробуй ещё раз:')

    if i == 1:
        skip = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        skip.add(KeyboardButton(text="Пропустить"))
        await message.answer(text=f"Напиши что-нибудь о себе", reply_markup=skip)
    return i


async def us_inf(message: types.Message, i): # information
    if message.text == "Пропустить":
        pass
    else: Users.update(information=message.text).where(Users.id == int(message.from_user.id)).execute()
    if i == 3:
        await message.answer(text="Вернуться к анкете..", reply_markup=my_profile)
    else:
        name = Users.get(Users.id == message.from_user.id)
        await message.answer(text=f'{name.name}, давай прикрепим твоё фото', reply_markup=types.ReplyKeyboardRemove())
    return i
            

async def sk_uni(message: types.Message, step): # skip_university
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


async def ch_uni(message: types.Message, selected_university, step): # university
    user_id = message.from_user.id
    selected_university = message.text
        
    universities = University.select().where(University.university == selected_university).exists()

    if universities:
        uni = University.get(University.university == selected_university)
        if selected_university.upper() == uni.university:

            if step == "university": Users.update(university=uni.id).where(Users.id == user_id).execute()
            if step == "fav_university": Users.update(fav_university=uni.id).where(Users.id == user_id).execute()

            faculties = Faculty.select().where(Faculty.university_id == uni.id)
            faculties_arr = [i.faculty for i in faculties]
            fac = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            for i in faculties_arr:
                fac.add(KeyboardButton(text=i))
            await message.answer(text="Теперь выбери факультет:", reply_markup=fac)
    else:
        selected_university = None
        await message.answer(text=f'<b>Не найдено,</b> попробуйте еще раз:', parse_mode="HTML")
    return selected_university


async def ch_fac(message: types.Message, selected_university, selected_faculty, step): # faculty
    user_id = message.from_user.id
    selected_faculty = message.text
    selected_faculty = selected_faculty.lower()

    universities = University.get(University.university == selected_university)
    faculties = Faculty.select().where((Faculty.university_id == universities.id) 
    & (Faculty.faculty == selected_faculty)).exists()

    if faculties:
        fac = Faculty.get((Faculty.university_id == universities.id) 
        & (Faculty.faculty == selected_faculty))

        if step == "faculty": Users.update(faculty=fac.id).where(Users.id == user_id).execute()
        if step == "fav_faculty": Users.update(fav_faculty=fac.id).where(Users.id == user_id).execute()

        directions = Direction.select().where(Direction.faculty_id == fac.id) 
        directions_arr = [i.direction for i in directions]
        dir = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        for i in directions_arr:
            dir.add(types.KeyboardButton(text=i))
        await message.answer(text="Теперь выбери направление:", reply_markup=dir)
    else:
        selected_faculty = None
        await message.answer(text=f'<b>Не найдено,</b> попробуйте еще раз:', parse_mode="HTML")
    return selected_faculty


async def ch_dir(message: types.Message, selected_university, selected_faculty, selected_direction, step): # direction
    user_id = message.from_user.id
    selected_direction = message.text
    selected_direction = selected_direction.lower()

    universities = University.get(University.university == selected_university)
    faculties = Faculty.get((Faculty.faculty == selected_faculty) & (Faculty.university_id == universities.id))
    directions = Direction.select().where((Direction.direction == selected_direction) & (Direction.faculty_id == faculties.id)).exists()

    if directions:
        dir = Direction.get((Direction.direction == selected_direction) & (Direction.faculty_id == faculties.id))

        if step == "direction": Users.update(direction=dir.id).where(Users.id == user_id).execute()
        if step == "fav_direction": Users.update(fav_direction=dir.id).where(Users.id == user_id).execute()

        courses = Course.select().where(Course.direction_id == dir.id)
        courses_arr = [i.course for i in courses]
        cour = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        for i in courses_arr:
            cour.add(types.KeyboardButton(text=i))
        await message.answer(text="Теперь выберите курс:", reply_markup=cour)
    else:
        selected_direction = None
        await message.answer(text=f'<b>Не найдено,</b> попробуйте еще раз:', parse_mode="HTML")
    return selected_direction


async def ch_cour(message: types.Message, selected_university, selected_faculty, selected_direction, selected_course, step): # course
    user_id = message.from_user.id
    selected_course = message.text

    universities = University.get(University.university == selected_university)
    faculties = Faculty.get((Faculty.faculty == selected_faculty) & (Faculty.university_id == universities.id))
    directions = Direction.get((Direction.direction == selected_direction) & (Direction.faculty_id == faculties.id))
    courses = Course.select().where((Course.course == selected_course) & (Course.direction_id == directions.id)).exists()

    if courses:
        cour = Course.get((Course.course == selected_course) & (Course.direction_id == directions.id))

        if step == "course": 
            Users.update(course=cour.id).where(Users.id == user_id).execute()
            await message.answer(text="Осталось настроить параметры поиска...")
            await message.answer(text="Кто тебе интересен?", reply_markup=another_user_sex)
        if step == "fav_course": 
            Users.update(fav_course=cour.id).where(Users.id == user_id).execute()

            await message.answer(text='Вы успешно прошли регистрацию.', reply_markup=types.ReplyKeyboardRemove())
            await message.answer(text="Вернуться к выбору действия..", reply_markup=my_profile)
    else:
        selected_course = None
        await message.answer(text=f'<b>Не найдено,</b> попробуйте еще раз:', parse_mode="HTML")
    return selected_course


async def ch_us_sex(message: types.Message, k): # user's sex
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
            k = 1
            break
    if k == 0:
        await message.answer("Пол введён неверно. Повторите попытку.")
    return k