"""V8 — Lag analysis (cross-correlogram on detrended data)."""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import detrend

from .style import save_figure, zeus_style

logger = logging.getLogger("zeus.eda.vis_lags")

_STATES = ["TX", "NM", "UT", "MA"]
_STATE_COLORS = {
    "TX": "#9E3424", "NM": "#246184",
    "UT": "#6A6395", "MA": "#63822E",
}


def plot_lag_analysis(df: pd.DataFrame) -> None:
    """V8: cross-correlogram of detrended industrial signal vs CI."""
    lags = range(-48, 49)
    lag_list = list(lags)

    with zeus_style():
        fig, ax = plt.subplots(figsize=(10, 5.5))

        sample_n = None

        for state in _STATES:
            sub = (
                df[df["state"] == state]
                .sort_values("period")
                .dropna(subset=["signal_ind", "coincident_index"])
            )
            sig = detrend(sub["signal_ind"].values)
            ci = detrend(sub["coincident_index"].values)

            n = len(sig)
            if sample_n is None:
                sample_n = n

            rs = []
            for lag in lags:
                if lag < 0:
                    r = np.corrcoef(sig[:lag], ci[-lag:])[0, 1]
                elif lag > 0:
                    r = np.corrcoef(sig[lag:], ci[:-lag])[0, 1]
                else:
                    r = np.corrcoef(sig, ci)[0, 1]
                rs.append(r)

            color = _STATE_COLORS.get(state, "gray")
            ax.plot(lag_list, rs, linewidth=1.5,
                    color=color, label=state, alpha=0.8)

        # 95% significance band under the null of no correlation
        if sample_n:
            sig_bound = 1.96 / np.sqrt(sample_n)
            ax.axhspan(-sig_bound, sig_bound, color="lightgray", alpha=0.3,
                        label="95% null band")

        ax.axvline(0, color="gray", linewidth=0.8, linestyle="--")
        ax.axhline(0, color="gray", linewidth=0.3)

        ax.set_xlabel("Months shifted (negative = electricity first)")
        ax.set_ylabel("Correlation strength")
        ax.set_title(
            "Does Electricity Usage Predict or Follow Economic Activity?",
            fontsize=13, fontweight="bold",
        )
        ax.set_xticks(range(-48, 49, 12))
        ax.set_xticklabels([f"{m}" for m in range(-48, 49, 12)])
        ax.legend(loc="best", fontsize=10, frameon=True, fancybox=True,
                  framealpha=0.9, edgecolor="lightgray")

        fig.tight_layout()
        save_figure(fig, "v8_lag_analysis")
    logger.info("V8 complete")
