import logging

import numpy as np
import pandas as pd
from scipy.signal import detrend

from .style import SECTOR_KEYS

logger = logging.getLogger("zeus.eda.correlations")


def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for state in sorted(df["state"].unique()):
        group = df[df["state"] == state].sort_values("period")
        for sector in SECTOR_KEYS:
            sig_col = f"signal_{sector}"
            sig = group[sig_col].values
            ci = group["coincident_index"].values

            if np.isnan(sig).all():
                continue

            r_level = np.corrcoef(sig, ci)[0, 1]

            sig_dt = detrend(sig, type="linear")
            ci_dt = detrend(ci, type="linear")
            r_detrended = np.corrcoef(sig_dt, ci_dt)[0, 1]

            rows.append({
                "state": state,
                "sector": sector,
                "r_level": round(r_level, 4),
                "r_detrended": round(r_detrended, 4),
            })

    corr_df = pd.DataFrame(rows)
    logger.info(
        "Computed correlations: %d rows (%d states × %d sectors)",
        len(corr_df), corr_df["state"].nunique(),
        corr_df["sector"].nunique(),
    )
    return corr_df
