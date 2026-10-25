from sqlalchemy.orm import Session
from db.models import FarmProfile, Field, ActivityLog
from datetime import datetime

class FarmDataManager:
    def __init__(self, db: Session):
        self.db = db

    # --- Profile Management ---
    def update_profile(self, location, soil, crops, size):
        profile = self.db.query(FarmProfile).first()
        if not profile:
            profile = FarmProfile(location=location, soil_type=soil, main_crops=crops, size=size)
            self.db.add(profile)
        else:
            profile.location = location
            profile.soil_type = soil
            profile.main_crops = crops
            profile.size = size
        self.db.commit()
        return profile

    def get_profile(self):
        return self.db.query(FarmProfile).first()

    # --- Field Management ---
    def add_field(self, name, crop, planted_date, area, notes=""):
        field = Field(name=name, crop=crop, planted_date=planted_date, area=area, notes=notes)
        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)
        return field

    def get_all_fields(self):
        return self.db.query(Field).all()

    def delete_field(self, field_id):
        field = self.db.query(Field).filter(Field.id == field_id).first()
        if field:
            self.db.delete(field)
            self.db.commit()
            return True
        return False

    # --- Activity Logging ---
    def add_log(self, field_id, activity_type, description, amount=""):
        log = ActivityLog(field_id=field_id, activity_type=activity_type, description=description, amount=amount)
        self.db.add(log)
        self.db.commit()
        return log

    def get_logs_for_field(self, field_id):
        return self.db.query(ActivityLog).filter(ActivityLog.field_id == field_id).order_by(ActivityLog.date.desc()).all()
