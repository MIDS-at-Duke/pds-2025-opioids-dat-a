import pandas as pd
from pathlib import Path

# Base directory for processed data
DATA_PROCESSED_DIR = Path("data") / "processed"


def inspect_inputs() -> None:
    """
    Print basic info about the three main processed parquet inputs.
    """
    deaths_path = DATA_PROCESSED_DIR / "vital_stats_deaths_2006_2015.parquet"
    pop_path = DATA_PROCESSED_DIR / "us_population_condensed_2006_2015.parquet"
    arcos_path = DATA_PROCESSED_DIR / "arcos_county_year_with_fips.parquet"

    print("📂 Loading processed datasets...\n")

    deaths = pd.read_parquet(deaths_path)
    pop = pd.read_parquet(pop_path)
    arcos = pd.read_parquet(arcos_path)

    print("vital_stats_deaths_2006_2015.parquet")
    print("   shape:", deaths.shape)
    print("   columns:", list(deaths.columns), "\n")

    print("us_population_condensed_2006_2015.parquet")
    print("   shape:", pop.shape)
    print("   columns:", list(pop.columns), "\n")

    print("arcos_county_year_with_fips.parquet")
    print("   shape:", arcos.shape)
    print("   columns:", list(arcos.columns), "\n")


def build_panel(
    output_path: Path = DATA_PROCESSED_DIR / "opioid_panel_2006_2015.parquet",
) -> None:
    """
    Merge deaths, population, and ARCOS to a single county-year panel.

    Steps:
    - Start from population (has all county-years)
    - Left-join drug overdose deaths
    - Left-join opioid shipments (MME & total pills)
    - Compute drug overdose death rate per 100k
    - Build Florida + controls analysis panel and drop counties with ANY missing deaths (any year)
    - Build Washington + controls analysis panel and drop counties with ANY missing deaths (any year)
    """

    deaths_path = DATA_PROCESSED_DIR / "vital_stats_deaths_2006_2015.parquet"
    pop_path = DATA_PROCESSED_DIR / "us_population_condensed_2006_2015.parquet"
    arcos_path = DATA_PROCESSED_DIR / "arcos_county_year_with_fips.parquet"

    # ----------------- load -----------------
    deaths = pd.read_parquet(deaths_path)
    pop = pd.read_parquet(pop_path)
    arcos = pd.read_parquet(arcos_path)

    # make sure fips is 5-char string everywhere
    for df in (deaths, pop, arcos):
        df["fips"] = df["fips"].astype(str).str.zfill(5)

    # ----------------- merge to full panel -----------------
    # start from population (complete grid of county-years)
    panel = pop.merge(
        deaths[["fips", "year", "drug_deaths"]],
        on=["fips", "year"],
        how="left",
    )

    panel = panel.merge(
        arcos[["fips", "year", "opioid_shipments_mme", "total_pills"]],
        on=["fips", "year"],
        how="left",
    )

    # drug overdose death rate per 100k population
    panel["drug_death_rate_per_100k"] = (
        panel["drug_deaths"] / panel["population"] * 100000
    )

    # some quick diagnostics on full panel
    print("Merged panel created")
    print("   shape:", panel.shape)
    print("   columns:", list(panel.columns), "\n")
    print("   Non-missing drug_deaths:", panel["drug_deaths"].notna().sum())
    print(
        "   Non-missing opioid_shipments_mme:",
        panel["opioid_shipments_mme"].notna().sum(),
    )

    # save full panel
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, index=False)
    print(f"\n💾 Saved merged panel to {output_path}")

    # =====================================================
    # FLORIDA ANALYSIS PANEL (FL + control states)
    # =====================================================
    FL_POLICY_YEAR = 2010
    fl_states = ["FL", "GA", "AL", "SC", "NC", "TN", "MS"]

    fl_panel = panel[panel["state_abbrev"].isin(fl_states)].copy()

    # Drop any county (fips) that has missing drug_deaths in ANY year (2006–2015)
    fl_bad_fips = fl_panel.groupby("fips")["drug_deaths"].apply(
        lambda x: x.isna().any()
    )
    fl_bad_fips = fl_bad_fips[fl_bad_fips].index.tolist()

    print(
        "\nNumber of FL-analysis counties DROPPED due to ANY NA in drug_deaths (any year):",
        len(fl_bad_fips),
    )

    fl_panel_clean = fl_panel[~fl_panel["fips"].isin(fl_bad_fips)].copy()

    # is_pre flag still useful for some analyses
    fl_panel_clean["is_pre"] = (fl_panel_clean["year"] < FL_POLICY_YEAR).astype(int)

    print("Final FL panel shape:", fl_panel_clean.shape)

    fl_out = DATA_PROCESSED_DIR / "fl_panel_clean.parquet"
    fl_panel_clean.to_parquet(fl_out, index=False)
    print(f"Saved clean Florida panel to: {fl_out}")

    # =====================================================
    # WASHINGTON ANALYSIS PANEL (WA + control states)
    # =====================================================
    WA_POLICY_YEAR = 2012
    wa_states = ["WA", "OR", "CO", "MN", "NV", "CA", "VA"]

    wa_panel = panel[panel["state_abbrev"].isin(wa_states)].copy()

    # Drop any county (fips) that has missing drug_deaths in ANY year (2006–2015)
    wa_bad_fips = wa_panel.groupby("fips")["drug_deaths"].apply(
        lambda x: x.isna().any()
    )
    wa_bad_fips = wa_bad_fips[wa_bad_fips].index.tolist()

    print(
        "\nNumber of WA-analysis counties DROPPED due to ANY NA in drug_deaths (any year):",
        len(wa_bad_fips),
    )

    wa_panel_clean = wa_panel[~wa_panel["fips"].isin(wa_bad_fips)].copy()

    wa_panel_clean["is_pre"] = (wa_panel_clean["year"] < WA_POLICY_YEAR).astype(int)

    print("✅ Final WA panel shape:", wa_panel_clean.shape)

    wa_out = DATA_PROCESSED_DIR / "wa_panel_clean.parquet"
    wa_panel_clean.to_parquet(wa_out, index=False)
    print(f"💾 Saved clean Washington panel to: {wa_out}")


if __name__ == "__main__":
    inspect_inputs()
    build_panel()
