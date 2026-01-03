# ApexFlow: F1 Lap-Time Prediction Platform

ApexFlow is a production-grade, end-to-end MLOps platform designed for real-time Formula 1 lap-time prediction. It leverages professional telemetry, automated retraining, and cloud-native orchestration to deliver race-weekend insights.

## 🏎️ Overview

This project implements a full ML lifecycle including:
- **Data Engineering**: DVC-tracked telemetry processing with schema validation.
- **Model Engineering**: XGBoost/LightGBM with Optuna hyperparameter tuning.
- **Automated Retraining**: Drift-triggered incremental learning.
- **Inference Service**: Secure FastAPI service with uncertainty estimation.
- **Live Telemetry & Frontend**: A React/Vite dashboard for real-time race visualization.
- **Observability**: Prometheus/Grafana stack for performance & drift tracking.

## 🛠️ Tech Stack

- **Frontend**: React 19, Vite, TailwindCSS, Recharts, Lucide-React
- **Backend API**: Python 3.10, FastAPI, Uvicorn
- **Database**: PostgreSQL (Supabase / Local)
- **Tracking**: MLflow
- **Data Versioning**: DVC
- **Monitoring**: Prometheus + Grafana + Loki
- **Deployment**: Docker, Vercel (Frontend), Render (Backend), Supabase (DB)

## 📁 Repository Structure

```text
.
├── .github/workflows/    # CI/CD pipelines
├── config/               # YAML environment configs
├── data/                 # Data samples (versioned by DVC)
├── deploy/               # Cloud Run/K8s manifests
├── docs/                 # Detailed documentation
├── frontend/             # React/Vite Frontend Application
├── monitoring/           # Prometheus/Grafana/Loki configs
├── scripts/              # Utility scripts (e.g., remove_comments.py)
├── src/apex_flow/        # Core source code
│   ├── api/              # Prediction API layer
│   ├── data/             # Ingestion & validation
│   ├── modeling/         # Training & versioning
│   ├── monitoring/       # Drift & metrics logic
│   └── orchestration/    # Prefect retraining flows
└── tests/                # Unit, integration, & quality tests
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ & npm
- Python 3.10+

### 1. Run the Full Stack Locally (Docker)
Launch the API, MLflow, Database, and Monitoring stack:
```bash
docker-compose up -d
```

### 2. Run Frontend Locally
```bash
cd frontend
npm install
npm run dev
```
Access the dashboard at `http://localhost:5173`.

### 3. Get a Prediction (API)
```bash
curl -X POST "http://localhost:8000/v1/predict" \
     -H "X-Apex-Key: race-weekend-key-2026" \
     -H "Content-Type: application/json" \
     -d '{
       "driver_id": "HAM",
       "circuit_id": "monaco",
       "fuel_load": 50.0,
       "tire_compound": "SOFT",
       "track_temp": 35.5,
       "session_type": "RACE"
     }'
```

## ☁️ Deployment Strategy

We recommend a cost-effective, split deployment strategy:

1.  **Frontend**: Deployed on **Vercel** (connects to `frontend/` directory).
2.  **Backend**: Deployed on **Render** or **Railway** (runs `uvicorn src.apex_flow.api.main:app`).
3.  **Database**: Managed **Supabase** instance (PostgreSQL).

Refer to `docs/deployment.md` or `deployment_strategy.md` (artifact) for detailed steps.

## 🧰 Scripts

- **Remove Comments**: `python scripts/remove_comments.py` - Recursively removes comments from code files for cleaner distribution.

## 📚 Documentation

For deep dives, troubleshooting, and contributing, see:
- [Architecture & Data Flow](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting Runbooks](docs/troubleshooting.md)

---
*Built with ❤️ for F1 Engineers.*
