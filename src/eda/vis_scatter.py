import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import detrend

from .style import (
    pick_key_states,
    save_figure,
    zeus_style,
    zscore_series,
)

logger = logging.getLogger("zeus.eda.vis_scatter")


def plot_scatter(df: pd.DataFrame, corr_df: pd.DataFrame) -> None:
    key_states = pick_key_states(corr_df)

    with zeus_style():
        fig, axes = plt.subplots(1, 3, figsize=(14, 5))

        for ax, (abbr, name, r_val, line_color) in zip(axes, key_states):
            sub = df[df["state"] == abbr].sort_values("period")
            sig = sub["signal_ind"].values
            ci = sub["coincident_index"].values

            sig_dt = detrend(sig, type="linear")
            ci_dt = detrend(ci, type="linear")

            sig_z = zscore_series(pd.Series(sig_dt)).values
            ci_z = zscore_series(pd.Series(ci_dt)).values

            ax.scatter(sig_z, ci_z, alpha=0.25, s=12, color="#555555",
                       edgecolors="none")

            m, b = np.polyfit(sig_z, ci_z, 1)
            x_range = np.linspace(sig_z.min(), sig_z.max(), 100)
            ax.plot(x_range, m * x_range + b, color=line_color, linewidth=2.0)

            ax.set_title(
                f"{name} (r = {r_val:+.2f})",
                fontsize=11, fontweight="bold",
            )
            ax.set_xlabel("Industrial electricity", fontsize=9)
            ax.set_ylabel("Economic index", fontsize=9)
            ax.axhline(0, color="gray", linewidth=0.3, linestyle="--")
            ax.axvline(0, color="gray", linewidth=0.3, linestyle="--")

        lim = 5
        for a in axes:
            a.set_xlim(-lim, lim)
            a.set_ylim(-lim, lim)
            a.set_aspect("equal", adjustable="box")

        fig.suptitle(
            "Each Month as a Data Point: Industrial Electricity vs. the Economy",
            fontsize=14, fontweight="bold", y=1.01,
        )
        fig.tight_layout()
        save_figure(fig, "v7_scatter")
    logger.info("V7 complete")
