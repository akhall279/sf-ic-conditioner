# SF-IC-Conditioner

A template for you test the validity of a signal's disperion as an IC conditioner. (See REPORT.md for more details about the intuition and purpose of this project.)

## Project Structure

```
signal/
│   ├── run_IC_conditioner_regression.py # Test a signal's dispersion as an IC conditioner

```

## Workflow

### 1. **Test dispersion of one or more signals as a valid predictor of IC** (`create_signal.py`)
   - Input your exposures data and the scores and alphas for any signal you want to test as an IC conditioner.
   - Run the Python file and check the statistical significance of your interaction coefficient.

## Data Files You Will Need

- **`exposures/exposures_*.parquet`**:
  - Columns: 'date', 'barrid', style exposures, and industry exposures
  - Format: Parquet (AlphaSchema)

- **`alphas/alphas.parquet`**:
  - Columns: 'date', 'barrid', 'signal_name', and 'alpha'
  - Format: Parquet

- **`scores/scores.parquet`**:
  - Columns: 'date', 'barrid', 'signal_name', and 'score'
  - Format: Parquet

---
