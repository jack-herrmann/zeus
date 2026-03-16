"""Step 2: STL seasonal decomposition. Step 3: z-score standardization."""

import logging

import pandas as pd
from statsmodels.tsa.seasonal import STL

logger = logging.getLogger("zeus.signal.seasonal")

STL_PERIOD = 12
STL_SEASONAL = 13
STL_ROBUST = True
SECTOR_KEYS = ["res", "com", "ind"]


def seasonal_adjust(df: pd.DataFrame) -> pd.DataFrame:
    """Apply STL decomposition to weather-adjusted residuals.

    Extracts trend + remainder (strips seasonal component).
    Returns df with deseason_res, deseason_com, deseason_ind added.
    """
    df = df.copy()
    for sector in SECTOR_KEYS:
        df[f"deseason_{sector}"] = float("nan")

    n_decomposed = 0

    for state, group in df.groupby("state"):
        for sector in SECTOR_KEYS:
            resid_col = f"resid_{sector}"
            values = group[resid_col]

            if values.isna().all():
                continue

            # Build frequency-stamped DatetimeIndex for STL
            idx = pd.DatetimeIndex(group["period"].values).to_period("M").to_timestamp()
            ts = pd.Series(values.values, index=idx).asfreq("MS")

            result = STL(ts, period=STL_PERIOD, seasonal=STL_SEASONAL, robust=STL_ROBUST).fit()
            deseasonalized = result.trend + result.resid

            df.loc[group.index, f"deseason_{sector}"] = deseasonalized.values
            n_decomposed += 1

    logger.info("STL decompositions completed: %d", n_decomposed)
    return df


def standardize(df: pd.DataFrame) -> pd.DataFrame:
    """Z-score deseasonalized signals within each state/sector.

    Returns df with signal_res, signal_com, signal_ind added.
    """
    df = df.copy()
    for sector in SECTOR_KEYS:
        df[f"signal_{sector}"] = float("nan")

    for state, group in df.groupby("state"):
        for sector in SECTOR_KEYS:
            values = group[f"deseason_{sector}"]

            if values.isna().all():
                continue

            mean = values.mean()
            std = values.std()

            if std < 1e-10:
                logger.warning("Near-zero std for %s/%s — setting signal to 0.0", state, sector)
                df.loc[group.index, f"signal_{sector}"] = 0.0
            else:
                df.loc[group.index, f"signal_{sector}"] = (values - mean) / std

    return df
