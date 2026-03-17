import logging

import matplotlib.pyplot as plt
import pandas as pd

from .style import parse_periods, save_figure, zeus_style

logger = logging.getLogger("zeus.eda.vis_weather")

# light -> medium -> dark
_COLOR_RAW = "#A8C4E0"
_COLOR_DEWEATHERED = "#4A86C8"
_COLOR_SIGNAL = "#1B4F8A"


def plot_signal_pipeline(df: pd.DataFrame) -> None:
    fl = df[df["state"] == "FL"].sort_values("period")
    dates = parse_periods(fl["period"])

    r2 = 1 - fl["resid_res"].var() / fl["sales_res"].var()

    with zeus_style():
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

        # panel 1: raw
        ax1.plot(dates, fl["sales_res"], color=_COLOR_RAW, linewidth=0.9)
        ax1.set_ylabel("MWh")
        ax1.set_title(
            "Raw Monthly Data — Dominated by Weather",
            fontsize=11, fontweight="bold", loc="left",
        )

        # panel 2: weather-adjusted
        ax2.plot(dates, fl["resid_res"], color=_COLOR_DEWEATHERED, linewidth=0.9)
        ax2.set_ylabel("MWh (residual)")
        ax2.set_title(
            "After Removing Weather Effects",
            fontsize=11, fontweight="bold", loc="left",
        )
        ax2.text(
            0.98, 0.92,
            f"R² = {r2:.2f} — weather explains {r2*100:.0f}% of variance",
            transform=ax2.transAxes, ha="right", va="top",
            fontsize=10, fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.3", fc="white",
                ec=_COLOR_DEWEATHERED, alpha=0.9,
            ),
        )

        # panel 3: final signal
        ax3.plot(dates, fl["signal_res"], color=_COLOR_SIGNAL, linewidth=0.9)
        ax3.set_ylabel("Relative level")
        ax3.set_title(
            "Final Cleaned Signal — Ready for Analysis",
            fontsize=11, fontweight="bold", loc="left",
        )
        ax3.axhline(0, color="gray", linewidth=0.5, linestyle="--")

        fig.suptitle(
            "How We Extract an Economic Signal from Electricity Data",
            fontsize=13, fontweight="bold", y=1.01,
        )
        fig.tight_layout()
        save_figure(fig, "v4_signal_pipeline")
    logger.info("V4 complete")
