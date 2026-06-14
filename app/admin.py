from sqladmin import ModelView
from app.models.user import User
from app.models.group import Group
from app.models.student import Student
from app.models.holiday import Holiday
from app.models.attendance import Attendance
from app.models.system_settings import SystemSettings




class StudentAdmin(ModelView, model=Student):

    name = "Student"
    name_plural = "Students"

    column_list = [
        Student.id,
        Student.full_name,
        Student.phone_number,
        Student.student_code,
        Student.status
    ]

    column_searchable_list = [
        Student.full_name,
        Student.phone_number,
        Student.student_code
    ]

    column_sortable_list = [
        Student.id,
        Student.full_name
    ]





class TeacherAdmin(ModelView, model=User):

    name = "Teacher"
    name_plural = "Teachers"

    column_list = [
        User.id,
        User.full_name,
        User.phone_number,
        User.role
    ]




class GroupAdmin(ModelView, model=Group):

    column_list = [
        Group.id,
        Group.name,
        Group.price,
        Group.teacher_id
    ]





class AttendanceAdmin(
    ModelView,
    model=Attendance
):

    column_list = [
        Attendance.id,
        Attendance.student_id,
        Attendance.date,
        Attendance.status,
        Attendance.lesson_price
    ]


class HolidayAdmin(
    ModelView,
    model=Holiday
):

    column_list = [
        Holiday.id,
        Holiday.date,
        Holiday.name,
        Holiday.is_paid
    ]


class SettingsAdmin(
    ModelView,
    model=SystemSettings
):

    column_list = [
        SystemSettings.id,
        SystemSettings.tax_percent
    ]