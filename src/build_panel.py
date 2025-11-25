import pandas as pd
from pathlib import Path

DATA_PROCESSED_DIR = Path("data") / "processed"


def inspect_inputs():
    """
    Just prints basic info about the three input parquet files.
    """
    deaths_path = DATA_PROCESSED_DIR / "vital_stats_deaths_2006_2015.parquet"
    pop_path = DATA_PROCESSED_DIR / "us_population_condensed_2006_2015.parquet"
    arcos_path = DATA_PROCESSED_DIR / "arcos_county_year_with_fips.parquet"

    print("📂 Loading processed datasets...\n")

    deaths = pd.read_parquet(deaths_path)
    pop = pd.read_parquet(pop_path)
    arcos = pd.read_parquet(arcos_path)

    print("✅ vital_stats_deaths_2006_2015.parquet")
    print("   shape:", deaths.shape)
    print("   columns:", list(deaths.columns), "\n")

    print("✅ us_population_condensed_2006_2015.parquet")
    print("   shape:", pop.shape)
    print("   columns:", list(pop.columns), "\n")

    print("✅ arcos_county_year_with_fips.parquet")
    print("   shape:", arcos.shape)
    print("   columns:", list(arcos.columns), "\n")


def build_panel(
    output_path: Path = DATA_PROCESSED_DIR / "opioid_panel_2006_2015.parquet",
):
    """
    Merge deaths, population, and ARCOS to a single county-year panel.

    - Start from population (all county-years)
    - Left-join deaths and shipments
    - Compute drug death rate per 100k
    """

    deaths_path = DATA_PROCESSED_DIR / "vital_stats_deaths_2006_2015.parquet"
    pop_path = DATA_PROCESSED_DIR / "us_population_condensed_2006_2015.parquet"
    arcos_path = DATA_PROCESSED_DIR / "arcos_county_year_with_fips.parquet"

    pop = pd.read_parquet(pop_path)
    deaths = pd.read_parquet(deaths_path)
    arcos = pd.read_parquet(arcos_path)

    # Make sure fips is a 5-character string everywhere
    pop["fips"] = pop["fips"].astype(str).str.zfill(5)
    deaths["fips"] = deaths["fips"].astype(str).str.zfill(5)
    arcos["fips"] = arcos["fips"].astype(str).str.zfill(5)

    # ------ merge deaths onto population ------
    panel = pop.merge(
        deaths[["fips", "year", "drug_deaths"]],
        on=["fips", "year"],
        how="left",
    )

    # ------ merge ARCOS onto that ------
    panel = panel.merge(
        arcos[["fips", "year", "opioid_shipments_mme", "total_pills"]],
        on=["fips", "year"],
        how="left",
    )

    # ------ compute death rate per 100k ------
    panel["drug_death_rate_per_100k"] = (
        panel["drug_deaths"] / panel["population"] * 100000
    )

    print("✅ Merged panel created")
    print("   shape:", panel.shape)
    print("   columns:", list(panel.columns), "\n")

    print("   Non-missing drug_deaths:", panel["drug_deaths"].notna().sum())
    print(
        "   Non-missing opioid_shipments_mme:",
        panel["opioid_shipments_mme"].notna().sum(),
    )

    # save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, index=False)
    print(f"\n💾 Saved merged panel to {output_path}")


if __name__ == "__main__":
    inspect_inputs()
    build_panel()
