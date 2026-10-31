import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    
    # AI Config
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-2.0-flash")
    TEMPERATURE: float = 0.0
    
    # App Config
    APP_NAME: str = "FarmPlan AI Pro"
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

    class Config:
        env_file = ".env"

settings = Settings()
