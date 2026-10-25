import os
import requests
from langchain_core.tools import tool

@tool
def get_weather_forecast(location: str):
    """Fetch current weather and forecast for a given location. Use this whenever the user asks about weather, planting times, or irrigation."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Weather API key not configured. Please set OPENWEATHER_API_KEY."
    
    try:
        # Get coordinates for the location
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={api_key}"
        geo_resp = requests.get(geo_url).json()
        if not geo_resp:
            return f"Could not find location {location}."
        
        lat, lon = geo_resp[0]['lat'], geo_resp[0]['lon']
        
        # Get 5 day forecast
        weather_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        weather_resp = requests.get(weather_url).json()
        
        forecasts = []
        for f in weather_resp['list'][:5]:
            forecasts.append(f"{f['dt_txt']}: {f['main']['temp']}°C, {f['weather'][0]['description']}")
        
        return "\n".join(forecasts)
    except Exception as e:
        return f"Error fetching weather: {str(e)}"
