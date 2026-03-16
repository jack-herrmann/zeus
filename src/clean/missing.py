"""Missingness audit and heatmap visualization."""

import logging

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import FIGURES_DIR

logger = logging.getLogger("zeus.clean.missing")

DATA_COLS = [
    "sales_res", "sales_com", "sales_ind",
    "price_res", "price_com", "price_ind",
    "hdd", "cdd",
    "coincident_index",
]


def audit_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Compute % missing for each (state, column) pair.

    Returns a DataFrame with states as rows and data columns as columns,
    values are % of months that are NaN.
    """
    states = sorted(df["state"].unique())
    result = {}

    for state in states:
        state_df = df.loc[df["state"] == state, DATA_COLS]
        result[state] = (state_df.isna().sum() / len(state_df) * 100).round(1)

    missing_pct = pd.DataFrame(result).T
    missing_pct.index.name = "state"

    total_nan = df[DATA_COLS].isna().sum().sum()
    logger.info("Total NaN cells across panel: %d", total_nan)

    nonzero = missing_pct.stack()
    nonzero = nonzero[nonzero > 0]
    if len(nonzero) > 0:
        logger.info("Non-zero missingness:")
        for (state, col), pct in nonzero.items():
            logger.info("  %s / %s: %.1f%%", state, col, pct)
    else:
        logger.info("No missing data found.")

    return missing_pct


def plot_missingness_heatmap(missing_pct: pd.DataFrame) -> None:
    """Save a missingness heatmap to figures/missingness_heatmap.png."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 8))

    # Annotation: show percentage only for non-zero cells
    annot = missing_pct.map(lambda v: f"{v:.0f}%" if v > 0 else "")

    sns.heatmap(
        missing_pct,
        ax=ax,
        cmap="Reds",
        vmin=0,
        vmax=100,
        annot=annot,
        fmt="",
        linewidths=0.3,
        linecolor="lightgray",
        cbar_kws={"label": "% Missing"},
    )

    ax.set_title("Missingness by State and Variable", fontsize=14)
    ax.set_xlabel("Variable", fontsize=12)
    ax.set_ylabel("State", fontsize=12)
    ax.tick_params(axis="y", labelsize=7)

    fig.tight_layout()
    out_path = FIGURES_DIR / "missingness_heatmap.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    logger.info("Saved missingness heatmap to %s", out_path)
