# Glossary of Terms

Aligning terminology across F1 Engineers, Data Scientists, and MLOps Engineers.

## Formula 1 Domain

| Term | Definition |
|------|------------|
| **Stint** | A period of time a car spends on track between two pit stops. |
| **Sectors** | The three distinct parts of a race track used for timing (Sector 1, 2, 3). |
| **Compounds** | The specific type of rubber used for tires (SOFT, MEDIUM, HARD). |
| **Parc Fermé** | A secure area where cars are kept before the race; no major changes allowed. |
| **Track Evolution** | The process where a track gets faster as more rubber is laid down (grip increases). |

## Machine Learning Domain

| Term | Definition |
|------|------------|
| **Data Drift** | Change in the distribution of input data (e.g., track temp spikes). |
| **Concept Drift** | Change in the relationship between input and target (e.g., a car upgrade changes its pace). |
| **Data Leakage** | When information from the future is accidentally used to train the model. |
| **Paired T-Test** | Statistical test used to compare the performance of two models on the same data. |

## MLOps & Platform Domain

| Term | Definition |
|------|------------|
| **Champion/Challenger** | Pattern where a production model (Champion) is compared against a new model (Challenger). |
| **Lineage** | The record of where data came from and how it evolved into a specific model. |
| **Rollback** | Reverting to a previous stable model version in the event of a failure. |
| **Observability** | The ability to understand the internal state of a system from its external outputs (metrics, logs). |
