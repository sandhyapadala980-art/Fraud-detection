from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from .model import ModelArtifacts, save_model, train_from_dataframe
except ImportError:
    from model import ModelArtifacts, save_model, train_from_dataframe


def load_dataset(dataset_path: str) -> pd.DataFrame:
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    return pd.read_csv(path)


def train_and_save(dataset_path: str, model_path: str) -> ModelArtifacts:
    dataframe = load_dataset(dataset_path)
    artifacts = train_from_dataframe(dataframe)
    save_model(artifacts, model_path)
    return artifacts


if __name__ == "__main__":
    import os

    dataset_path = os.getenv("DATASET_PATH", "./data/sample_transactions.csv")
    model_path = os.getenv("MODEL_PATH", "./artifacts/fraud_model.joblib")
    trained = train_and_save(dataset_path, model_path)
    print("Training complete")
    print(trained.metadata.get("classification_report", ""))
