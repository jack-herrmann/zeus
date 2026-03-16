Here's the plan, organized by phase. I'll map each piece to the rubric so nothing falls through the cracks.

---

## Phase 0 — Data Collection (Rubric: Data Collection)

This is where the complexity requirement gets satisfied. You're joining four distinct government data sources, each with its own format, API, and quirks.

**Source 1: EIA-861M — Monthly Electricity Sales by State and Sector.** The EIA provides a bulk data API. You'll pull monthly MWh sales for residential, commercial, and industrial sectors, for all 50 states plus DC. The series IDs follow a structured naming convention, so you'll programmatically construct ~153 series queries (3 sectors × 51 geographies). This is your REST API complexity.

**Source 2: Philadelphia Fed State Coincident Index.** Available as downloadable Excel files, one per state. You'll need to scrape or batch-download 50 files and parse them into a unified panel. Each file has its own date formatting.

**Source 3: NOAA Heating/Cooling Degree Days by State.** Available through NOAA's Climate Divisional Database or the nClimDiv dataset. Monthly state-level HDD and CDD. This requires either API calls or parsing fixed-width text files, then aggregating climate divisions up to state level.

**Source 4: EIA Retail Electricity Prices by State and Sector.** Same EIA API as Source 1, different series (cents/kWh instead of MWh). Another ~153 series queries.

The join complexity is real: you're aligning four sources on a shared (state, month) key, each with different date formats, geographic identifiers (FIPS vs. state abbreviation vs. full name), and temporal coverage windows.

---

## Phase 1 — Data Cleaning and Validation

**Date alignment.** Standardize all dates to a common `YYYY-MM` format. Identify the overlapping time window across all four sources — likely something like 2001–2024, but you'll let the data tell you.

**Geographic harmonization.** Map every source to a common state identifier (two-letter abbreviation is simplest). Watch for DC, territories, and aggregated "U.S. Total" rows that need to be dropped.

**Missing data audit.** For each (state, month) cell, flag missingness across all four sources. Visualize a missingness heatmap (states × months). Decide on a policy: drop state-months with any missing value, or interpolate small gaps. Document either way.

**Unit standardization.** Electricity in MWh (or GWh for readability), prices in cents/kWh, HDD/CDD in degree-days, index as-is (unitless).

**Outlier check.** Look for implausible spikes or zeros in electricity data — these happen when utilities report late or a state reclassifies a large customer between sectors.

---

## Phase 2 — Signal Extraction (Non-Weather, Non-Cyclic)

This is the processing core. The goal is to isolate the component of electricity use that reflects economic activity rather than seasons or temperature.

**Step 1: Weather adjustment.** For each state and sector, regress monthly electricity sales on HDD, CDD, and retail price:

$$\text{Elec}_{s,t}^{k} = \alpha + \beta_1 \cdot \text{HDD}_{s,t} + \beta_2 \cdot \text{CDD}_{s,t} + \beta_3 \cdot \text{Price}_{s,t}^{k} + \varepsilon_{s,t}$$

The residual $\varepsilon_{s,t}$ is weather- and price-adjusted electricity use. Run this separately for each (state, sector) pair.

**Step 2: Seasonal adjustment.** Apply a seasonal decomposition (STL or classical) to the residuals from Step 1 to strip out any remaining calendar-driven periodicity (e.g., holiday effects, fiscal-year patterns). Extract the trend + remainder component as your cleaned signal.

**Step 3: Standardization.** Normalize the cleaned signal within each state to zero mean and unit variance so that cross-state comparisons reflect relative movements, not level differences in economic size.

You now have, for every (state, month), three cleaned signals — one per sector — plus the coincident index.

---

## Phase 3 — Exploratory Data Analysis and Visualization (Rubric: Visualization + Storytelling)

This is the bulk of the poster content. Structure the visuals as a narrative arc.

**Visual 1 — Raw data overview.** Small-multiples line chart: raw electricity by sector for a handful of representative states (one large industrial like Texas, one service-economy like New York, one small like Vermont). Overlay the coincident index on a secondary axis. This is your "here's the question" opener.

**Visual 2 — Weather effect magnitude.** Before/after comparison showing raw vs. weather-adjusted electricity for one example state. Shows the audience why the adjustment matters.

**Visual 3 — Correlation heatmap.** For each sector, compute the Pearson correlation between the cleaned electricity signal and the coincident index across all states. Display as a 50-state × 3-sector heatmap. The hypothesis is that industrial and commercial columns are warmer (higher correlation) than residential.

**Visual 4 — Choropleth map.** Map the industrial-sector correlation onto a U.S. state map. This shows geographic variation — maybe manufacturing-heavy Midwest states show stronger links than finance-heavy states.

**Visual 5 — Time-series deep dives.** Pick 3–4 states with interesting patterns (strong link, weak link, structural break). Plot the cleaned industrial signal against the coincident index over time. Annotate recessions (2008, 2020) to show whether the signal captures downturns.

**Visual 6 — Sector comparison.** Box plots or violin plots of correlation coefficients by sector across all states. This is the key "industrial > commercial > residential" result in one clean visual.

**Visual 7 — Lag analysis.** Cross-correlation plots showing whether electricity leads, coincides with, or lags the index. If electricity leads by 1–2 months, that's your nowcasting justification.

---

## Phase 4 — Formal Analysis (Rubric: Data Analysis)

**Panel regression.** Fixed-effects regression of the coincident index on the three sector signals with state and time fixed effects, as described earlier. Report $\beta$ coefficients with standard errors. This quantifies the relationship.

**Granger causality tests.** For a subset of states, test whether lagged electricity Granger-causes the index. This formalizes the lead/lag finding from Phase 3.

**Principal component analysis.** Extract the first few PCs from the three sector signals across states. See if PC1 tracks the national business cycle.

**Rolling correlations.** Compute 24-month rolling correlations between industrial electricity and the index. Visualize whether the relationship is stable or has shifted over time (e.g., weakened as the economy deindustrialized).

---

## Phase 5 — Forecasting Add-On (Rubric: ML + Real-World Application)

**Nowcast model.** Train a simple model (Ridge or Random Forest) to predict this month's coincident index from this month's electricity signals plus one or two lags. Use an expanding-window cross-validation scheme so you never train on future data.

**Benchmark comparison.** Compare forecast accuracy (RMSE, MAE) against a naive benchmark (last month's index value). If the electricity model beats naive, you have a practical result.

**Live prediction.** Pull the most recent month of electricity data, feed it through the pipeline, and produce a prediction for the current coincident index value. When the Fed releases the actual number, compare. This is the "pans out" moment for the poster.

---

## Rubric Mapping Summary

The research question is cleanly motivated and has direct policy relevance (10-point target). Data collection involves four government APIs/sources with non-trivial joins (10-point target). Visualizations build a narrative arc from raw data through cleaned signals to results (10-point target). Analysis spans correlations, panel regression, Granger causality, PCA, and rolling windows — broad range (10-point target). The story follows a logical thread: question → data → cleaning → signal → pattern → model → prediction (10-point target). The real-world application is explicit: nowcasting state economic conditions from readily available electricity data (10-point target).
