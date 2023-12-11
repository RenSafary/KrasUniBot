from peewee import *


db = SqliteDatabase('data.db')

class BaseModel(Model):
    class Meta:
        database = db


class University(BaseModel):
    id = IntegerField(primary_key=True)
    university = CharField(max_length=50)


class Faculty(BaseModel):
    id = IntegerField(primary_key=True)
    university_id = ForeignKeyField(University, backref="faculty")
    faculty = CharField(max_length=255)


class Direction(BaseModel):
    id = IntegerField(primary_key=True)
    faculty_id = ForeignKeyField(Faculty, backref="direction")  
    direction = CharField(max_length=255)  


class Course(BaseModel):
    id = IntegerField(primary_key=True)
    direction_id = ForeignKeyField(Direction, backref="course")  
    course = CharField(max_length=255)


class Users(BaseModel):
    id = IntegerField(primary_key=True)
    name_tg = CharField(max_length=255)
    name = CharField(max_length=255)
    information = TextField(null=True)
    sex = CharField(max_length=1, null=True)
    age = IntegerField(null=True)
    photo = BlobField(null=True)
    university = ForeignKeyField(University, backref='users', null=True)
    faculty = ForeignKeyField(Faculty, backref="user", null=True)
    direction = ForeignKeyField(Direction, backref="user", null=True)
    course = ForeignKeyField(Course, backref="user", null=True)
    fav_sex = CharField(max_length=1, null=True)
    fav_university = ForeignKeyField(University, null=True)
    fav_faculty = ForeignKeyField(Faculty, null=True)
    fav_direction = ForeignKeyField(Direction, null=True)
    fav_course = ForeignKeyField(Course, null=True)


class Liked_Users(BaseModel):
    user = ForeignKeyField(Users, backref="liked_users")
    liked_id = ForeignKeyField(Users)
    message = TextField(null=True)
    watched = BooleanField(null=True)
    mutually = BooleanField(null=True)
    date = DateField(null=True)


class Watched_Users(BaseModel):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(Users, backref="watched_users")
    watched_user = ForeignKeyField(Users)
    date = DateField(null=True)


class Complaint(BaseModel):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(Users, backref="complaint")
    intruder = ForeignKeyField(Users)
    message = TextField()


class Admin(BaseModel):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(Users, backref='admin')


class Support(BaseModel):
    id = IntegerField(primary_key=True)
    user = ForeignKeyField(Users, backref="support")
    text = TextField()


if __name__ == "__main__":
    db.connect()
    db.create_tables([Users])
    db.close()