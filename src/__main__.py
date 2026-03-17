import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("zeus")


def main():
    parser = argparse.ArgumentParser(description="ZEUS data collection pipeline")
    parser.add_argument(
        "--no-cache", action="store_true", help="Re-download all data (ignore cache)"
    )
    args = parser.parse_args()
    use_cache = not args.no_cache

    from src.collect import eia, fred, noaa
    from src.collect.merge import merge_panel
    from src.collect.validate import validate_panel

    sources = {}
    for name, fetcher in [("EIA", eia), ("FRED", fred), ("NOAA", noaa)]:
        try:
            logger.info("Collecting %s...", name)
            sources[name] = fetcher.fetch_all(use_cache=use_cache)
        except Exception:
            logger.exception("Failed to collect %s", name)

    if len(sources) < 3:
        failed = {"EIA", "FRED", "NOAA"} - sources.keys()
        logger.error("Missing sources: %s — cannot build full panel", failed)
        sys.exit(1)

    logger.info("Merging into panel...")
    panel = merge_panel(sources["EIA"], sources["FRED"], sources["NOAA"])

    logger.info("Validating panel...")
    issues = validate_panel(panel)
    if issues:
        for issue in issues:
            logger.warning(issue)
    else:
        logger.info("All validation checks passed.")

    logger.info("--- Panel Summary ---")
    logger.info("Shape: %s", panel.shape)
    logger.info("States: %d", panel["state"].nunique())
    logger.info("Periods: %s to %s", panel["period"].min(), panel["period"].max())
    logger.info("Columns: %s", list(panel.columns))
    logger.info("NaN overview:\n%s", panel.isna().sum().to_string())

    from src.clean.pipeline import clean_panel

    logger.info("Phase 1: Cleaning panel...")
    panel_clean = clean_panel(panel)
    logger.info("Phase 1 complete. Clean panel shape: %s", panel_clean.shape)

    from src.signal.pipeline import extract_signal

    logger.info("Phase 2: Extracting economic signal...")
    panel_signal = extract_signal(panel_clean)
    logger.info("Phase 2 complete. Signal panel shape: %s", panel_signal.shape)

    from src.eda.pipeline import run_eda

    logger.info("Phase 3: Exploratory data analysis...")
    run_eda()
    logger.info("Phase 3 complete. Figures saved to figures/")


if __name__ == "__main__":
    main()
