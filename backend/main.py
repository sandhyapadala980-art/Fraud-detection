from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

try:
    from .database import TransactionRecord, create_tables, get_db
    from .model import ModelArtifacts, load_model, predict_probability, to_feature_frame
    from .schemas import PredictionResponse, TrainRequest, TransactionInput, TransactionOut
    from .train import train_and_save
except ImportError:
    from database import TransactionRecord, create_tables, get_db
    from model import ModelArtifacts, load_model, predict_probability, to_feature_frame
    from schemas import PredictionResponse, TrainRequest, TransactionInput, TransactionOut
    from train import train_and_save


APP_TITLE = "Fraud Detection System"
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = Path(os.getenv("DATASET_PATH", str(BASE_DIR / "data" / "sample_transactions.csv")))
MODEL_PATH = Path(os.getenv("MODEL_PATH", "/tmp/fraud_model.joblib"))
ALLOW_MODEL_PERSISTENCE = os.getenv("ALLOW_MODEL_PERSISTENCE", "false").lower() == "true"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
]

app = FastAPI(title=APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_artifacts: ModelArtifacts | None = None


def _classification_from_score(risk_score: int) -> str:
    if risk_score <= 30:
        return "Legitimate"
    if risk_score <= 70:
        return "Suspicious"
    return "Fraud"


def _derive_risk_factors(
    transaction: TransactionInput,
    frequency_transactions: int,
    device_change: int,
    location_anomaly: int,
) -> List[str]:
    factors: List[str] = []
    if transaction.amount >= 1000:
        factors.append("High transaction amount")
    if frequency_transactions >= 5:
        factors.append("High transaction frequency")
    if device_change:
        factors.append("Device changed from previous transaction")
    if location_anomaly:
        factors.append("Location differs from recent activity")
    if transaction.failed_login_attempts >= 3:
        factors.append("Multiple failed login attempts")
    if transaction.payment_method.lower() in {"crypto", "wire_transfer"}:
        factors.append("Higher-risk payment method")
    return factors or ["No strong risk indicators detected"]


def _recent_transactions(db: Session, user_id: int) -> List[TransactionRecord]:
    cutoff = datetime.utcnow() - timedelta(days=1)
    return (
        db.query(TransactionRecord)
        .filter(TransactionRecord.user_id == user_id)
        .filter(TransactionRecord.created_at >= cutoff)
        .order_by(TransactionRecord.created_at.desc())
        .all()
    )


def _build_feature_payload(db: Session, transaction: TransactionInput) -> Dict[str, object]:
    recent = _recent_transactions(db, transaction.user_id)
    frequency_transactions = max(1, len(recent) + 1)
    previous = recent[0] if recent else None
    device_change = 1 if previous and previous.device_id != transaction.device_id else 0
    location_anomaly = 1 if previous and previous.location.lower() != transaction.location.lower() else 0

    return {
        "amount": transaction.amount,
        "frequency_transactions": frequency_transactions,
        "device_change": device_change,
        "location_anomaly": location_anomaly,
        "failed_login_attempts": transaction.failed_login_attempts,
        "location": transaction.location,
        "device_id": transaction.device_id,
        "payment_method": transaction.payment_method,
    }


def _classify_probability(probability: float) -> Tuple[int, str]:
    risk_score = max(0, min(100, int(round(probability * 100))))
    return risk_score, _classification_from_score(risk_score)


def _ensure_model_loaded() -> ModelArtifacts:
    global model_artifacts
    if model_artifacts is None:
        try:
            model_artifacts = load_model(str(MODEL_PATH))
        except Exception:
            model_artifacts = None
    if model_artifacts is None:
        if not DATASET_PATH.exists():
            raise HTTPException(status_code=503, detail="Model is not trained yet")
        try:
            data = pd.read_csv(DATASET_PATH)
            from .model import train_from_dataframe, save_model

            model_artifacts = train_from_dataframe(data)
            if ALLOW_MODEL_PERSISTENCE:
                try:
                    save_model(model_artifacts, str(MODEL_PATH))
                except Exception:
                    pass
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Unable to load or train model: {exc}") from exc
    return model_artifacts


@app.on_event("startup")
def startup_event() -> None:
    create_tables()
    try:
        _ensure_model_loaded()
    except Exception:
        pass


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "message": "Fraud Detection API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/predict", response_model=PredictionResponse)
def predict_transaction(transaction: TransactionInput, db: Session = Depends(get_db)) -> PredictionResponse:
    artifacts = _ensure_model_loaded()
    feature_payload = _build_feature_payload(db, transaction)
    features = to_feature_frame(feature_payload)

    try:
        fraud_probability = predict_probability(artifacts, features)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    risk_score, classification = _classify_probability(fraud_probability)
    risk_factors = _derive_risk_factors(
        transaction,
        int(feature_payload["frequency_transactions"]),
        int(feature_payload["device_change"]),
        int(feature_payload["location_anomaly"]),
    )

    record = TransactionRecord(
        user_id=transaction.user_id,
        amount=transaction.amount,
        location=transaction.location,
        device_id=transaction.device_id,
        payment_method=transaction.payment_method,
        prediction=classification,
        classification=classification,
        risk_score=risk_score,
        risk_factors=risk_factors,
        fraud_probability=fraud_probability,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return PredictionResponse(
        risk_score=risk_score,
        classification=classification,
        risk_factors=risk_factors,
        fraud_probability=round(fraud_probability, 4),
    )


@app.post("/train")
def train_model(payload: TrainRequest | None = None) -> Dict[str, object]:
    global model_artifacts
    dataset_path = Path(payload.dataset_path) if payload and payload.dataset_path else DATASET_PATH
    if not dataset_path.exists():
        raise HTTPException(status_code=400, detail=f"Dataset not found: {dataset_path}")
    try:
        data = pd.read_csv(dataset_path)
        from .model import train_from_dataframe, save_model

        artifacts = train_from_dataframe(data)
        if ALLOW_MODEL_PERSISTENCE:
            try:
                save_model(artifacts, str(MODEL_PATH))
            except Exception:
                pass
        model_artifacts = artifacts
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Training failed: {exc}") from exc
    return {
        "message": "Model trained successfully",
        "metadata": model_artifacts.metadata,
    }


@app.get("/transactions", response_model=list[TransactionOut])
def list_transactions(db: Session = Depends(get_db)) -> List[TransactionOut]:
    rows = db.query(TransactionRecord).order_by(TransactionRecord.created_at.desc()).limit(100).all()
    return rows
