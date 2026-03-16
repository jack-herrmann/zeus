"""Phase 3 orchestrator — runs all EDA visualizations."""

import logging
import warnings

import pandas as pd

from src.config import DATA_PROCESSED

from .correlations import compute_correlations
from .vis_national import plot_national_trends
from .vis_weather import plot_signal_pipeline
from .vis_deepdive import plot_deepdive
from .vis_scatter import plot_scatter
from .vis_lags import plot_lag_analysis

logger = logging.getLogger("zeus.eda.pipeline")


def run_eda() -> None:
    """Phase 3 orchestrator. Reads parquet files directly."""
    df_raw = pd.read_parquet(DATA_PROCESSED / "panel.parquet")
    df = pd.read_parquet(DATA_PROCESSED / "panel_signal.parquet")
    corr_df = compute_correlations(df)

    # ------------------------------------------------------------------
    # Act 1: The Promise
    # ------------------------------------------------------------------
    plot_national_trends(df_raw)           # V1
    _try_geo("plot_industrial_share", df)  # V2
    _try_geo("plot_growth_comparison", df) # V3

    # ------------------------------------------------------------------
    # Act 2: The Method
    # ------------------------------------------------------------------
    plot_signal_pipeline(df)               # V4

    # ------------------------------------------------------------------
    # Act 3: The Surprise
    # ------------------------------------------------------------------
    _try_geo("plot_deindustrialization_map", corr_df)    # V5 — climax
    plot_deepdive(df, corr_df)                           # V6
    plot_scatter(df, corr_df)                            # V7

    # ------------------------------------------------------------------
    # Act 4: The Practical Limits
    # ------------------------------------------------------------------
    plot_lag_analysis(df)                  # V8

    logger.info("All Phase 3 visuals complete.")


def _try_geo(func_name: str, data) -> None:
    """Attempt a geopandas-dependent plot; skip gracefully if unavailable."""
    try:
        from . import geo
        fn = getattr(geo, func_name)
        fn(data)
    except ImportError:
        logger.warning(
            "geopandas not installed — skipping %s. "
            "Install with: pip install geopandas", func_name,
        )
    except Exception:
        logger.exception("Failed to generate %s", func_name)
