"""V8 — Lag analysis (cross-correlogram on detrended data)."""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import detrend

from .style import pick_key_states, save_figure, zeus_style

logger = logging.getLogger("zeus.eda.vis_lags")


def plot_lag_analysis(df: pd.DataFrame, corr_df: pd.DataFrame) -> None:
    """V8: cross-correlogram of detrended industrial signal vs CI (all states)."""
    lags = range(-48, 49)
    lag_list = list(lags)

    all_states = sorted(df["state"].unique())
    key_states = {abbr: (name, color) for abbr, name, _r, color in pick_key_states(corr_df)}

    def _compute_ccf(state):
        sub = (
            df[df["state"] == state]
            .sort_values("period")
            .dropna(subset=["signal_ind", "coincident_index"])
        )
        if len(sub) < 10:
            return None, 0
        sig = detrend(sub["signal_ind"].values)
        ci = detrend(sub["coincident_index"].values)
        rs = []
        for lag in lags:
            if lag < 0:
                r = np.corrcoef(sig[:lag], ci[-lag:])[0, 1]
            elif lag > 0:
                r = np.corrcoef(sig[lag:], ci[:-lag])[0, 1]
            else:
                r = np.corrcoef(sig, ci)[0, 1]
            rs.append(r)
        return rs, len(sig)

    with zeus_style():
        fig, ax = plt.subplots(figsize=(10, 5.5))

        sample_n = None
        key_curves = {}

        for state in all_states:
            rs, n = _compute_ccf(state)
            if rs is None:
                continue
            if sample_n is None:
                sample_n = n

            if state in key_states:
                key_curves[state] = rs
            else:
                ax.plot(lag_list, rs, linewidth=0.8,
                        color="#2F4F6F", alpha=0.15)

        # Overlay key states on top (in pick_key_states order: green, yellow, red)
        key_order = [abbr for abbr, _name, _r, _color in pick_key_states(corr_df)]
        for state in key_order:
            if state in key_curves:
                name, color = key_states[state]
                ax.plot(lag_list, key_curves[state], linewidth=2.0,
                        color=color, alpha=0.9, label=name)

        # 95% significance band under the null of no correlation
        if sample_n:
            sig_bound = 1.96 / np.sqrt(sample_n)
            ax.axhspan(-sig_bound, sig_bound, color="lightgray", alpha=0.3)

        ax.axvline(0, color="gray", linewidth=0.8, linestyle="--")
        ax.axhline(0, color="gray", linewidth=0.3)

        ax.set_xlabel("Months shifted (negative = electricity first)")
        ax.set_ylabel("Correlation strength")
        ax.set_title(
            "Does Electricity Usage Predict or Follow Economic Activity?",
            fontsize=13, fontweight="bold",
        )
        ax.set_xlim(-48, 48)
        ax.set_xticks(range(-48, 49, 12))
        ax.set_ylim(-1.0, 1.0)
        ax.set_xticklabels([f"{m}" for m in range(-48, 49, 12)])
        ax.legend(loc="best", fontsize=10, frameon=True, fancybox=True,
                  framealpha=0.9, edgecolor="lightgray")

        fig.tight_layout()
        save_figure(fig, "v8_lag_analysis")
    logger.info("V8 complete")
