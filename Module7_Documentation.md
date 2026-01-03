# Module 7: Automated Retraining Pipeline Documentation

## Overview
The Automated Retraining Pipeline is a self-healing system designed to detect model drift, retrain models using warm-start strategies, validate improvements against production baselines, and safely deploy or roll back models without human intervention.

## Component Guide

### 1. Drift Listener (`apex_flow.monitoring.drift_listener`)
- **Purpose**: Consumes alerts from the drift detector.
- **Logic**: Implements debouncing (preventing rapid-fire triggers for the same event) and cooldown periods.
- **Queueing**: Enqueues valid triggers into the Resource Manager.

### 2. Data Readiness (`apex_flow.data.readiness`)
- **Purpose**: Ensures data integrity before training.
- **Logic**: Checks `dvc status` for completeness and validates CSV schemas and session records.

### 3. Model Trainer (`apex_flow.modeling.trainer`)
- **Purpose**: Handles model training.
- **Logic**: Supports `warm_start` for incremental learning using previous booster weights. Falls back to full training if no baseline exists.

### 4. Resource Manager (`apex_flow.resource_manager`)
- **Purpose**: Manages compute resources.
- **Logic**: Implements a priority queue and checks CPU/Memory usage before launching jobs.

### 5. Validation & Comparison (`apex_flow.validation`)
- **Gate**: Statistical significance testing using paired t-tests. Rejects models showing regression.
- **Comparator**: Compares candidate vs. production performance. Promotion occurs only if improvement exceeds the threshold.

### 6. Rollback & Safety (`apex_flow.deployment.rollback`)
- **Purpose**: Ensures stability.
- **Logic**: Persists the last known "Stable" model run ID. Automatically rolls back to this version if a new deployment fails validation.

## Configuration (`config/retraining.yaml`)
Key parameters include:
- `severity_threshold`: Minimum drift score to trigger retraining.
- `debounce_seconds`: Time to ignore repeat alerts.
- `max_weekend_retrains`: Cap on computational cost during race events.
- `improvement_threshold`: Minimum gain required for promotion.

## Failure Modes & Recovery
| Failure Mode | Detection | Recovery Action |
|--------------|-----------|-----------------|
| Data Missing | Data Readiness Check | Skips job, notifies via logs/webhook |
| High Resource Usage | Resource Manager | Re-queues job for later execution |
| Model Regression | Validation Gate | Rejects model, keeps production version |
| Deployment Error | Rollback Mechanism | Automatically reverts to last stable MLflow run |

## Orchestration
The pipeline is orchestrated using **Prefect** (`src/apex_flow/orchestration/prefect_flow.py`). It can be triggered programmatically or via CLI.
