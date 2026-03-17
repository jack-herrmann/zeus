import logging

import pandas as pd

from src.config import DATA_PROCESSED

from .missing import audit_missing, plot_missingness_heatmap
from .outliers import detect_outliers, interpolate_outliers, log_outlier_report

logger = logging.getLogger("zeus.clean.pipeline")


def clean_panel(df: pd.DataFrame) -> pd.DataFrame:
    missing_pct = audit_missing(df)
    plot_missingness_heatmap(missing_pct)

    outlier_report = detect_outliers(df)
    log_outlier_report(outlier_report)
    df_clean = interpolate_outliers(df, outlier_report)

    sales_cols = ["sales_res", "sales_com", "sales_ind"]
    n_changed = 0
    for col in sales_cols:
        n_changed += (df[col] != df_clean[col]).sum()
    logger.info("Values changed: %d", n_changed)

    out_path = DATA_PROCESSED / "panel_clean.parquet"
    df_clean.to_parquet(out_path, index=False)
    logger.info("Saved clean panel to %s", out_path)

    return df_clean
