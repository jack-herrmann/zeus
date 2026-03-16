"""Shared visual style, palettes, and helper functions for Phase 3 figures."""

import logging
from contextlib import contextmanager

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from src.config import FIGURES_DIR

logger = logging.getLogger("zeus.eda.style")

# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------
DIVERGING_CMAP = "RdBu_r"
SEQUENTIAL_CMAP = "YlGn"

SECTOR_LABELS = {"res": "Residential", "com": "Commercial", "ind": "Industrial"}
SECTOR_KEYS = ["res", "com", "ind"]

# Colors for the three key states (max / near-0 / min correlation)
COLOR_KEY_MAX = "#1A7A2E"    # green
COLOR_KEY_MIN = "#C0392B"    # red
COLOR_KEY_NEAR0 = "#DAA520"  # yellow (goldenrod)

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}


def pick_key_states(corr_df):
    """Return [(abbr, name, r_val, color), ...] for max, near-0, min industrial correlation."""
    ind = corr_df[corr_df["sector"] == "ind"].copy()
    max_idx = ind["r_detrended"].idxmax()
    min_idx = ind["r_detrended"].idxmin()
    ind["_abs_r"] = ind["r_detrended"].abs()
    near0_idx = ind["_abs_r"].idxmin()

    result = []
    for idx, color in [(max_idx, COLOR_KEY_MAX), (near0_idx, COLOR_KEY_NEAR0), (min_idx, COLOR_KEY_MIN)]:
        row = ind.loc[idx]
        abbr = row["state"]
        result.append((abbr, STATE_NAMES.get(abbr, abbr), row["r_detrended"], color))
    return result

# ---------------------------------------------------------------------------
# NBER recession date ranges
# ---------------------------------------------------------------------------
RECESSIONS = [
    ("2007-12-01", "2009-06-30"),
    ("2020-02-01", "2020-04-30"),
]

# ---------------------------------------------------------------------------
# States used in lag visuals
# ---------------------------------------------------------------------------
LAG_STATES = ["TX", "OH", "LA", "FL", "PA"]

# ---------------------------------------------------------------------------
# Style context manager
# ---------------------------------------------------------------------------
_ZEUS_RC = {
    "figure.figsize": (10, 6),
    "figure.dpi": 100,
    "savefig.dpi": 300,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.alpha": 0.3,
    "grid.linewidth": 0.5,
    "legend.frameon": False,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
}


@contextmanager
def zeus_style():
    """Context manager that applies the ZEUS matplotlib theme."""
    with plt.rc_context(_ZEUS_RC):
        yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def save_figure(fig, name: str) -> None:
    """Save figure to figures/ at 300 DPI and close it."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / f"{name}.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info("Saved %s", out)


def add_recession_bands(ax) -> None:
    """Shade NBER recession periods. Adds one legend entry."""
    added_label = False
    for start, end in RECESSIONS:
        label = "Recession" if not added_label else None
        ax.axvspan(
            pd.Timestamp(start), pd.Timestamp(end),
            facecolor="#CCCCCC", alpha=0.3, edgecolor="none",
            label=label, zorder=0,
        )
        added_label = True


def zscore_series(s: pd.Series) -> pd.Series:
    """Z-score a Series (subtract mean, divide by std)."""
    std = s.std()
    if std < 1e-10:
        return s - s.mean()
    return (s - s.mean()) / std


def parse_periods(period_col: pd.Series) -> pd.DatetimeIndex:
    """Convert 'YYYY-MM' string column to DatetimeIndex."""
    return pd.to_datetime(period_col, format="%Y-%m")
