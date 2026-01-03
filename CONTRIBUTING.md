# Contributing to ApexFlow

Welcome! We are excited you want to help build the future of F1 lap-time prediction.

## Standards & Practices

- **Python**: Follow PEP 8. Use `pytest` for all new features.
- **Typing**: Use strong typing for all function signatures.
- **Documentation**: Update the `Data Dictionary` if you add features. Update `Troubleshooting` if you find a new edge case.

## Development Workflow

1. **Feature Engineering**:
   - Add your logic to `src/apex_flow/data/`.
   - Ensure the transformation is deterministic.
   - Run `pytest tests/features/` to verify.

2. **Training New Models**:
   - Use the `ModelTrainer` in `src/apex_flow/modeling/`.
   - Log all experiments to **MLflow**.
   - Compare results using the `PerformanceComparator`.

3. **API Changes**:
   - Update **Pydantic** schemas in `src/apex_flow/api/schemas.py`.
   - Add instrumentation metrics if the endpoint adds new dimensions (circuit, driver).

## Commit Convention

We use semantic commit messages:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `chore`: Updating build tasks, dependencies, etc.

## Promoting to Production

- Never push directly to `main`.
- Create a Pull Request (PR).
- The CI/CD pipeline must turn green.
- A teammate must review the **MLflow metrics** and the code.
