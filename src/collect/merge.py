"""Merge EIA, FRED, and NOAA data into a single panel dataset."""

import logging

import pandas as pd

from src.config import DATA_PROCESSED

logger = logging.getLogger(__name__)

PANEL_PATH = DATA_PROCESSED / "panel.parquet"


def merge_panel(
    eia_df: pd.DataFrame,
    fred_df: pd.DataFrame,
    noaa_df: pd.DataFrame,
) -> pd.DataFrame:
    """Join all sources on (state, period) and save as parquet."""

    # --- Pivot EIA from long (one row per sector) to wide ---
    eia_wide = eia_df.pivot_table(
        index=["state", "period"],
        columns="sector",
        values=["sales_mwh", "price_cents_kwh"],
        aggfunc="first",
    )
    # Flatten MultiIndex columns: ('sales_mwh', 'RES') -> 'sales_res'
    eia_wide.columns = [
        f"{metric.split('_')[0]}_{sector.lower()}"
        for metric, sector in eia_wide.columns
    ]
    eia_wide.reset_index(inplace=True)

    # --- Outer joins ---
    panel = eia_wide.merge(fred_df, on=["state", "period"], how="outer")
    panel = panel.merge(noaa_df, on=["state", "period"], how="outer")

    panel.sort_values(["state", "period"], inplace=True)
    panel.reset_index(drop=True, inplace=True)

    # --- Merge diagnostics ---
    logger.info("--- Merge Diagnostics ---")
    logger.info("EIA pivoted: %d rows", len(eia_wide))
    logger.info("FRED:        %d rows", len(fred_df))
    logger.info("NOAA:        %d rows", len(noaa_df))
    logger.info("Merged:      %d rows", len(panel))
    logger.info("States: %d", panel["state"].nunique())
    logger.info("Periods: %d", panel["period"].nunique())

    nan_counts = panel.isna().sum()
    nan_pct = (nan_counts / len(panel) * 100).round(1)
    for col in panel.columns:
        if nan_counts[col] > 0:
            logger.info(
                "  NaN in %-20s: %5d (%4.1f%%)", col, nan_counts[col], nan_pct[col]
            )

    # --- Save ---
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(PANEL_PATH, index=False)
    logger.info("Saved panel to %s", PANEL_PATH)

    return panel
