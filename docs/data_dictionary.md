# Data Dictionary & Schema Reference

The following features form the core input for ApexFlow lap-time prediction models.

## Input Features

| Feature Name | Description | Units | Valid Range | Source |
|--------------|-------------|-------|-------------|--------|
| `driver_id` | Unique identifier for the driver | String (HAM, VER) | N/A | Telemetry |
| `circuit_id` | Unique circuit identifier | String (monaco) | N/A | Telemetry |
| `fuel_load` | Current fuel in the tank | Kilograms (kg) | 0.5 - 110.0 | Estimated/Telemetry |
| `tire_compound` | Current tire compound | Enum (SOFT, MED) | SOFT, MEDIUM, HARD | Telemetry |
| `track_temp` | Ambient track surface temperature | Celsius (°C) | 10.0 - 65.0 | Weather Station |
| `session_type` | Type of race session | Enum | FP1, QUALY, RACE | Race Control |
| `lap_number` | Current lap in the session | Integer | 1 - 85 | Telemetry |

## Target Variable

| Feature Name | Description | Units | Target Type |
|--------------|-------------|-------|-------------|
| `lap_time` | Final time for the lap | Seconds (s) | Continuous (Float) |

## Derived Features (Engineering)

- **`tire_age`**: Number of laps since the current set was fitted.
- **`fuel_burn_rate`**: Estimated fuel consumption per lap (derived from historic stints).
- **`track_evolution`**: Normalized improvement factor based on session progression.

## Handling Missing Values

- **Categorical**: Default to "UNKNOWN".
- **Numerical**: Imputed with session-median or rolling-average based on the feature importance.
- **Critical Fields**: If `fuel_load` or `track_temp` are missing, the prediction returns an uncertainty warning.
