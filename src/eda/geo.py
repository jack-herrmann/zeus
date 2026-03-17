import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, PROJECT_ROOT

from .style import (
    DIVERGING_CMAP,
    SEQUENTIAL_CMAP,
    pick_key_states,
    save_figure,
    zeus_style,
)

logger = logging.getLogger("zeus.eda.geo")

_GEO_DIR = PROJECT_ROOT / "data" / "geo"
_SHAPEFILE = _GEO_DIR / "cb_2023_us_state_500k.zip"

FIPS_EXCLUDE = {"02", "15", "60", "66", "69", "72", "78"}


def load_states_gdf():
    import geopandas as gpd

    if not _SHAPEFILE.exists():
        raise FileNotFoundError(
            f"Shapefile not found at {_SHAPEFILE}. "
            "Download cb_2023_us_state_500k.zip from Census Bureau."
        )

    gdf = gpd.read_file(f"zip://{_SHAPEFILE}")
    gdf = gdf[~gdf["STATEFP"].isin(FIPS_EXCLUDE)].copy()
    gdf = gdf.to_crs("ESRI:102003")
    return gdf


def _annotate_extremes(ax, gdf, values_col, top_n, bottom_n):
    merged = gdf.dropna(subset=[values_col])
    if merged.empty:
        return

    sorted_df = merged.sort_values(values_col, ascending=False)

    label_states = pd.concat([sorted_df.head(top_n), sorted_df.tail(bottom_n)])
    for _, row in label_states.iterrows():
        centroid = row.geometry.centroid
        val = row[values_col]
        ax.annotate(
            f"{row['STUSPS']}: {val:+.2f}" if val < 0 else f"{row['STUSPS']}: {val:.2f}",
            xy=(centroid.x, centroid.y),
            fontsize=7, fontweight="bold", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", alpha=0.7, lw=0),
        )


def plot_industrial_share(df: pd.DataFrame) -> None:
    df = df.copy()
    total = df["sales_res"] + df["sales_com"] + df["sales_ind"]
    df["ind_share"] = df["sales_ind"] / total * 100
    share_by_state = df.groupby("state")["ind_share"].mean()

    gdf = load_states_gdf()
    gdf = gdf.merge(
        share_by_state.rename("ind_share").reset_index().rename(columns={"state": "STUSPS"}),
        on="STUSPS", how="left",
    )

    max_row = gdf.loc[gdf["ind_share"].idxmax()]
    min_row = gdf.loc[gdf["ind_share"].idxmin()]

    with zeus_style():
        fig, ax = plt.subplots(1, 1, figsize=(12, 7))
        gdf.plot(
            column="ind_share", cmap="Blues", ax=ax,
            edgecolor="white", linewidth=0.5,
            legend=True,
            legend_kwds={"label": "Industrial Share (%)", "shrink": 0.6},
            vmin=0, vmax=100,
        )

        for row in [max_row, min_row]:
            c = row.geometry.centroid
            ax.annotate(
                f"{row['STUSPS']}  {row['ind_share']:.0f}%",
                xy=(c.x, c.y), fontsize=9, fontweight="bold",
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.8, lw=0),
            )

        ax.set_title(
            "What Share of Each State's Electricity Goes to Industry?",
            fontsize=14, fontweight="bold",
        )
        ax.set_axis_off()
        save_figure(fig, "v2_industrial_share")


