import unittest
from datetime import datetime, timezone
from db.database import SessionLocal
from services.farm_service import FarmService
from utils.memory_manager import MemoryManager
from tools.farm_data_tool import (
    get_farm_profile,
    list_farm_fields,
    get_field_activity_logs,
    search_activity_logs,
    get_field_trend_analysis,
)
from tools.market_tool import get_market_prices
from schemas.agri_schema import AgriResponse
from utils.notifications import NotificationEngine


class TestFarmPlan(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.farm_service = FarmService(self.db)
        self.memory = MemoryManager()
        self.farm_service.update_farm_profile({
            "location": "Eldoret, Kenya",
            "soil": "Volcanic loam",
            "crops": "Maize, Wheat",
            "size": "25 acres"
        })

    def test_profile_management(self):
        profile = self.farm_service.get_full_profile()
        self.assertEqual(profile["location"], "Eldoret, Kenya")
        self.assertEqual(profile["crops"], "Maize, Wheat")

    def test_field_and_activity_lifecycle(self):
        # 1. Add field
        field = self.farm_service.manage_fields("add", {
            "name": "East Field",
            "crop": "Coffee",
            "date": datetime.now(timezone.utc),
            "area": 5.0,
            "notes": "Testing notes"
        })
        self.assertIsNotNone(field.id)
        field_id = field.id

        # 2. List fields
        fields = self.farm_service.manage_fields("list")
        self.assertTrue(any(f.id == field_id for f in fields))

        # 3. Log activities
        self.farm_service.log_activity(field_id, {
            "type": "Irrigation",
            "description": "Drip irrigation applied",
            "amount": "100"
        })
        self.farm_service.log_activity(field_id, {
            "type": "Irrigation",
            "description": "Secondary watering",
            "amount": "120"
        })

        logs = self.farm_service.get_field_logs(field_id)
        self.assertGreaterEqual(len(logs), 2)

        # 4. Tools integration test
        profile_str = get_farm_profile.invoke({})
        self.assertIn("Eldoret", profile_str)

        fields_str = list_farm_fields.invoke({})
        self.assertIn("East Field", fields_str)

        logs_str = get_field_activity_logs.invoke({"field_id": str(field_id)})
        self.assertIn("Irrigation", logs_str)

        search_str = search_activity_logs.invoke({"query": "Drip"})
        self.assertIn("Drip", search_str)

        trend_str = get_field_trend_analysis.invoke({
            "field_id": str(field_id),
            "activity_type": "Irrigation"
        })
        self.assertIn("Trend Analysis", trend_str)

        # 5. Delete field
        deleted = self.farm_service.manage_fields("delete", field_id=field_id)
        self.assertTrue(deleted)

    def test_memory_manager(self):
        history = [{"role": "user", "content": f"Question {i}"} for i in range(12)]
        trimmed = self.memory.trim_history(history, max_messages=4)
        self.assertEqual(len(trimmed), 4)
        self.assertEqual(trimmed[-1]["content"], "Question 11")

        summary = self.memory.summarize_history(history, max_messages=4)
        self.assertTrue(len(summary) > 0)
        self.assertIn("Question 0", summary)

    def test_market_prices(self):
        prices = get_market_prices.invoke({"crop": "maize"})
        self.assertIn("KES", prices)

    def test_agri_schema_validation(self):
        valid_response = AgriResponse(
            summary="All indicators look solid.",
            requirements=[{"category": "Soil", "detail": "Apply 50kg DAP fertilizer per acre before planting"}],
            pro_tip="Always check moisture levels at root depth before irrigation.",
            alerts=[],
            confidence_score=0.98,
            verification_status="Weather forecast clear for 48 hours."
        )
        self.assertEqual(valid_response.confidence_score, 0.98)

    def test_notification_engine(self):
        notifier = NotificationEngine()
        result = notifier.send_alert("Severe frost alert", priority="HIGH")
        self.assertIn("Notification sent via", result)


if __name__ == "__main__":
    unittest.main()
