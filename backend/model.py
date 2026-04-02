from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


NUMERIC_FEATURES = [
    "amount",
    "frequency_transactions",
    "device_change",
    "location_anomaly",
    "failed_login_attempts",
]

CATEGORICAL_FEATURES = ["location", "device_id", "payment_method"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


@dataclass
class ModelArtifacts:
    pipeline: Pipeline
    metadata: Dict[str, Any]


def _ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def build_pipeline() -> Pipeline:
    try:
        categorical_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        categorical_encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", categorical_encoder),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        sparse_threshold=0.0,
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=4,
        random_state=42,
        class_weight="balanced",
    )

    return Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])


def train_from_dataframe(df: pd.DataFrame) -> ModelArtifacts:
    required = FEATURE_COLUMNS + ["label"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    work_df = df.copy()
    work_df["label"] = work_df["label"].astype(int)

    X = work_df[FEATURE_COLUMNS]
    y = work_df["label"]

    pipeline = build_pipeline()
    pipeline.fit(X, y)

    predicted = pipeline.predict(X)
    probability = pipeline.predict_proba(X)[:, 1]
    metadata = {
        "classification_report": classification_report(y, predicted, zero_division=0),
        "roc_auc": float(roc_auc_score(y, probability)) if len(set(y)) > 1 else 0.0,
        "training_rows": int(len(work_df)),
    }

    return ModelArtifacts(pipeline=pipeline, metadata=metadata)


def save_model(artifacts: ModelArtifacts, model_path: str) -> None:
    _ensure_parent(model_path)
    joblib.dump(artifacts, model_path)


def load_model(model_path: str) -> ModelArtifacts | None:
    if not os.path.exists(model_path):
        return None
    loaded = joblib.load(model_path)
    if isinstance(loaded, ModelArtifacts):
        return loaded
    if isinstance(loaded, dict) and "pipeline" in loaded:
        return ModelArtifacts(pipeline=loaded["pipeline"], metadata=loaded.get("metadata", {}))
    return ModelArtifacts(pipeline=loaded, metadata={})


def predict_probability(artifacts: ModelArtifacts, features: pd.DataFrame) -> float:
    if not hasattr(artifacts.pipeline, "predict_proba"):
        raise ValueError("Loaded model does not support probability predictions")
    proba = artifacts.pipeline.predict_proba(features)[0]
    classes = list(getattr(artifacts.pipeline.named_steps["model"], "classes_", []))
    if len(classes) == 2 and 1 in classes:
        fraud_index = classes.index(1)
        return float(proba[fraud_index])
    if len(proba) > 1:
        return float(proba[-1])
    return float(proba[0])


def to_feature_frame(payload: Dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame([payload], columns=FEATURE_COLUMNS)
