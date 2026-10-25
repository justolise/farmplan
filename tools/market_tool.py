from langchain_core.tools import tool

@tool
def get_market_prices(crop: str):
    """Fetch current market prices for a specific crop. Use this when the user asks about pricing, selling, or market trends."""
    market_data = {
        "corn": "$4.50 per bushel (Stable)",
        "soybeans": "$12.00 per bushel (Trending Up)",
        "wheat": "$6.00 per bushel (Volatile)",
        "rice": "$15.00 per metric ton (Stable)",
        "coffee": "$180 per bag (Trending Down)"
    }
    crop_lower = crop.lower()
    return market_data.get(crop_lower, f"Market data for {crop} is currently unavailable, but generally trending with global indices.")