def plot_growth_comparison(df: pd.DataFrame) -> None:
    import matplotlib.ticker as mticker

    early = df[df["period"] < "2003-01"].groupby("state")
    late = df[df["period"] >= "2023-01"].groupby("state")

    ind_growth = ((late["sales_ind"].mean() / early["sales_ind"].mean()) - 1) * 100
    ci_growth = ((late["coincident_index"].mean() / early["coincident_index"].mean()) - 1) * 100

    growth_df = pd.DataFrame({"ind_growth": ind_growth, "ci_growth": ci_growth}).reset_index()
    growth_df = growth_df.rename(columns={"state": "STUSPS"})

    # save ND original before clip
    nd_orig = growth_df.loc[growth_df["STUSPS"] == "ND", "ind_growth"].values[0]

    gdf = load_states_gdf()
    gdf = gdf.merge(growth_df, on="STUSPS", how="left")

    # clip to [-100, 100]
    gdf["ind_growth_clipped"] = gdf["ind_growth"].clip(-100, 100)
    gdf["ci_growth_clipped"] = gdf["ci_growth"].clip(-100, 100)

    cmap = "RdYlGn"

    with zeus_style():
        fig, (ax1, ax2) = plt.subplots(
            1, 2, figsize=(16, 7),
            gridspec_kw={"wspace": 0.02},
        )

        gdf.plot(
            column="ind_growth_clipped", cmap=cmap, ax=ax1,
            edgecolor="white", linewidth=0.5,
            legend=True,
            legend_kwds={"label": "% Change", "shrink": 0.55},
            vmin=-100, vmax=100,
        )
        ax1.set_title(
            "How Much Did Industrial\nElectricity Change?",
            fontsize=12, fontweight="bold",
        )
        ax1.set_axis_off()

        # label ND with unclipped value
        nd_row = gdf[gdf["STUSPS"] == "ND"].iloc[0]
        c = nd_row.geometry.centroid
        ax1.annotate(
            f"ND  +{nd_orig:.0f}%",
            xy=(c.x, c.y), fontsize=8, fontweight="bold",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.85, lw=0),
        )

        # "100" -> "100+"
        cb1 = ax1.get_figure().axes[-1]
        cb1.yaxis.set_major_formatter(
            mticker.FuncFormatter(
                lambda x, _: f"{x:+.0f}%" if abs(x) < 100 else f"{x:+.0f}%+"
            )
        )

        gdf.plot(
            column="ci_growth_clipped", cmap=cmap, ax=ax2,
            edgecolor="white", linewidth=0.5,
            legend=True,
            legend_kwds={"label": "% Change", "shrink": 0.55},
            vmin=-100, vmax=100,
        )
        ax2.set_title(
            "How Much Did the\nEconomy Grow?",
            fontsize=12, fontweight="bold",
        )
        ax2.set_axis_off()

        cb2 = ax2.get_figure().axes[-1]
        cb2.yaxis.set_major_formatter(
            mticker.FuncFormatter(
                lambda x, _: f"{x:+.0f}%" if abs(x) < 100 else f"{x:+.0f}%+"
            )
        )

        fig.suptitle(
            "Growth in Industrial Electricity vs. Growth in the Economy (2001–2024)",
            fontsize=14, fontweight="bold", y=0.97,
        )
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        save_figure(fig, "v3_growth_comparison")


def plot_deindustrialization_map(corr_df: pd.DataFrame) -> None:
    ind_corr = corr_df[corr_df["sector"] == "ind"][["state", "r_detrended"]].copy()
    ind_corr = ind_corr.rename(columns={"state": "STUSPS"})

    gdf = load_states_gdf()
    gdf = gdf.merge(ind_corr, on="STUSPS", how="left")

    key_states = pick_key_states(corr_df)

    with zeus_style():
        fig, ax = plt.subplots(1, 1, figsize=(13, 8))
        gdf.plot(
            column="r_detrended", cmap="RdYlGn", ax=ax,
            edgecolor="white", linewidth=0.5,
            legend=True,
            legend_kwds={"label": "Correlation", "shrink": 0.6},
            vmin=-1.0, vmax=1.0,
        )

        for abbr, _name, _r_val, color in key_states:
            row = gdf[gdf["STUSPS"] == abbr].iloc[0]
            c = row.geometry.centroid
            val = row["r_detrended"]
            ax.annotate(
                f"{abbr}  {val:+.2f}",
                xy=(c.x, c.y), fontsize=9, fontweight="bold",
                ha="center", va="center", color=color,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.8, lw=0),
            )

        ax.set_title(
            "Where Does Industrial Electricity Track the Economy?",
            fontsize=15, fontweight="bold",
        )
        ax.text(
            0.5, -0.02, "AK & HI excluded",
            transform=ax.transAxes, ha="center", fontsize=9, color="gray",
        )
        ax.set_axis_off()
        save_figure(fig, "v5_deindustrialization_map")
