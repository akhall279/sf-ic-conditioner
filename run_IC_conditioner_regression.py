import sf_quant.data as sfd
import polars as pl
import pandas as pd
import statsmodels.api as sm
import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

# Provide your datafiles and initialize variables here
@dataclass
class Config:
    # Provide the paths to your exposure files, your alpha file, and your score file
    exposures_glob: str = "exposures/exposures_*.parquet"
    alphas_path:    str = "alphas/alphas.parquet"
    scores_path:    str = "scores/scores.parquet"

    # Pick the start and end date for your data
    start_date: dt.date = dt.date(1995, 1, 1)
    end_date:   dt.date = dt.date(2026, 2, 28)

    # Pick the span for your exponentially weighted moving statsitics
    ewm_span: int = 20

    # If you have any signals if your alpha/score files that you don't want to use, put them here
    signals_to_exclude: list[str] = field(default_factory=lambda: [
        "ivol", "barra_momentum", "barra_reversal", "beta"
    ])

    # If your exposure files have style factors, drop them here
    style_cols_to_drop: list[str] = field(default_factory=lambda: [
        "USSLOWL_DIVYILD", "USSLOWL_EARNQLTY", "USSLOWL_EARNYILD",
        "USSLOWL_GROWTH",  "USSLOWL_LEVERAGE", "USSLOWL_LIQUIDTY",
        "USSLOWL_LTREVRSL","USSLOWL_MIDCAP",   "USSLOWL_MOMENTUM",
        "USSLOWL_PROFIT",  "USSLOWL_PSNLPROD", "USSLOWL_SIZE",
        "USSLOWL_VALUE",   "USSLOWL_SPLTYRET", "USSLOWL_BETA",
        "USSLOWL_MGMTQLTY","USSLOWL_RESVOL",   "USSLOWL_COUNTRY",
    ])

# Regression for IC_conditioner, will be used later on in main()
def run_regression(sub_df):
    # Get rid of nulls, nans, and infinite values
    sub_df = sub_df.drop_nulls(subset=['alpha', 'interaction_coeff', 'return_forward'])
    sub_df = sub_df.drop_nans( subset=['alpha', 'interaction_coeff', 'return_forward'])
    sub_df = sub_df.filter(
        pl.col('alpha').is_finite() &
        pl.col('interaction_coeff').is_finite() &
        pl.col('return_forward').is_finite()
    )

    # Set your independent variables as alpha and interaction_coeff (the IC conditioner)
    X = sm.add_constant(sub_df.select(['alpha', 'interaction_coeff']).to_pandas().astype('float32'), has_constant='add')
    # Set your dependent variable as forward returns
    y = sub_df['return_forward'].to_pandas().astype('float32')
    # Accounts for cross-sectional correlation (the fact that returns on the same date move together)
    model = sm.OLS(y, X).fit(cov_type='cluster', cov_kwds={'groups': sub_df['date'].to_pandas()})

    # Return coefficients, t-stats, p-values, and R-squared
    return {
        'intercept': model.params['const'],           'intercept_t': model.tvalues['const'],       'intercept_p': model.pvalues['const'],
        'alpha_coef': model.params['alpha'],           'alpha_t':     model.tvalues['alpha'],       'alpha_p':     model.pvalues['alpha'],
        'interaction_coef': model.params['interaction_coeff'],  'interaction_t': model.tvalues['interaction_coeff'],  'interaction_p': model.pvalues['interaction_coeff'],
        'r2': model.rsquared,
    }


