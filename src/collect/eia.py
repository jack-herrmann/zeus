import json
import logging
import time

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

from src.config import (
    DATA_RAW,
    EIA_API_KEY,
    EIA_BASE_URL,
    EIA_REQUEST_DELAY,
    EIA_SECTORS,
    END_DATE,
    START_DATE,
    STATES_50,
)

logger = logging.getLogger(__name__)

EIA_RAW_DIR = DATA_RAW / "eia"
EIA_RAW_FILE = EIA_RAW_DIR / "eia_raw.json"


def _make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def fetch_state(state: str, session: requests.Session) -> list[dict]:
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "monthly",
        "data[0]": "sales",
        "data[1]": "price",
        "facets[stateid][]": state,
        "facets[sectorid][]": EIA_SECTORS,
        "start": START_DATE,
        "end": END_DATE,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": 5000,
    }
    resp = session.get(EIA_BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()["response"]["data"]

    if len(data) == 5000:
        logger.warning("EIA response for %s has exactly 5000 rows — possible truncation!", state)

    return data


def fetch_all(use_cache: bool = True) -> pd.DataFrame:
    if use_cache and EIA_RAW_FILE.exists():
        logger.info("Loading cached EIA data from %s", EIA_RAW_FILE)
        with open(EIA_RAW_FILE) as f:
            all_records = json.load(f)
    else:
        session = _make_session()
        all_records = []
        for state in tqdm(STATES_50, desc="EIA"):
            records = fetch_state(state, session)
            all_records.extend(records)
            time.sleep(EIA_REQUEST_DELAY)

        EIA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        with open(EIA_RAW_FILE, "w") as f:
            json.dump(all_records, f)
        logger.info("Saved %d raw EIA records", len(all_records))

    df = pd.DataFrame(all_records)

    df = df.rename(columns={
        "stateid": "state",
        "sectorid": "sector",
    })

    df = df[["state", "period", "sector", "sales", "price"]].copy()

    # EIA returns strings
    for col in ["sales", "price"]:
        before = df[col].notna().sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        after = df[col].notna().sum()
        coerced = before - after
        if coerced > 0:
            logger.warning("EIA: %d values coerced to NaN in '%s'", coerced, col)

    dropped = df[~df["state"].isin(STATES_50)]
    if len(dropped) > 0:
        logger.info("EIA: dropped %d rows with state not in STATES_50", len(dropped))
    df = df[df["state"].isin(STATES_50)].copy()

    df = df.rename(columns={"sales": "sales_mwh", "price": "price_cents_kwh"})

    df.sort_values(["state", "period", "sector"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    logger.info("EIA: %d rows, %d states", len(df), df["state"].nunique())
    return df
