from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TransactionInput(BaseModel):
    user_id: int = Field(ge=1)
    amount: float = Field(gt=0)
    location: str = Field(min_length=2, max_length=120)
    device_id: str = Field(min_length=2, max_length=120)
    payment_method: str = Field(min_length=2, max_length=80)
    failed_login_attempts: int = Field(default=0, ge=0, le=20)


class PredictionResponse(BaseModel):
    risk_score: int
    classification: str
    risk_factors: List[str]
    fraud_probability: float


class TrainRequest(BaseModel):
    dataset_path: Optional[str] = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    amount: float
    location: str
    device_id: str
    payment_method: str
    prediction: str
    classification: str
    risk_score: int
    risk_factors: List[str]
    fraud_probability: float
    created_at: datetime
