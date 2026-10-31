from typing import Any, Optional
from db.database import SessionLocal
from db.manager import FarmDataManager


class FarmService:
    def __init__(self, db: Any = None):
        self.db = db if db is not None else SessionLocal()
        self.manager = FarmDataManager(self.db)

    def get_full_profile(self):
        profile = self.manager.get_profile()
        if not profile:
            return {"location": "", "soil": "", "crops": "", "size": ""}
        if isinstance(profile, dict):
            return {
                "location": profile.get("location", "") or "",
                "soil": profile.get("soil_type", "") or "",
                "crops": profile.get("main_crops", "") or "",
                "size": profile.get("size", "") or ""
            }
        return {
            "location": getattr(profile, "location", "") or "",
            "soil": getattr(profile, "soil_type", "") or "",
            "crops": getattr(profile, "main_crops", "") or "",
            "size": getattr(profile, "size", "") or ""
        }

    def update_farm_profile(self, data: dict):
        return self.manager.update_profile(
            data.get("location"), 
            data.get("soil"), 
            data.get("crops"), 
            data.get("size")
        )

    def manage_fields(self, action: str, data: Optional[dict] = None, field_id: Any = None):
        if action == "add":
            return self.manager.add_field(
                data['name'], data['crop'], data['date'], data['area'], data.get('notes', "")
            )
        elif action == "delete":
            return self.manager.delete_field(field_id)
        elif action == "list":
            return self.manager.get_all_fields()
        return None

    def log_activity(self, field_id: Any, activity_data: dict):
        return self.manager.add_log(
            field_id, 
            activity_data['type'], 
            activity_data['description'], 
            activity_data.get('amount', "")
        )

    def get_field_logs(self, field_id: Any):
        return self.manager.get_logs_for_field(field_id)
