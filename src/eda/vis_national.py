"""V1 — Three-panel national sector trends with economic event markers."""

import logging

import matplotlib.pyplot as plt
import pandas as pd

from .style import (
    parse_periods,
    save_figure,
    zeus_style,
)

logger = logging.getLogger("zeus.eda.vis_national")

LINE_COLOR = "#2F4F6F"
ROLLING_WINDOW = 12

RECESSIONS = [
    ("2001-03-01", "2001-11-30", "Dot-com\nRecession"),
    ("2007-12-01", "2009-06-30", "Great\nRecession"),
    ("2020-02-01", "2020-04-30", "COVID-19"),
]

EVENT_LINES = [
    ("2001-12-11", "China joins\nWTO", "#348ABD"),
    ("2008-09-15", "Lehman Brothers\ncollapse", "#D62728"),
    ("2014-06-01", "Oil price\ncollapse", "#E8900C"),
    ("2016-01-01", "Manufacturing\ntrough", "#E8900C"),
    ("2020-05-01", "Economy\nreopens", "#2CA02C"),
    ("2022-08-09", "CHIPS Act\nsigned", "#2CA02C"),
]

SECTORS = ["ind"]
PANEL_TITLES = {
    "ind": "Industrial",
}


def _add_events(ax, ymin: float, ymax: float) -> None:
    """Add labeled recession bands and event lines to an axis."""
    for start, end, label in RECESSIONS:
        ts_start = pd.Timestamp(start)
        ts_end = pd.Timestamp(end)
        ax.axvspan(
            ts_start, ts_end,
            facecolor="#CCCCCC", alpha=0.25, edgecolor="none", zorder=0,
        )
        mid = ts_start + (ts_end - ts_start) / 2
        ax.text(
            mid, ymin + (ymax - ymin) * 0.06, label,
            fontsize=6, color="#666666", ha="center", va="bottom",
            fontstyle="italic", alpha=0.9,
        )

    for date_str, label, color in EVENT_LINES:
        dt = pd.Timestamp(date_str)
        ax.axvline(dt, color=color, linewidth=0.7, linestyle="--", alpha=0.6, zorder=1)
        ax.text(
            dt, ymax - (ymax - ymin) * 0.02, label,
            fontsize=6.5, color=color, ha="center", va="top",
            fontweight="bold", alpha=0.85,
        )


def plot_national_trends(df: pd.DataFrame) -> None:
    """V1: three stacked panels, rolling avg, recession bands, event markers."""
    national = df.groupby("period")[["sales_res", "sales_com", "sales_ind"]].sum()
    national = national / 1000  # MWh → GWh
    national.index = parse_periods(pd.Series(national.index))
    national = national.sort_index()

    with zeus_style():
        fig, ax = plt.subplots(1, 1, figsize=(14, 4.5))

        for sector in SECTORS:
            col = f"sales_{sector}"
            raw = national[col]
            smooth = raw.rolling(ROLLING_WINDOW, min_periods=1).mean()

            data_min = smooth.min()
            data_max = smooth.max()
            data_range = data_max - data_min
            ymin = max(0, data_min - data_range * 0.8)
            ymax = data_max + data_range * 0.6

            ax.plot(raw.index, raw.values, color=LINE_COLOR, alpha=0.3, linewidth=0.5)
            ax.plot(smooth.index, smooth.values, color=LINE_COLOR, linewidth=2.2)

            ax.set_ylim(ymin, ymax)
            ax.set_ylabel("GWh", fontsize=10)
            ax.set_title(PANEL_TITLES[sector], fontsize=12, fontweight="bold", loc="left")

            _add_events(ax, ymin, ymax)

        fig.suptitle(
            "U.S. Monthly Electricity by Sector (12-Month Rolling Average)",
            fontsize=14, fontweight="bold", y=1.0,
        )
        fig.tight_layout()
        save_figure(fig, "v1_national_trends")
    logger.info("V1 complete")
