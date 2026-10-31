from datetime import datetime, timezone
from bson import ObjectId
from db.models import FarmProfile, Field, ActivityLog, MarketReport


class FarmDataManager:
    def __init__(self, db):
        # db is the MongoDatabase instance
        self.db = db

    # --- Profile Management ---
    def update_profile(self, location, soil, crops, size):
        profile_data = {
            "location": location,
            "soil_type": soil,
            "main_crops": crops,
            "size": size,
            "updated_at": datetime.now(timezone.utc)
        }
        # We use a fixed ID 'default_profile' to simulate the single-profile nature of the app
        self.db.get_collection("farm_profiles").update_one(
            {"_id": "default_profile"},
            {"$set": profile_data},
            upsert=True
        )
        return FarmProfile(profile_data)

    def get_profile(self):
        doc = self.db.get_collection("farm_profiles").find_one({"_id": "default_profile"})
        return FarmProfile(doc) if doc else None

    # --- Field Management ---
    def add_field(self, name, crop, planted_date, area, notes=""):
        field_data = {
            "name": name,
            "crop": crop,
            "planted_date": planted_date,
            "area": area,
            "notes": notes
        }
        result = self.db.get_collection("fields").insert_one(field_data)
        field_data["_id"] = result.inserted_id
        return Field(field_data)

    def get_all_fields(self):
        docs = list(self.db.get_collection("fields").find())
        return [Field(d) for d in docs]

    def delete_field(self, field_id):
        # Support both string, ObjectId, and int
        if isinstance(field_id, ObjectId):
            query = {"_id": field_id}
        elif isinstance(field_id, str) and ObjectId.is_valid(field_id):
            query = {"$or": [{"_id": ObjectId(field_id)}, {"_id": field_id}]}
        else:
            query = {"_id": field_id}
        result = self.db.get_collection("fields").delete_one(query)
        return result.deleted_count > 0

    # --- Activity Logging ---
    def add_log(self, field_id, activity_type, description, amount=""):
        oid = ObjectId(field_id) if isinstance(field_id, str) and ObjectId.is_valid(field_id) else field_id
        log_data = {
            "field_id": oid,
            "date": datetime.now(timezone.utc),
            "activity_type": activity_type,
            "description": description,
            "amount": amount
        }
        result = self.db.get_collection("activity_logs").insert_one(log_data)
        log_data["_id"] = result.inserted_id
        return ActivityLog(log_data)

    def get_logs_for_field(self, field_id):
        queries = [{"field_id": field_id}]
        if isinstance(field_id, str) and ObjectId.is_valid(field_id):
            queries.append({"field_id": ObjectId(field_id)})
        elif isinstance(field_id, ObjectId):
            queries.append({"field_id": str(field_id)})
        query = {"$or": queries} if len(queries) > 1 else queries[0]
        docs = list(self.db.get_collection("activity_logs").find(query).sort("date", -1))
        return [ActivityLog(d) for d in docs]

    # --- Market Data Management ---
    def add_market_report(self, crop, price, unit, location_county, reported_by="system"):
        report_data = {
            "crop": crop,
            "price": price,
            "unit": unit,
            "location_county": location_county,
            "reported_by": reported_by,
            "date": datetime.now(timezone.utc)
        }
        result = self.db.get_collection("market_reports").insert_one(report_data)
        report_data["_id"] = result.inserted_id
        return MarketReport(report_data)

    def get_average_market_price(self, crop, location_county=None):
        pipeline = [
            {"$match": {"crop": {"$regex": crop, "$options": "i"}}}
        ]
        if location_county:
            pipeline.append({"$match": {"location_county": {"$regex": location_county, "$options": "i"}}})

        pipeline.append({
            "$group": {
                "_id": None,
                "avgPrice": {"$avg": "$price"}
            }
        })

        result = list(self.db.get_collection("market_reports").aggregate(pipeline))
        return result[0]["avgPrice"] if result else None
