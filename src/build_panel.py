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
    - Build Florida + controls analysis panel:
        * Drop counties with ANY missing deaths (any year, pre or post)
        * Then drop YEAR-LEVEL rows with missing MME
    - Build Washington + controls analysis panel:
        * Same rules as Florida
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

    # save full panel (unaltered) in case anything else uses it
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, index=False)
    print(f"\n💾 Saved merged full panel to {output_path}")

    # =====================================================
    # FLORIDA ANALYSIS PANEL (FL + control states)
    # =====================================================
    FL_POLICY_YEAR = 2010
    fl_states = ["FL", "GA", "AL", "SC", "NC", "TN", "MS"]

    fl_panel = panel[panel["state_abbrev"].isin(fl_states)].copy()
    fl_panel["is_pre"] = (fl_panel["year"] < FL_POLICY_YEAR).astype(int)

    # ---- 1) Drop counties with ANY missing deaths (any year) ----
    fl_bad_death_fips = fl_panel.groupby("fips")["drug_deaths"].apply(
        lambda x: x.isna().any()
    )
    fl_bad_death_fips = fl_bad_death_fips[fl_bad_death_fips].index.tolist()

    print(
        "\n[FL] Number of counties DROPPED due to ANY NA in drug_deaths (2006–2015):",
        len(fl_bad_death_fips),
    )

    fl_panel_clean = fl_panel[~fl_panel["fips"].isin(fl_bad_death_fips)].copy()

    # ---- 2) Drop YEAR-LEVEL rows with missing MME (keep county, lose year) ----
    before_rows = fl_panel_clean.shape[0]
    fl_panel_clean = fl_panel_clean[
        fl_panel_clean["opioid_shipments_mme"].notna()
    ].copy()
    after_rows = fl_panel_clean.shape[0]

    print(
        "[FL] Year-level rows dropped due to NA opioid_shipments_mme:",
        before_rows - after_rows,
    )
    print("[FL] Final FL panel shape:", fl_panel_clean.shape)

    fl_out = DATA_PROCESSED_DIR / "fl_panel_clean.parquet"
    fl_panel_clean.to_parquet(fl_out, index=False)
    print(f"[FL] Saved clean Florida analysis panel to: {fl_out}")

    # =====================================================
    # WASHINGTON ANALYSIS PANEL (WA + control states)
    # =====================================================
    WA_POLICY_YEAR = 2012
    wa_states = ["WA", "OR", "CO", "MN", "NV", "CA", "VA"]

    wa_panel = panel[panel["state_abbrev"].isin(wa_states)].copy()
    wa_panel["is_pre"] = (wa_panel["year"] < WA_POLICY_YEAR).astype(int)

    # ---- 1) Drop counties with ANY missing deaths (any year) ----
    wa_bad_death_fips = wa_panel.groupby("fips")["drug_deaths"].apply(
        lambda x: x.isna().any()
    )
    wa_bad_death_fips = wa_bad_death_fips[wa_bad_death_fips].index.tolist()

    print(
        "\n[WA] Number of counties DROPPED due to ANY NA in drug_deaths (2006–2015):",
        len(wa_bad_death_fips),
    )

    wa_panel_clean = wa_panel[~wa_panel["fips"].isin(wa_bad_death_fips)].copy()

    # ---- 2) Drop YEAR-LEVEL rows with missing MME (keep county, lose year) ----
    before_rows_wa = wa_panel_clean.shape[0]
    wa_panel_clean = wa_panel_clean[
        wa_panel_clean["opioid_shipments_mme"].notna()
    ].copy()
    after_rows_wa = wa_panel_clean.shape[0]

    print(
        "[WA] Year-level rows dropped due to NA opioid_shipments_mme:",
        before_rows_wa - after_rows_wa,
    )
    print("[WA] Final WA panel shape:", wa_panel_clean.shape)

    wa_out = DATA_PROCESSED_DIR / "wa_panel_clean.parquet"
    wa_panel_clean.to_parquet(wa_out, index=False)
    print(f"[WA] Saved clean Washington analysis panel to: {wa_out}")


if __name__ == "__main__":
    inspect_inputs()
    build_panel()
