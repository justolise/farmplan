from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class AgriResponse(BaseModel):
    summary: str = Field(description="A friendly, human-readable introductory sentence.")
    requirements: List[Dict[str, str]] = Field(
        description="A list of requirements, each with a 'category' (e.g., Soil, Water) and 'detail'."
    )
    pro_tip: str = Field(description="A highly actionable, gold-standard piece of advice.")
    alerts: Optional[List[str]] = Field(default=[], description="Any urgent warnings based on weather or market data.")
