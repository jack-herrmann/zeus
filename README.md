# ZEUS

Can state-level electricity consumption tell us something about economic activity?

This project collects monthly data from three federal sources, strips out weather
and seasonal noise, and checks whether what's left tracks the
[Philadelphia Fed State Coincident Index](https://www.philadelphiafed.org/surveys-and-data/regional-economic-analysis/state-coincident-indexes).

## Data

| Source | What we pull | API |
|--------|-------------|-----|
| **EIA** | Electricity sales & retail prices (res/com/ind, 50 states) | [EIA v2](https://www.eia.gov/opendata/) |
| **FRED** | State Coincident Index | [FRED API](https://fred.stlouisfed.org/) |
| **NOAA** | Heating & cooling degree-days (nClimDiv fixed-width files) | [NCEI bulk download](https://www.ncei.noaa.gov/pub/data/cirs/climdiv/) |

Everything is joined on `(state, YYYY-MM)` into a single panel covering 2001 -- 2024.

## Pipeline

```
collect  ->  clean  ->  signal  ->  eda
```

1. **collect** -- pull from the three APIs, merge into `panel.parquet`
2. **clean** -- missingness audit, outlier detection (rolling MAD + neighbor deviation), interpolation
3. **signal** -- OLS weather/price regression, STL seasonal decomposition, z-score standardization
4. **eda** -- eight figures exploring the electricity-economy relationship across states

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your EIA and FRED API keys
```

## Run

```bash
python -m src              # full pipeline (uses cache by default)
python -m src --no-cache   # re-download everything
```

Output lands in `data/` (parquet files) and `figures/` (png).
