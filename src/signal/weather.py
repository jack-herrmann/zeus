import logging

import pandas as pd
import statsmodels.api as sm

logger = logging.getLogger("zeus.signal.weather")

SECTORS = {
    "res": ("sales_res", "price_res"),
    "com": ("sales_com", "price_com"),
    "ind": ("sales_ind", "price_ind"),
}
WEATHER_SKIP_STATES = {"AK", "HI"}


def weather_adjust(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for sector in SECTORS:
        df[f"resid_{sector}"] = float("nan")

    r2_by_sector = {sector: [] for sector in SECTORS}
    skipped = []

    for state, group in df.groupby("state"):
        if state in WEATHER_SKIP_STATES:
            skipped.append(state)
            continue

        for sector, (sales_col, price_col) in SECTORS.items():
            y = group[sales_col]
            X = group[["hdd", "cdd", price_col]].copy()
            X["hdd2"] = X["hdd"] ** 2
            X["cdd2"] = X["cdd"] ** 2
            X = sm.add_constant(X)

            model = sm.OLS(y, X).fit()
            df.loc[group.index, f"resid_{sector}"] = model.resid
            r2_by_sector[sector].append(model.rsquared)

    for sector, r2_list in r2_by_sector.items():
        s = pd.Series(r2_list)
        logger.info(
            "R² [%s]: min=%.3f  median=%.3f  max=%.3f",
            sector, s.min(), s.median(), s.max(),
        )
    logger.info("Skipped states (no weather data): %s", sorted(skipped))

    return df
