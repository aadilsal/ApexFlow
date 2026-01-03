# Model Architecture & Training Guide

This guide explains the machine learning methodology behind ApexFlow predictions.

## Model Selection

ApexFlow uses **Gradient Boosted Decision Trees (GBDT)** via **XGBoost** as the primary estimator. 

### Rationale:
- **Tabular Superiority**: GBDTs consistently outperform deep learning on structured telemetry data.
- **Explainability**: Feature importance helps race engineers understand drivers of lap time variation.
- **Efficiency**: Training and inference are fast enough for live race-weekend cycles.

## Training Pipeline Flow

1. **Preprocessing**: Scaling fuel load, ordinal encoding for tires, and handling session-specific biases.
2. **Hyperparameter Tuning**: **Optuna** uses Bayesian optimization (TPE) to find optimal shrinkage, depth, and regularization.
3. **Cross-Validation**: 5-fold Time-Series split to avoid temporal data leakage.
4. **Validation**: Comparison against the "Champion" model using a paired t-test on a 20% holdout set.

## Incremental Learning Strategy

To adapt to track evolution during a race weekend:
- The system supports **Warm Start** training.
- We load the latest stable booster weights and train on the last 2 sessions of data with a low learning rate.
- This allows the model to "learn" the specific track grip levels without forgetting seasonal patterns.

## Known Assumptions & Limitations

- **Dry Track Dominance**: The model is currently optimized for dry conditions. Performance degrades significantly during transition/wet sessions.
- **Traffic Neglect**: Latent traffic factors (blue flags, overtaking) are not currently explicit features.
- **Constant Fuel burn**: Fuel burn is assumed linear unless modified by telemetry-derived coefficients.
