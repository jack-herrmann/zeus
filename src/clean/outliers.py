"""Spike detection and interpolation for electricity sales data."""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger("zeus.clean.outliers")

SALES_COLS = ["sales_res", "sales_com", "sales_ind"]
ROLLING_WINDOW = 13
MIN_PERIODS = 7
LOCAL_Z_THRESHOLD = 4.0
NEIGHBOR_DEV_THRESHOLD = 0.50


def detect_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Detect outlier spikes using rolling MAD z-score AND neighbor deviation.

    Both thresholds must be exceeded to flag a value. This avoids false
    positives from structural breaks (rolling window handles regime shifts)
    and seasonal peaks (neighbor check handles regular extremes).
    """
    records = []

    for state, group in df.groupby("state"):
        group = group.sort_values("period")

        for col in SALES_COLS:
            values = group[col].values
            periods = group["period"].values

            rolling_median = (
                pd.Series(values)
                .rolling(ROLLING_WINDOW, center=True, min_periods=MIN_PERIODS)
                .median()
                .values
            )
            rolling_mad = (
                pd.Series(values)
                .rolling(ROLLING_WINDOW, center=True, min_periods=MIN_PERIODS)
                .apply(lambda x: np.median(np.abs(x - np.median(x))), raw=True)
                .values
            )

            for i in range(len(values)):
                v = values[i]
                med = rolling_median[i]
                mad = rolling_mad[i]

                if np.isnan(v) or np.isnan(med) or np.isnan(mad) or mad == 0:
                    continue

                local_z = 0.6745 * abs(v - med) / mad

                if local_z < LOCAL_Z_THRESHOLD:
                    continue

                # Neighbor deviation check
                prev_val = values[i - 1] if i > 0 else np.nan
                next_val = values[i + 1] if i < len(values) - 1 else np.nan
                neighbors = [x for x in [prev_val, next_val] if not np.isnan(x)]

                if not neighbors:
                    continue

                neighbor_avg = np.mean(neighbors)
                if neighbor_avg == 0:
                    continue

                neighbor_dev = abs(v - neighbor_avg) / neighbor_avg

                if neighbor_dev >= NEIGHBOR_DEV_THRESHOLD:
                    records.append({
                        "state": state,
                        "period": periods[i],
                        "column": col,
                        "value": v,
                        "rolling_median": round(med, 1),
                        "local_z": round(local_z, 2),
                        "neighbor_dev_pct": round(neighbor_dev * 100, 1),
                    })

    return pd.DataFrame(records)


def interpolate_outliers(
    df: pd.DataFrame, outlier_report: pd.DataFrame
) -> pd.DataFrame:
    """Replace flagged spikes with neighbor averages.

    Uses original (pre-interpolation) values for neighbor lookups.
    Falls back to rolling median if a neighbor is itself an outlier.
    """
    if outlier_report.empty:
        logger.info("No outliers to interpolate.")
        return df.copy()

    df_clean = df.copy()

    # Set of outlier keys for neighbor-is-outlier fallback
    outlier_keys = set()
    for _, row in outlier_report.iterrows():
        outlier_keys.add((row["state"], row["period"], row["column"]))

    for _, row in outlier_report.iterrows():
        state = row["state"]
        period = row["period"]
        col = row["column"]
        rolling_med = row["rolling_median"]

        # Get this state's data sorted by period from ORIGINAL df
        state_mask = df["state"] == state
        state_data = df.loc[state_mask].sort_values("period")
        periods = state_data["period"].values
        idx = np.where(periods == period)[0]

        if len(idx) == 0:
            continue
        i = idx[0]

        neighbors = []
        # Previous month
        if i > 0:
            prev_period = periods[i - 1]
            if (state, prev_period, col) not in outlier_keys:
                neighbors.append(state_data.iloc[i - 1][col])
        # Next month
        if i < len(periods) - 1:
            next_period = periods[i + 1]
            if (state, next_period, col) not in outlier_keys:
                neighbors.append(state_data.iloc[i + 1][col])

        if neighbors:
            new_val = np.mean(neighbors)
        else:
            new_val = rolling_med

        mask = (df_clean["state"] == state) & (df_clean["period"] == period)
        old_val = df_clean.loc[mask, col].iloc[0]
        df_clean.loc[mask, col] = new_val

        logger.info(
            "  %s %s %s: %.1f -> %.1f",
            state, period, col, old_val, new_val,
        )

    return df_clean


def log_outlier_report(outlier_report: pd.DataFrame) -> None:
    """Pretty-print the outlier detection results."""
    if outlier_report.empty:
        logger.info("No outliers detected.")
        return

    logger.info("Detected %d outlier(s):", len(outlier_report))
    logger.info(
        "  %-5s %-8s %-10s %8s %8s %7s %8s",
        "State", "Period", "Column", "Value", "RolMed", "Z", "Nbr%",
    )
    for _, row in outlier_report.iterrows():
        logger.info(
            "  %-5s %-8s %-10s %8.1f %8.1f %7.2f %7.1f%%",
            row["state"],
            row["period"],
            row["column"],
            row["value"],
            row["rolling_median"],
            row["local_z"],
            row["neighbor_dev_pct"],
        )
