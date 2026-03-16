"""NOAA HDD/CDD bulk file download and fixed-width parser."""

import json
import logging
import re
from pathlib import Path

import pandas as pd
import requests

from src.config import (
    DATA_RAW,
    END_DATE,
    NCLIMDIV_TO_STATE,
    NOAA_BASE_URL,
    NOAA_CDD_PREFIX,
    NOAA_HDD_PREFIX,
    START_DATE,
    STATES_50,
)

logger = logging.getLogger(__name__)

NOAA_RAW_DIR = DATA_RAW / "noaa"


def discover_filename(prefix: str, session: requests.Session) -> str:
    """Find the latest versioned filename from the NOAA directory listing."""
    resp = session.get(NOAA_BASE_URL, timeout=30)
    resp.raise_for_status()

    # Parse hrefs from directory listing HTML
    matches = re.findall(r'href="(' + re.escape(prefix) + r'[^"]+)"', resp.text)
    if not matches:
        raise FileNotFoundError(
            f"No files matching prefix '{prefix}' at {NOAA_BASE_URL}"
        )
    # Last lexicographically = most recent date stamp
    return sorted(matches)[-1]


def download_file(
    filename: str, session: requests.Session
) -> Path:
    """Stream-download a file from NOAA to data/raw/noaa/."""
    dest = NOAA_RAW_DIR / filename
    if dest.exists():
        logger.info("Already downloaded: %s", dest.name)
        return dest

    url = NOAA_BASE_URL + filename
    logger.info("Downloading %s", url)
    resp = session.get(url, stream=True, timeout=60)
    resp.raise_for_status()

    NOAA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return dest


def parse_fixed_width(filepath: Path, value_name: str) -> pd.DataFrame:
    """Parse an nClimDiv fixed-width file into a long DataFrame.

    Layout (0-indexed):
      [0:3]   state code (3 digits)
      [3]     division ("0" = state-level)
      [4:6]   element code
      [6:10]  year
      [10+i*7 : 10+(i+1)*7] for i in 0..11 → monthly values
    """
    rows = []
    with open(filepath, "r") as f:
        for line in f:
            if len(line.rstrip()) < 94:
                continue
            # Only state-level aggregates (division code "0")
            if line[3] != "0":
                continue

            state_code = int(line[0:3])
            if state_code not in NCLIMDIV_TO_STATE:
                continue

            state = NCLIMDIV_TO_STATE[state_code]
            year = line[6:10]

            for month_idx in range(12):
                start = 10 + month_idx * 7
                end = start + 7
                val_str = line[start:end].strip()
                try:
                    val = float(val_str)
                except ValueError:
                    val = float("nan")

                if val <= -9999:
                    val = float("nan")

                period = f"{year}-{month_idx + 1:02d}"
                rows.append({"state": state, "period": period, value_name: val})

    return pd.DataFrame(rows)


def fetch_all(use_cache: bool = True) -> pd.DataFrame:
    """Download and parse NOAA HDD/CDD data for all 50 states."""
    session = requests.Session()

    # Discover and download both files
    hdd_filename = discover_filename(NOAA_HDD_PREFIX, session)
    cdd_filename = discover_filename(NOAA_CDD_PREFIX, session)

    hdd_path = download_file(hdd_filename, session)
    cdd_path = download_file(cdd_filename, session)

    # Parse
    logger.info("Parsing HDD file: %s", hdd_path.name)
    hdd_df = parse_fixed_width(hdd_path, "hdd")
    logger.info("Parsing CDD file: %s", cdd_path.name)
    cdd_df = parse_fixed_width(cdd_path, "cdd")

    # Merge HDD and CDD
    df = hdd_df.merge(cdd_df, on=["state", "period"], how="outer")

    # Filter to date range and known states
    df = df[
        (df["period"] >= START_DATE)
        & (df["period"] <= END_DATE)
        & (df["state"].isin(STATES_50))
    ].copy()

    df.sort_values(["state", "period"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    logger.info("NOAA: %d rows, %d states", len(df), df["state"].nunique())
    return df
