"""Phase 2 orchestrator: weather adjust, seasonal adjust, standardize."""

import logging

from src.config import DATA_PROCESSED

from .weather import weather_adjust
from .seasonal import seasonal_adjust, standardize

logger = logging.getLogger("zeus.signal.pipeline")

EXPECTED_COLS = [
    "state", "period",
    "sales_res", "sales_com", "sales_ind",
    "price_res", "price_com", "price_ind",
    "hdd", "cdd", "coincident_index",
    "resid_res", "resid_com", "resid_ind",
    "signal_res", "signal_com", "signal_ind",
]


def extract_signal(df):
    """Run the full Phase 2 signal extraction pipeline.

    1. OLS weather/price regression → residuals
    2. STL seasonal decomposition → deseasonalized
    3. Z-score standardization → signals
    4. Drop intermediate columns, save panel_signal.parquet
    """
    df = weather_adjust(df)
    df = seasonal_adjust(df)
    df = standardize(df)

    # Drop intermediate deseason columns
    df = df.drop(columns=["deseason_res", "deseason_com", "deseason_ind"])

    # Verify output
    assert len(df.columns) == 17, f"Expected 17 columns, got {len(df.columns)}"
    for col in EXPECTED_COLS:
        assert col in df.columns, f"Missing column: {col}"

    # Save
    out_path = DATA_PROCESSED / "panel_signal.parquet"
    df.to_parquet(out_path, index=False)
    logger.info("Saved signal panel to %s", out_path)
    logger.info("Shape: %s", df.shape)
    logger.info("NaN overview:\n%s", df.isna().sum().to_string())

    return df
