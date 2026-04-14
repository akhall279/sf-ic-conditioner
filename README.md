# SF-IC-Conditioner

A template for you test the validity of a signal's disperion as an IC conditioner. (See REPORT.md for more details about the intuition and purpose of this project.)

## Project Structure

```
signal/
│   ├── run_IC_conditioner_regression.py # Test a signal's dispersion as an IC conditioner

```

## Workflow

### Required Columns
date: Date column
barrid: Asset identifier
alpha: Alpha signal values
predicted_beta: Predicted beta values
signal: orignal signal values (name can be changed)


### 1. **Implement Signal** (`create_signal.py`)
   - Customize date ranges, data columns, and calculation logic
   - Develop your signal logic
   - Saves signal to `data/signal.parquet`

   ```bash
   make create-signal
   ```

### 2. **View Equal-Weight Performance** (`ew_dash.py`)
   - Compare your signal against an equal-weight baseline
   - Analyze signal characteristics
   - Visualize signal properties and performance

   ```bash
   make ew-dash
   ```

### 3. **Run Backtest** (`run_backtest.py`)
   - Run MVO-based backtest on your signal
   - Generates optimal portfolio weights
   - Saves results to `data/weights.parquet`

   ```bash
   make run-backtest
   ```

### 4. **View Optimized Performance** (`opt_dash.py`)
   - View optimized portfolio performance
   - Analyze backtest returns, drawdowns, and metrics

   ```bash
   make opt-dash
   ```

## Data Files

All data files are stored in the `data/` directory:

- **`data/signal.parquet`**: Output from `create_signal.py`
  - Columns: `date`, `barrid`, `alpha` (your signal), `signal`
  - Format: Parquet (AlphaSchema)

- **`data/weights/*.parquet`**: Output from backtest
  - Contains: Portfolio weights and performance data
  - Format: Parquet

## Quick Start

```bash
# 1. Implement your signal
# Edit src/signal/create_signal.py with your logic
make create-signal

# 2. View equal-weight performance
make ew-dash

# 3. Run backtest
make run-backtest

# 4. View optimized performance
make opt-dash
```

## Template Files (Do Not Need to Edit)

The following files are templates and should not be modified:
- `src/framework/ew_dash.py` - Equal-weight comparison dashboard
- `src/framework/opt_dash.py` - Optimized portfolio dashboard
- `src/framework/run_backtest.py` - Backtest runner

If you want to edit the marimo notebooks use:
```bash
uv run marimo edit src/framework/{}_dash.py
```

**All signal customization happens in `src/signal/create_signal.py`.**

## Configuration

All configuration is managed through the `.env` file (copied from `.env.example`):

- **`SIGNAL_PATH`**: Where to save your generated signal (relative or absolute path)
- **`WEIGHT_DIR`**: Where backtest results will be saved
- **`LOG_DIR`**: Where backtest logs will be saved
- **`SIGNAL_NAME`**: Name for your signal
- **`GAMMA`**: Risk aversion / transaction cost parameter
- **`EMAIL`**: Your BYU email for job notifications
- **`CONSTRAINTS`**: Portfolio constraints as JSON array (e.g., `["ZeroBeta", "ZeroInvestment"]`)
- **`SLURM_N_CPUS`**: Number of CPU cores for cluster jobs
- **`SLURM_MEM`**: Memory allocation for cluster jobs
- **`SLURM_TIME`**: Time limit for cluster jobs
- **`SLURM_MAIL_TYPE`**: Email notifications (BEGIN, END, FAIL)
- **`SLURM_MAX_CONCURRENT_JOBS`**: Maximum parallel jobs

**Note:** Do not edit `src/framework/run_backtest.py` directly. All configuration comes from `.env`.

## Next Steps

1. Implement your signal logic in `src/signal/create_signal.py`
2. Run `make create-signal` to generate your signal
3. Compare against baseline with `make ew-dash`
4. Run backtest with `make run-backtest`
5. Analyze optimized results with `make opt-dash`
6. Iterate and refine your approach

---

**Note**: This is a template project. Customize `src/signal/create_signal.py` with your unique signal logic, then use the workflow above to backtest your ideas.


