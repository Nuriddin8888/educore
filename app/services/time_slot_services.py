from app.models.time_slot import TimeSlot



def create_time_slot(db, data):
    # 🔥 unique check
    existing = db.query(TimeSlot).filter(
        TimeSlot.start_time == data.start_time,
        TimeSlot.end_time == data.end_time
    ).first()

    if existing:
        raise ValueError("Time slot already exists")

    new_time = TimeSlot(
        start_time=data.start_time,
        end_time=data.end_time
    )

    db.add(new_time)
    db.commit()
    db.refresh(new_time)

    return new_time


def get_all_time_slots(db):
    return db.query(TimeSlot).all()


def get_time_slot(db, time_slot_id: int):
    time_slot = db.query(TimeSlot).filter(
        TimeSlot.id == time_slot_id
    ).first()

    if not time_slot:
        raise ValueError("Time slot not found")

    return time_slot


def delete_time_slot(db, time_slot_id: int):
    time_slot = get_time_slot(db, time_slot_id)

    db.delete(time_slot)
    db.commit()

    return {"message": "Deleted"}