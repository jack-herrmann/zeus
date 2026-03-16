"""V6 — Deep-dive: cleaned industrial signal vs economic index."""

import logging

import matplotlib.pyplot as plt
import pandas as pd

from .style import (
    parse_periods,
    save_figure,
    zeus_style,
    zscore_series,
)

logger = logging.getLogger("zeus.eda.vis_deepdive")

ROLLING_WINDOW = 12

STATES_POS = [("TX", "Texas", 0.83), ("NM", "New Mexico", 0.74)]
STATES_NEG = [("UT", "Utah", -0.62), ("MA", "Massachusetts", -0.54)]

COLOR_POS = "#1A7A2E"
COLOR_NEG = "#C0392B"
COLOR_CI = "#7EBF8E"


def plot_deepdive(df: pd.DataFrame, corr_df: pd.DataFrame) -> None:
    """V6: 4 states, cleaned industrial signal + CI, rolling average."""
    all_states = STATES_POS + STATES_NEG

    with zeus_style():
        fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)

        for ax, (abbr, name, r_val) in zip(axes, all_states):
            sub = df[df["state"] == abbr].sort_values("period")
            dates = parse_periods(sub["period"])

            is_positive = r_val > 0
            line_color = COLOR_POS if is_positive else COLOR_NEG

            sig = sub["signal_ind"].copy()
            ci_z = zscore_series(sub["coincident_index"])

            sig.index = dates
            ci_z.index = dates

            sig_smooth = sig.rolling(ROLLING_WINDOW, min_periods=1).mean()
            ci_smooth = ci_z.rolling(ROLLING_WINDOW, min_periods=1).mean()

            # Raw monthly as faint background
            ax.plot(dates, sig.values, color=line_color, alpha=0.15, linewidth=0.5)

            # Smooth lines
            ax.plot(dates, sig_smooth.values, color=line_color, linewidth=2.2,
                    label="Industrial signal (cleaned)")
            ax.plot(dates, ci_smooth.values, color=COLOR_CI, linewidth=1.8,
                    linestyle="--", label="Economic index")

            ax.set_title(
                f"{name} (r = {r_val:+.2f})",
                fontsize=11, fontweight="bold", loc="left",
            )
            ax.set_ylabel("Relative level", fontsize=9)
            ax.axhline(0, color="gray", linewidth=0.3)

        axes[0].legend(loc="upper left", fontsize=8)

        fig.suptitle(
            "Does the Cleaned Industrial Signal Track the Economy?",
            fontsize=14, fontweight="bold", y=1.0,
        )
        fig.tight_layout()
        save_figure(fig, "v6_deepdive")
    logger.info("V6 complete")
