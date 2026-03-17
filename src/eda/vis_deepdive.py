import logging

import matplotlib.pyplot as plt
import pandas as pd

from .style import (
    parse_periods,
    pick_key_states,
    save_figure,
    zeus_style,
    zscore_series,
)

logger = logging.getLogger("zeus.eda.vis_deepdive")

ROLLING_WINDOW = 12
COLOR_CI = "#5B7B9A"


def plot_deepdive(df: pd.DataFrame, corr_df: pd.DataFrame) -> None:
    key_states = pick_key_states(corr_df)

    with zeus_style():
        fig, axes = plt.subplots(3, 1, figsize=(14, 8), sharex=True)

        for ax, (abbr, name, r_val, line_color) in zip(axes, key_states):
            sub = df[df["state"] == abbr].sort_values("period")
            dates = parse_periods(sub["period"])

            sig = sub["signal_ind"].copy()
            ci_z = zscore_series(sub["coincident_index"])

            sig.index = dates
            ci_z.index = dates

            sig_smooth = sig.rolling(ROLLING_WINDOW, min_periods=1).mean()
            ci_smooth = ci_z.rolling(ROLLING_WINDOW, min_periods=1).mean()

            # raw monthly as faint background
            ax.plot(dates, sig.values, color=line_color, alpha=0.15, linewidth=0.5)

            # smooth lines
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

        axes[-1].set_xlim(dates.min(), dates.max())
        axes[0].legend(loc="upper left", fontsize=8)

        fig.suptitle(
            "Does the Cleaned Industrial Signal Track the Economy?",
            fontsize=14, fontweight="bold", y=1.0,
        )
        fig.tight_layout()
        save_figure(fig, "v6_deepdive")
    logger.info("V6 complete")
