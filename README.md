# Fraud Detection System

This project is a full-stack fraud detection dashboard built with FastAPI, scikit-learn, React, and SQLite by default.

## Structure

```text
/backend
/frontend
docker-compose.yml
```

## Backend

1. Create a Python virtual environment.
2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Train the model once:

```bash
python train.py
```

4. Start the API:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend

Run the app:

```bash
cd frontend
npm run dev
```

This starts a local Python static server on port `5173`.

## API Endpoints

- `POST /predict`
- `POST /train`
- `GET /transactions`
- `GET /health`

## Docker

```bash
docker compose up --build
```

## Notes

- SQLite is used by default for simplicity.
- The backend will try to load a saved model and fall back to training from `backend/data/sample_transactions.csv` if needed.
- The frontend is served directly from `frontend/index.html`, `frontend/app.js`, and `frontend/style.css`.
