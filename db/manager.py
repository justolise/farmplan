from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import ActivityLog, FarmProfile, Field, MarketReport


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

    # --- Market Data Management ---
    def add_market_report(self, crop, price, unit, location_county, reported_by="system"):
        report = MarketReport(crop=crop, price=price, unit=unit, location_county=location_county, reported_by=reported_by)
        self.db.add(report)
        self.db.commit()
        return report

    def get_average_market_price(self, crop, location_county=None):
        query = self.db.query(func.avg(MarketReport.price))
        query = query.filter(MarketReport.crop.ilike(f"%{crop}%"))

        if location_county:
            query = query.filter(MarketReport.location_county.ilike(f"%{location_county}%"))

        avg_price = query.scalar()
        return avg_price