def main():
    # Import your tables and variables
    cfg = Config()

    # Checks to see if any files are missing
    missing = [p for p in [cfg.alphas_path, cfg.scores_path] if not Path(p).exists()]
    if missing:
        raise FileNotFoundError(f"Missing input files: {missing}")

    # exposures should have 'date', 'barrid', various style exposure, and various industry exposure columns
    exposures = pl.scan_parquet(cfg.exposures_glob)
    # alphas should have 'date', 'barrid', 'signal_name', and 'alpha' columns
    alphas    = pl.scan_parquet(cfg.alphas_path)
    # scores should have 'date', 'barrid', 'signal_name', and 'score' columns
    scores    = pl.scan_parquet(cfg.scores_path)

    # Drop the style factors
    exposures = exposures.drop(cfg.style_cols_to_drop, strict=False)
    # Create list of industries from exposures table (excludes date and barrid and includes everything else)
    industry_cols = [c for c in exposures.collect_schema().names() if c not in ('date', 'barrid')]

    # Finds the maximum exposure WEIGHT for each asset
    exposures = exposures.with_columns(row_max=pl.max_horizontal(industry_cols))

    # Gets the LABEL of the maximum industry for each asset
    argmax_expr = pl.lit(None)
    for col in industry_cols:
        argmax_expr = pl.when(pl.col(col) == pl.col("row_max")).then(pl.lit(col)).otherwise(argmax_expr)

    # Filter out assets with no industry exposures
    exposures = (
        exposures
        .with_columns(industry_label=argmax_expr)
        .filter(~pl.all_horizontal(pl.col(industry_cols).is_null()))
        .collect()
    )

    # Join the alpha and score tables to the exposures table, collect the lazy dataframe
    df = (
        exposures.lazy()
        .join(alphas, on=['barrid', 'date'], how='inner')
        .join(scores, on=['barrid', 'date', 'signal_name'], how='inner')
        .filter(~pl.col('signal_name').is_in(cfg.signals_to_exclude))
        .drop(industry_cols, strict=False)
        .collect()
    )

    # Calculate industry standard deviation: std of scores within the same industry, grouped by signal and date
    indus_std_df = (
        df.lazy()
        .select(['signal_name', 'date', 'industry_label', 'score'])
        .group_by(['signal_name', 'date', 'industry_label'])
        .agg(pl.col('score').std().alias('indus_std'))
        .sort(['signal_name', 'date'])
    )

    # Calculate cross-industry standard deviation: take an equal-weighted average of industry std for each signal/date combo
    # Also calculate the ewm average and ewm std of cross-industry std to use for normalization later
    cross_industry_std_df = (
        indus_std_df
        .select(['signal_name', 'date', 'indus_std'])
        .group_by(['signal_name', 'date'])
        .agg(pl.col('indus_std').mean().alias('cross_industry_std'))
        .sort(['signal_name', 'date'])
        .with_columns(
            score_ewmmean=pl.col("cross_industry_std").ewm_mean(span=cfg.ewm_span, adjust=False).over(['signal_name']),
            score_ewmstd =pl.col("cross_industry_std").ewm_std( span=cfg.ewm_span, adjust=False).over(['signal_name']),
        )
        .collect()
    )

    # Join original dataframe with cross-industry std
    # Calculate the IC conditioner as normalized cross-industry std
    # Calculate the interaction coefficient (interaction_coeff) as product of alpha and IC conditioner
    df = (
        df.join(cross_industry_std_df, on=['signal_name', 'date'], how='inner')
        .with_columns(
            IC_conditioner=(pl.col('cross_industry_std') - pl.col('score_ewmmean')) / pl.col('score_ewmstd')
        )
        .with_columns(
            interaction_coeff=pl.col('alpha') * pl.col('IC_conditioner')
        )
    )

    # Load returns from sfd package
    # Shift returns forward by one period to get next-period (forward) returns
    df_ret = (
        sfd.load_assets(
            start=cfg.start_date, end=cfg.end_date,
            in_universe=True, columns=["barrid", "date", "return"]
        )
        .sort(['barrid', 'date'])
        .with_columns(return_forward=pl.col("return").shift(-1).over("barrid"))
    )

    # Join original dataframe with forward returns
    df_merged = df.join(df_ret, on=['barrid', 'date'], how='inner')

    # Partition data into per-signal groups
    signal_groups = df_merged.partition_by('signal_name', as_dict=True)

    # Create a dataframe of your regression results
    results = pd.DataFrame([
        {'signal_name': sig, **run_regression(group)}
        for sig, group in signal_groups.items()
    ])

    # Display your results
    pd.set_option('display.max_columns', None)
    print(results)

if __name__ == "__main__":
    main()