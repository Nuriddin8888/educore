from datetime import datetime
from fastapi import HTTPException


def validate_attendance_time(group):
    now = datetime.now()

    # 🔥 schedule check
    if now.weekday() not in group.schedule:
        raise HTTPException(400, "Today is not a class day")

    # 🔥 start_date check
    if now.date() < group.start_date:
        raise HTTPException(400, "Course not started yet")

    # 🔥 time check
    if not group.time_slot:
        raise HTTPException(400, "Time slot not set")

    if now.time() < group.time_slot.start_time:
        raise HTTPException(400, "Attendance not started yet")

    return now.date()
