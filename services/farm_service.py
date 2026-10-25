from sqlalchemy.orm import Session
from db.manager import FarmDataManager
from db.database import SessionLocal

class FarmService:
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.manager = FarmDataManager(self.db)

    def get_full_profile(self):
        profile = self.manager.get_profile()
        if not profile:
            return {"location": "", "soil": "", "crops": "", "size": ""}
        return {
            "location": profile.location,
            "soil": profile.soil_type,
            "crops": profile.main_crops,
            "size": profile.size
        }

    def update_farm_profile(self, data: dict):
        return self.manager.update_profile(
            data.get("location"), 
            data.get("soil"), 
            data.get("crops"), 
            data.get("size")
        )

    def manage_fields(self, action: str, data: dict = None, field_id: int = None):
        if action == "add":
            return self.manager.add_field(
                data['name'], data['crop'], data['date'], data['area'], data.get('notes', "")
            )
        elif action == "delete":
            return self.manager.delete_field(field_id)
        elif action == "list":
            return self.manager.get_all_fields()
        return None

    def log_activity(self, field_id: int, activity_data: dict):
        return self.manager.add_log(
            field_id, 
            activity_data['type'], 
            activity_data['description'], 
            activity_data.get('amount', "")
        )

    def get_field_logs(self, field_id: int):
        return self.manager.get_logs_for_field(field_id)
