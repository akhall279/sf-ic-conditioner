# SF-IC-Conditioner

A template for you test the validity of a signal's disperion as an IC conditioner. (See REPORT.md for more details about the intuition and purpose of this project.)

## Project Structure

```
signal/
│   ├── run_IC_conditioner_regression.py # Test a signal's dispersion as an IC conditioner

```

## Workflow

### 1. **Test dispersion of one or more signals as a valid predictor of IC** (`create_signal.py`)
   - Input your 

## Data Files

All data files are stored in the `data/` directory:

- **`data/signal.parquet`**: Output from `create_signal.py`
  - Columns: `date`, `barrid`, `alpha` (your signal), `signal`
  - Format: Parquet (AlphaSchema)

- **`data/weights/*.parquet`**: Output from backtest
  - Contains: Portfolio weights and performance data
  - Format: Parquet

---

**Note**: This is a template project. Customize `src/signal/create_signal.py` with your unique signal logic, then use the workflow above to backtest your ideas.


