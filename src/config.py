import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

EIA_API_KEY = os.environ["EIA_API_KEY"]
FRED_API_KEY = os.environ["FRED_API_KEY"]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"

START_DATE = "2001-01"
END_DATE = "2024-12"

STATES_50 = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

# alphabetical: 001=AL ... 048=WY, then 049=AK, 050=HI
NCLIMDIV_TO_STATE = {
    1: "AL",  2: "AZ",  3: "AR",  4: "CA",  5: "CO",
    6: "CT",  7: "DE",  8: "FL",  9: "GA", 10: "ID",
    11: "IL", 12: "IN", 13: "IA", 14: "KS", 15: "KY",
    16: "LA", 17: "ME", 18: "MD", 19: "MA", 20: "MI",
    21: "MN", 22: "MS", 23: "MO", 24: "MT", 25: "NE",
    26: "NV", 27: "NH", 28: "NJ", 29: "NM", 30: "NY",
    31: "NC", 32: "ND", 33: "OH", 34: "OK", 35: "OR",
    36: "PA", 37: "RI", 38: "SC", 39: "SD", 40: "TN",
    41: "TX", 42: "UT", 43: "VT", 44: "VA", 45: "WA",
    46: "WV", 47: "WI", 48: "WY", 49: "AK", 50: "HI",
}

EIA_BASE_URL = "https://api.eia.gov/v2/electricity/retail-sales/data/"
EIA_SECTORS = ["RES", "COM", "IND"]
EIA_REQUEST_DELAY = 0.5

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_REQUEST_DELAY = 0.2

NOAA_BASE_URL = "https://www.ncei.noaa.gov/pub/data/cirs/climdiv/"
NOAA_HDD_PREFIX = "climdiv-hddcst-v1.0.0-"
NOAA_CDD_PREFIX = "climdiv-cddcst-v1.0.0-"
