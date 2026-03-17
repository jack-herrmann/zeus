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
    END_DATE,
    FRED_API_KEY,
    FRED_BASE_URL,
    FRED_REQUEST_DELAY,
    START_DATE,
    STATES_50,
)

logger = logging.getLogger(__name__)

FRED_RAW_DIR = DATA_RAW / "fred"
FRED_RAW_FILE = FRED_RAW_DIR / "fred_raw.json"


def _make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def fetch_series(series_id: str, session: requests.Session) -> list[dict]:
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": START_DATE + "-01",
        "observation_end": END_DATE + "-31",
    }
    resp = session.get(FRED_BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()["observations"]


def fetch_all(use_cache: bool = True) -> pd.DataFrame:
    if use_cache and FRED_RAW_FILE.exists():
        logger.info("Loading cached FRED data from %s", FRED_RAW_FILE)
        with open(FRED_RAW_FILE) as f:
            all_records = json.load(f)
    else:
        session = _make_session()
        all_records = []
        for state in tqdm(STATES_50, desc="FRED"):
            series_id = f"{state}PHCI"
            observations = fetch_series(series_id, session)
            for obs in observations:
                obs["state"] = state
            all_records.extend(observations)
            time.sleep(FRED_REQUEST_DELAY)

        FRED_RAW_DIR.mkdir(parents=True, exist_ok=True)
        with open(FRED_RAW_FILE, "w") as f:
            json.dump(all_records, f)
        logger.info("Saved %d raw FRED records", len(all_records))

    df = pd.DataFrame(all_records)
    df["period"] = df["date"].str[:7]

    # FRED uses "." for missing
    df["value"] = df["value"].replace(".", pd.NA)
    df["coincident_index"] = pd.to_numeric(df["value"], errors="coerce")

    df = df[["state", "period", "coincident_index"]].copy()

    df = df[
        (df["period"] >= START_DATE) & (df["period"] <= END_DATE)
    ].copy()

    df.sort_values(["state", "period"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    logger.info("FRED: %d rows, %d states", len(df), df["state"].nunique())
    return df
