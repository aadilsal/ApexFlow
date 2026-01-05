# ApexFlow: F1 Lap-Time Prediction Platform

ApexFlow is a production-grade, end-to-end MLOps platform designed for real-time Formula 1 lap-time prediction. It leverages professional telemetry, automated retraining, and cloud-native orchestration to deliver race-weekend insights.

## 🏎️ Overview

This project implements a full ML lifecycle including:
- **Data Engineering**: DVC-tracked telemetry processing with schema validation.
- **Model Engineering**: XGBoost/LightGBM with Optuna hyperparameter tuning.
- **Automated Retraining**: Weekly retraining with warm-start on new race data via Apache Airflow.
- **Inference Service**: Secure FastAPI service with uncertainty estimation.
- **Live Telemetry & Frontend**: A React/Vite dashboard for real-time race visualization.
- **Observability**: Prometheus/Grafana stack for performance & drift tracking.

## 🛠️ Tech Stack

- **Frontend**: React 19, Vite, TailwindCSS, Recharts, Lucide-React
- **Backend API**: Python 3.10, FastAPI, Uvicorn
- **Orchestration**: Apache Airflow
- **Database**: PostgreSQL (Supabase / Local)
- **Tracking**: MLflow & DagsHub
- **Data Versioning**: DVC
- **Monitoring**: Prometheus + Grafana + Loki
- **Deployment**: Docker, Vercel (Frontend), Render (Backend), Supabase (DB)

## 📁 Repository Structure

```text
.
├── .github/workflows/    # CI/CD pipelines
├── config/               # YAML environment configs
├── dags/                 # Airflow DAGs
├── data/                 # Data samples (versioned by DVC)
├── deploy/               # Cloud Run/K8s manifests
├── docs/                 # Detailed documentation
├── frontend/             # React/Vite Frontend Application
├── monitoring/           # Prometheus/Grafana/Loki configs
├── scripts/              # Utility scripts (Continuous Training, etc.)
├── src/apex_flow/        # Core source code
│   ├── api/              # Prediction API layer
│   ├── data/             # Ingestion & validation
│   ├── modeling/         # Training & versioning
│   ├── monitoring/       # Drift & metrics logic
│   └── orchestration/    # Orchestration logic
└── tests/                # Unit, integration, & quality tests
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ & npm
- Python 3.10+
- **DagsHub Account** (for MLflow/DVC)

### 1. Environment Setup
Create a `.env` file in the root directory:
```ini
# Security
DAGSHUB_USER_TOKEN=your_token_here
APEX_API_KEY=race-weekend-key-2026

# Supabase (Optional)
# VITE_SUPABASE_URL=...
# VITE_SUPABASE_ANON_KEY=...
```

### 2. Run the Full Stack Locally (Docker)
Launch the API, MLflow, Database, and Monitoring stack:
```bash
docker-compose up -d
```

### 3. Run Frontend Locally
```bash
cd frontend
npm install
npm run dev
```
Access the dashboard at `http://localhost:5173`.

### 4. Continuous Training Pipeline
Trigger the automated retraining pipeline (manually or via Airflow):
```bash
# Manual Run
python scripts/continuous_training_pipeline.py

# Airflow
# Enable the 'apexflow_weekly_retraining' DAG
```

## ☁️ Deployment Strategy

We recommend a cost-effective, split deployment strategy:

1.  **Frontend**: Deployed on **Vercel** (connects to `frontend/` directory).
2.  **Backend**: Deployed on **Render** or **Railway** (runs `uvicorn src.apex_flow.api.main:app`).
3.  **Database**: Managed **Supabase** instance (PostgreSQL).
4.  **Orchestration**: Self-hosted Airflow or Cloud Composer (for Weekly Retraining).

> **Important**: Ensure `DAGSHUB_USER_TOKEN` and `APEX_API_KEY` are set in your deployment environment variables.

## 🧰 Scripts

- **Continuous Training**: `python scripts/continuous_training_pipeline.py` - Fetches latest race, retrains model, and promotes if better.
- **Register Model**: `python scripts/register_model.py` - Manual model registration helper.

## 📚 Documentation

For deep dives, troubleshooting, and contributing, see:
- [Architecture & Data Flow](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting Runbooks](docs/troubleshooting.md)

---
*Built with ❤️ for F1 Engineers.*
