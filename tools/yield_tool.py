import random

from langchain_core.tools import tool


@tool
def predict_crop_yield(crop: str, area: float, health_score: float = 1.0):
    """
    Predict the estimated harvest yield based on crop type, area, and a health score (0.0 to 1.0).
    Use this when the farmer asks 'How much will I harvest?' or 'What is my predicted yield?'.
    """
    # Base yields per acre (simplified)
    base_yields = {
        "corn": 170,      # bushels per acre
        "soybeans": 50,   # bushels per acre
        "wheat": 40,      # bushels per acre
        "rice": 150,      # bushels per acre
    }
    
    crop_lower = crop.lower()
    base = base_yields.get(crop_lower, 100)
    
    # Simple prediction logic: Area * Base * Health
    prediction = area * base * health_score
    
    # Add a small random variance for realism
    variance = prediction * random.uniform(-0.05, 0.05)
    final_yield = prediction + variance
    
    return f"Estimated yield for {crop}: {final_yield:.2f} units. (Based on {area} acres and current health indices)."
