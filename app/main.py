from sqladmin import Admin
from fastapi import FastAPI
from app.db.session import engine
from app.admin_auth import AdminAuth
from fastapi.staticfiles import StaticFiles
from app.admin import StudentAdmin, TeacherAdmin, GroupAdmin, AttendanceAdmin, HolidayAdmin, SettingsAdmin
from app.api.v1.endpoints import auth, group, student, teacher, attendance, payment, dashboard, room, time_slot, salary, grade, replace
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="EduCore API")

app.mount("/media", StaticFiles(directory="app/media"), name="media")

app.include_router(auth.router)
app.include_router(group.router)
app.include_router(student.router)
app.include_router(teacher.router)
app.include_router(replace.router)
app.include_router(salary.router)
app.include_router(attendance.router)
app.include_router(payment.router)
app.include_router(dashboard.router)
app.include_router(room.router)
app.include_router(time_slot.router)
app.include_router(grade.router)


authentication_backend = AdminAuth(
    secret_key="super-secret-key"
)


admin = Admin(
    app,
    engine,
    authentication_backend=authentication_backend
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

admin.add_view(StudentAdmin)
admin.add_view(TeacherAdmin)
admin.add_view(GroupAdmin)
admin.add_view(AttendanceAdmin)
admin.add_view(HolidayAdmin)
admin.add_view(SettingsAdmin)


