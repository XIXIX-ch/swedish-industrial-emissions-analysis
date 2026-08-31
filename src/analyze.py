"""Reproduce the Swedish E-PRTR industrial air-emissions analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import pandas as pd
import plotly.express as px

matplotlib.use("Agg")
import matplotlib.pyplot as plt

YEARS = [str(year) for year in range(2018, 2025)]
CO2 = "Carbon dioxide (CO2) excluding biomass"
FOCUS_POLLUTANTS = [
    CO2,
    "Ammonia (NH3)",
    "Nitrogen oxides (NOX)",
    "Nitrous oxide (N2O)",
    "Non-methane volatile organic compounds (NMVOC)",
    "Particulate matter (PM10)",
]
SHORT_NAMES = {
    CO2: "CO2",
    "Ammonia (NH3)": "NH3",
    "Nitrogen oxides (NOX)": "NOX",
    "Nitrous oxide (N2O)": "N2O",
    "Non-methane volatile organic compounds (NMVOC)": "NMVOC",
    "Particulate matter (PM10)": "PM10",
}
SECTOR_NAMES = {
    "1": "Energy",
    "2": "Production and processing of metals",
    "3": "Mineral industry",
    "4": "Chemical industry",
    "5": "Waste and wastewater management",
    "6": "Paper and wood production",
    "7": "Intensive livestock and aquaculture",
    "8": "Food and beverage sector",
    "9": "Other activities",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("EEA_Industry_Dataset_EPRTR_Air_Releases.xlsx"),
        help="Path to the EEA Excel workbook.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for generated figures, tables, and interactive output.",
    )
    return parser.parse_args()


def load_and_validate(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not path.exists():
        raise FileNotFoundError(
            f"Source workbook not found: {path}. See DATA.md for download instructions."
        )
    facilities = pd.read_excel(path, sheet_name="Air_Releases_Facilities")
    national = pd.read_excel(path, sheet_name="Air_Releases_National")
    required = {
        "countryName",
        "FacilityInspireId",
        "facilityName",
        "city",
        "Longitude",
        "Latitude",
        "EPRTRAnnexIMainActivity",
        "TargetRelease",
        "Pollutant",
        *YEARS,
    }
    missing = sorted(required.difference(facilities.columns))
    if missing:
        raise ValueError(f"Facility sheet is missing required columns: {missing}")
    sweden = facilities.loc[facilities["countryName"].eq("Sweden")].copy()
    duplicates = sweden.duplicated(["FacilityInspireId", "Pollutant"]).sum()
    if duplicates:
        raise ValueError(
            f"Found {duplicates} duplicate facility-pollutant records; "
            "aggregation would double count releases."
        )
    return sweden, national


def reshape(sweden: pd.DataFrame) -> pd.DataFrame:
    id_columns = [
        "FacilityInspireId",
        "facilityName",
        "city",
        "Longitude",
        "Latitude",
        "EPRTRAnnexIMainActivity",
        "TargetRelease",
        "Pollutant",
    ]
    long = sweden.melt(
        id_vars=id_columns,
        value_vars=YEARS,
        var_name="Year",
        value_name="Emission_kg",
    )
    long["Year"] = long["Year"].astype(int)
    long["Emission_kg"] = pd.to_numeric(long["Emission_kg"], errors="coerce")
    if (long["Emission_kg"].dropna() < 0).any():
        raise ValueError("Negative release values found in the selected period.")
    return long


def build_tables(
    long: pd.DataFrame, national: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    focus = long.loc[long["Pollutant"].isin(FOCUS_POLLUTANTS)].copy()
    availability = (
        focus.groupby(["Pollutant", "Year"])["Emission_kg"]
        .agg(total_records="size", reported_values="count")
        .reset_index()
    )
    availability["value_availability_pct"] = (
        availability["reported_values"] / availability["total_records"] * 100
    ).round(1)

    reported = focus.dropna(subset=["Emission_kg"]).copy()
    counts = (
        reported.groupby(["Pollutant", "FacilityInspireId"])["Year"]
        .nunique()
        .rename("years_reported")
        .reset_index()
    )
    panel_ids = counts.loc[counts["years_reported"].eq(len(YEARS))]
    panel = reported.merge(
        panel_ids[["Pollutant", "FacilityInspireId"]],
        on=["Pollutant", "FacilityInspireId"],
        how="inner",
        validate="many_to_one",
    )
    annual = (
        panel.groupby(["Pollutant", "Year"], as_index=False)["Emission_kg"]
        .sum()
        .rename(columns={"Emission_kg": "TotalEmission_kg"})
        .sort_values(["Pollutant", "Year"])
    )
    baseline = annual.loc[annual["Year"].eq(2018), ["Pollutant", "TotalEmission_kg"]]
    baseline = baseline.rename(columns={"TotalEmission_kg": "Baseline_2018_kg"})
    annual = annual.merge(baseline, on="Pollutant", validate="many_to_one")
    annual["Index_2018_100"] = (
        annual["TotalEmission_kg"] / annual["Baseline_2018_kg"] * 100
    ).round(1)
    annual["TotalEmission_tonnes"] = annual["TotalEmission_kg"] / 1_000

    summary = annual.pivot(
        index="Pollutant", columns="Year", values="TotalEmission_tonnes"
    )[[2018, 2024]].rename(
        columns={2018: "Emission_2018_tonnes", 2024: "Emission_2024_tonnes"}
    )
    summary["Change_pct"] = (
        (summary["Emission_2024_tonnes"] / summary["Emission_2018_tonnes"] - 1)
        * 100
    ).round(1)
    summary.insert(
        0,
        "Stable_facilities",
        panel_ids.groupby("Pollutant")["FacilityInspireId"].nunique(),
    )
    summary = summary.reset_index()

    co2 = reported.loc[(reported["Pollutant"].eq(CO2)) & reported["Year"].eq(2024)].copy()
    co2["Emission_tonnes"] = co2["Emission_kg"] / 1_000
    co2["SectorCode"] = co2["EPRTRAnnexIMainActivity"].astype("string").str.extract(
        r"^(\d+)", expand=False
    )
    co2["Sector"] = co2["SectorCode"].map(SECTOR_NAMES).fillna("Unknown")
    co2 = co2.sort_values("Emission_tonnes", ascending=False).reset_index(drop=True)
    top10 = co2[
        [
            "facilityName",
            "city",
            "EPRTRAnnexIMainActivity",
            "Sector",
            "Emission_tonnes",
            "Longitude",
            "Latitude",
        ]
    ].head(10).copy()
    top10.insert(0, "Rank", range(1, len(top10) + 1))
    sector = (
        co2.groupby("Sector", as_index=False)
        .agg(
            Facilities=("FacilityInspireId", "nunique"),
            Emission_tonnes=("Emission_tonnes", "sum"),
        )
        .sort_values("Emission_tonnes", ascending=False)
    )
    sector["Emission_Mt"] = sector["Emission_tonnes"] / 1_000_000
    sector["Share_pct"] = (
        sector["Emission_tonnes"] / sector["Emission_tonnes"].sum() * 100
    ).round(1)

    national_value = national.loc[
        national["countryName"].eq("Sweden") & national["Pollutant"].eq(CO2), "2024"
    ]
    if len(national_value) != 1:
        raise ValueError("Expected exactly one Swedish national CO2 record for 2024.")
    if not pd.isna(national_value.iloc[0]) and not abs(
        co2["Emission_kg"].sum() - national_value.iloc[0]
    ) < 1:
        raise ValueError("Facility CO2 total does not reconcile to the national sheet.")

    return {
        "availability": availability,
        "annual": annual.drop(columns="Baseline_2018_kg"),
        "summary": summary,
        "co2": co2,
        "top10": top10,
        "sector": sector,
    }


def save_outputs(tables: dict[str, pd.DataFrame], output_dir: Path) -> None:
    figures_dir = output_dir / "figures"
    tables_dir = output_dir / "tables"
    interactive_dir = output_dir / "interactive"
    for directory in (figures_dir, tables_dir, interactive_dir):
        directory.mkdir(parents=True, exist_ok=True)

    annual = tables["annual"]
    trend = annual.pivot(index="Year", columns="Pollutant", values="Index_2018_100")
    trend = trend.rename(columns=SHORT_NAMES)
    fig, ax = plt.subplots(figsize=(11, 6))
    for pollutant in trend.columns:
        ax.plot(trend.index, trend[pollutant], marker="o", linewidth=2, label=pollutant)
    ax.axhline(100, color="black", linestyle="--", linewidth=1)
    ax.set(
        title="Swedish Industrial Air Emissions Trend\nConsistent Reporters, 2018–2024",
        xlabel="Year",
        ylabel="Emission Index (2018 = 100)",
    )
    ax.grid(alpha=0.25)
    ax.legend(title="Pollutant", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(figures_dir / "emission_trend_index_2018_2024.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    coverage = tables["availability"].pivot(
        index="Year", columns="Pollutant", values="value_availability_pct"
    ).rename(columns=SHORT_NAMES)
    fig, ax = plt.subplots(figsize=(11, 6))
    for pollutant in coverage.columns:
        ax.plot(coverage.index, coverage[pollutant], marker="o", linewidth=2, label=pollutant)
    ax.set(
        title="Availability of Reported E-PRTR Air Release Values\nSwedish Facility–Pollutant Records, 2018–2024",
        xlabel="Year",
        ylabel="Records with a reported value (%)",
        ylim=(0, 100),
    )
    ax.grid(alpha=0.25)
    ax.legend(title="Pollutant", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.text(
        0.5,
        -0.01,
        "Blank values can reflect releases below E-PRTR reporting thresholds.",
        ha="center",
        fontsize=9,
        color="dimgray",
    )
    fig.tight_layout()
    fig.savefig(figures_dir / "reporting_coverage_2018_2024.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    top10 = tables["top10"].copy()
    top10["Emission_Mt"] = top10["Emission_tonnes"] / 1_000_000
    top10["Label"] = top10["facilityName"] + " (" + top10["city"].str.title() + ")"
    top10 = top10.sort_values("Emission_Mt")
    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(top10["Label"], top10["Emission_Mt"], color="#4472C4")
    ax.set(
        title="Top 10 Reported Industrial CO₂ Emitters in Sweden, 2024\nCO₂ Excluding Biomass",
        xlabel="Reported CO₂ Releases (million tonnes/year)",
        ylabel="Facility",
    )
    ax.grid(axis="x", alpha=0.25)
    ax.bar_label(bars, fmt="%.2f", padding=3)
    fig.tight_layout()
    fig.savefig(figures_dir / "top10_co2_facilities_2024.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    sector = tables["sector"].sort_values("Share_pct").copy()
    sector["Label"] = sector["Sector"] + " (n=" + sector["Facilities"].astype(str) + ")"
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(sector["Label"], sector["Share_pct"], color="#70AD47")
    ax.set(
        title="Sector Contribution to Reported Industrial CO₂ Releases\nSweden, 2024 — CO₂ Excluding Biomass",
        xlabel="Share of Reported CO₂ Releases (%)",
        ylabel="E-PRTR Sector",
    )
    ax.grid(axis="x", alpha=0.25)
    ax.bar_label(bars, fmt="%.1f%%", padding=3)
    ax.set_xlim(0, sector["Share_pct"].max() + 7)
    fig.tight_layout()
    fig.savefig(figures_dir / "co2_sector_contribution_2024.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    map_data = tables["co2"].copy()
    valid = map_data["Longitude"].between(10, 25) & map_data["Latitude"].between(54, 70)
    map_data = map_data.loc[valid].copy()
    map_data["Emission_Mt"] = map_data["Emission_tonnes"] / 1_000_000
    fig = px.scatter_geo(
        map_data,
        lat="Latitude",
        lon="Longitude",
        size="Emission_Mt",
        color="Sector",
        hover_name="facilityName",
        hover_data={
            "city": True,
            "Emission_Mt": ":.3f",
            "EPRTRAnnexIMainActivity": True,
            "Latitude": False,
            "Longitude": False,
        },
        size_max=35,
        projection="mercator",
        title=(
            "Reported Industrial CO₂ Releases in Sweden, 2024"
            "<br><sup>CO₂ excluding biomass; bubble size represents reported releases</sup>"
        ),
    )
    fig.update_geos(
        fitbounds="locations",
        showland=True,
        landcolor="#F2F2F2",
        showocean=True,
        oceancolor="#DDEBF7",
        showcountries=True,
        showcoastlines=True,
    )
    fig.update_layout(height=750, margin={"l": 20, "r": 20, "t": 90, "b": 20})
    fig.write_html(
        interactive_dir / "sweden_co2_facilities_2024.html",
        include_plotlyjs="cdn",
        full_html=True,
    )

    tables["annual"].to_csv(tables_dir / "annual_emission_trends.csv", index=False)
    tables["summary"].to_csv(tables_dir / "trend_summary_2018_2024.csv", index=False)
    tables["availability"].to_csv(
        tables_dir / "reported_value_availability.csv", index=False
    )
    tables["top10"].to_csv(tables_dir / "top10_co2_facilities_2024.csv", index=False)
    tables["sector"].to_csv(tables_dir / "co2_sector_summary_2024.csv", index=False)


def main() -> None:
    args = parse_args()
    sweden, national = load_and_validate(args.input)
    long = reshape(sweden)
    tables = build_tables(long, national)
    save_outputs(tables, args.output_dir)
    co2_total_mt = tables["co2"]["Emission_tonnes"].sum() / 1_000_000
    print(f"Analysis complete: {co2_total_mt:.2f} Mt CO2 reported in 2024")
    print(f"Outputs written to: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
