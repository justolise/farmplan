
from pydantic import BaseModel, Field, field_validator

class AgriResponse(BaseModel):
    summary: str = Field(description="A friendly, human-readable introductory sentence.")
    requirements: list[dict[str, str]] = Field(
        description="A list of requirements, each with a 'category' (e.g., Soil, Water) and 'detail'."
    )
    pro_tip: str = Field(description="A highly actionable, gold-standard piece of advice.")
    alerts: list[str] | None = Field(default=[], description="Any urgent warnings based on weather or market data.")
    confidence_score: float = Field(
        description="A score from 0.0 to 1.0 indicating confidence in the advice based on data consistency. 1.0 = High, <0.7 = Conflicting data/Uncertain."
    )
    verification_status: str = Field(
        description="Explanation of what was verified (e.g., 'Weather checked, no rain forecast for 48h')."
    )

    @field_validator('requirements')
    @classmethod
    def validate_requirements_not_vague(cls, v):
        if not v:
            raise ValueError("Requirements cannot be empty. Provide at least one actionable step.")
        for req in v:
            detail = req.get('detail', '').lower()
            if len(detail) < 10 or any(word in detail for word in ["some", "etc", "maybe", "possibly"]):
                raise ValueError(f"Requirement detail is too vague: '{detail}'. Provide specific quantities or actions.")
        return v

    @field_validator('pro_tip')
    @classmethod
    def validate_pro_tip_substantial(cls, v):
        if len(v) < 20:
            raise ValueError("Pro-tip is too short. Provide a substantial, gold-standard piece of advice.")
        return v
