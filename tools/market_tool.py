from langchain_core.tools import tool
from db.database import SessionLocal
from db.manager import FarmDataManager

@tool
def get_market_prices(crop: str, location_county: str | None = None):
    """
    Fetch current market prices for a specific crop.
    If location_county is provided, it fetches localized Kenyan market data based on community reports.
    Otherwise, it returns general benchmarks.
    """
    db = SessionLocal()
    manager = FarmDataManager(db)
    try:
        # 1. Try to get localized community-reported price
        if location_county:
            avg_price = manager.get_average_market_price(crop, location_county)
            if avg_price:
                return f"Localized Market Price for {crop} in {location_county}: KES {avg_price:.2f} per unit (Based on community reports)."

        # 2. Fallback to general benchmark data
        market_data = {
            "corn": "KES 45 per kg (Stable)",
            "maize": "KES 45 per kg (Stable)",
            "soybeans": "KES 80 per kg (Trending Up)",
            "wheat": "KES 60 per kg (Volatile)",
            "coffee": "KES 180 per kg (Trending Down)",
            "tea": "KES 120 per kg (Stable)"
        }
        crop_lower = crop.lower()
        return market_data.get(crop_lower, f"Local market data for {crop} is currently unavailable, but benchmark prices suggest a stable trend.")
    finally:
        db.close()
