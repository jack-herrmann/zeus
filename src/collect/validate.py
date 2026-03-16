"""Post-collection integrity checks for the merged panel."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def validate_panel(df: pd.DataFrame) -> list[str]:
    """Run integrity checks on the merged panel. Returns list of warnings/errors."""
    issues = []

    # 1. 50 unique states
    n_states = df["state"].nunique()
    if n_states != 50:
        issues.append(f"ERROR: Expected 50 states, found {n_states}")

    # 2. No duplicate (state, period)
    dupes = df.duplicated(subset=["state", "period"], keep=False).sum()
    if dupes > 0:
        issues.append(f"ERROR: {dupes} duplicate (state, period) rows")

    # 3. Contiguous monthly periods per state
    for state in df["state"].unique():
        periods = sorted(df.loc[df["state"] == state, "period"].unique())
        if len(periods) < 2:
            continue
        expected = pd.date_range(
            periods[0], periods[-1], freq="MS"
        ).strftime("%Y-%m").tolist()
        missing = set(expected) - set(periods)
        if missing:
            issues.append(
                f"WARNING: {state} missing {len(missing)} months "
                f"(e.g. {sorted(missing)[:3]})"
            )

    # 4. Non-negative sales
    for col in ["sales_res", "sales_com", "sales_ind"]:
        if col in df.columns:
            neg = (df[col] < 0).sum()
            if neg > 0:
                issues.append(f"WARNING: {neg} negative values in {col}")

    # 5. Price in [0, 100] cents/kWh
    for col in ["price_res", "price_com", "price_ind"]:
        if col in df.columns:
            out = ((df[col] < 0) | (df[col] > 100)).sum()
            if out > 0:
                issues.append(f"WARNING: {out} out-of-range values in {col}")

    # 6. Non-negative HDD/CDD
    for col in ["hdd", "cdd"]:
        if col in df.columns:
            neg = (df[col] < 0).sum()
            if neg > 0:
                issues.append(f"WARNING: {neg} negative values in {col}")

    # 7. Alaska has highest avg HDD
    if "hdd" in df.columns:
        avg_hdd = df.groupby("state")["hdd"].mean()
        if avg_hdd.idxmax() != "AK":
            issues.append(
                f"ERROR: Highest avg HDD is {avg_hdd.idxmax()} "
                f"({avg_hdd.max():.0f}), expected AK — "
                f"nClimDiv lookup table may be wrong!"
            )

    # 8. Hawaii has highest avg CDD
    if "cdd" in df.columns:
        avg_cdd = df.groupby("state")["cdd"].mean()
        if avg_cdd.idxmax() != "HI":
            issues.append(
                f"ERROR: Highest avg CDD is {avg_cdd.idxmax()} "
                f"({avg_cdd.max():.0f}), expected HI — "
                f"nClimDiv lookup table may be wrong!"
            )

    # 9. NaN < 5% per column
    nan_pct = df.isna().mean() * 100
    for col, pct in nan_pct.items():
        if pct > 5:
            issues.append(f"WARNING: {col} has {pct:.1f}% NaN (threshold: 5%)")

    # 10. No all-NaN rows
    data_cols = [c for c in df.columns if c not in ("state", "period")]
    all_nan = df[data_cols].isna().all(axis=1).sum()
    if all_nan > 0:
        issues.append(f"WARNING: {all_nan} rows with all-NaN data columns")

    return issues
