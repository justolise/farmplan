import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    
    # AI Config
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-2.0-flash")
    TEMPERATURE: float = 0.0
    
    # App Config
    APP_NAME: str = "FarmPlan AI Pro"
    DATABASE_URL: str = "sqlite:///./farmplan.db"

    class Config:
        env_file = ".env"

settings = Settings()
