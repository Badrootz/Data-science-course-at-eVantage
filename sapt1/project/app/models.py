from typing import Literal
from pydantic import BaseModel, Field

class LoanApplication(BaseModel):
    """
    Pydantic model representing the input loan application details for risk scoring.
    Includes strict validation based on production schema requirements.
    """
    age: int = Field(
        ...,
        ge=18,
        le=69,
        description="Age of the applicant in years. Must be between 18 and 69."
    )
    income: float = Field(
        ...,
        gt=0.0,
        description="Annual income of the applicant. Must be strictly greater than 0."
    )
    loan_amount: float = Field(
        ...,
        gt=0.0,
        description="Requested loan amount. Must be strictly greater than 0."
    )
    credit_score: int = Field(
        ...,
        ge=300,
        le=850,
        description="Credit score of the applicant. Must be between 300 and 850."
    )


class RiskPrediction(BaseModel):
    """
    Pydantic model representing the calculated risk score and risk category.
    """
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calculated risk score, bounded between 0.0 and 1.0 (rounded to 2 decimal places)."
    )
    risk_category: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        ...,
        description="Categorized risk class: LOW (0.0 to 0.3), MEDIUM (0.3 to 0.7), or HIGH (0.7 to 1.0)."
    )
