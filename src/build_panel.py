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

    # =====================================================
    # IMPUTE SUPPRESSED DEATH VALUES (< 10)
    # CDC suppresses death counts < 10 for privacy
    # Approach (per TA guidance):
    #   1. Calculate avg death rate from observed data
    #   2. Predict expected deaths = rate * population / 100k
    #   3. Round to integers, clip to [0, 9]
    # =====================================================
    import numpy as np
    
    print("\n" + "=" * 60)
    print("IMPUTING SUPPRESSED DEATH VALUES")
    print("=" * 60)
    
    # Separate observed vs missing
    observed_mask = panel["drug_deaths"].notna()
    missing_mask = panel["drug_deaths"].isna()
    
    n_observed = observed_mask.sum()
    n_missing = missing_mask.sum()
    print(f"   Observed deaths: {n_observed:,} ({100*n_observed/len(panel):.1f}%)")
    print(f"   Missing (suppressed <10): {n_missing:,} ({100*n_missing/len(panel):.1f}%)")
    
    # Calculate average death rate from observed data
    observed = panel[observed_mask].copy()
    observed["death_rate"] = observed["drug_deaths"] / observed["population"] * 100000
    avg_rate = observed["death_rate"].mean()
    print(f"   Average death rate (observed): {avg_rate:.1f} per 100k")
    
    # Predict expected deaths for missing values
    # expected_deaths = rate * population / 100000
    predicted_raw = avg_rate * panel.loc[missing_mask, "population"] / 100000
    
    # Clip to integers [0, 9] since suppressed means < 10
    predicted_clipped = np.clip(np.round(predicted_raw), 0, 9).astype(int)
    
    print(f"   Imputed values distribution:")
    for v in range(10):
        count = (predicted_clipped == v).sum()
        pct = 100 * count / len(predicted_clipped) if len(predicted_clipped) > 0 else 0
        print(f"      {v}: {count:,} ({pct:.1f}%)")
    
    # Fill missing values
    panel.loc[missing_mask, "drug_deaths"] = predicted_clipped.values
    
    # Add flag for imputed values
    panel["death_imputed"] = missing_mask.astype(int)
    
    # Recalculate death rate with imputed values
    panel["drug_death_rate_per_100k"] = (
        panel["drug_deaths"] / panel["population"] * 100000
    )
    
    print(f"\n   ✓ Imputation complete!")
    print(f"   Remaining missing drug_deaths: {panel['drug_deaths'].isna().sum()}")
    print("=" * 60)

    # save full panel (with imputed values)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, index=False)
    print(f"\n💾 Saved merged full panel (with imputation) to {output_path}")

    # =====================================================
    # FLORIDA ANALYSIS PANEL (FL + control states)
    # =====================================================
    FL_POLICY_YEAR = 2010
    fl_states = ["FL", "GA", "AL", "SC", "NC", "TN", "MS"]

    fl_panel = panel[panel["state_abbrev"].isin(fl_states)].copy()
    fl_panel["is_pre"] = (fl_panel["year"] < FL_POLICY_YEAR).astype(int)

    # No longer dropping counties for missing deaths (values are imputed)
    # Only drop YEAR-LEVEL rows with missing MME
    before_rows = fl_panel.shape[0]
    fl_panel_clean = fl_panel[
        fl_panel["opioid_shipments_mme"].notna()
    ].copy()
    after_rows = fl_panel_clean.shape[0]

    print(f"\n[FL] Florida + controls panel")
    print(f"   Total rows: {before_rows:,}")
    print(f"   Dropped for missing MME: {before_rows - after_rows:,}")
    print(f"   Final shape: {fl_panel_clean.shape}")
    print(f"   Counties: {fl_panel_clean['fips'].nunique()}")
    print(f"   Imputed death observations: {fl_panel_clean['death_imputed'].sum():,}")

    fl_out = DATA_PROCESSED_DIR / "fl_panel_clean.parquet"
    fl_panel_clean.to_parquet(fl_out, index=False)
    print(f"   Saved: {fl_out}")

    # =====================================================
    # WASHINGTON ANALYSIS PANEL (WA + control states)
    # =====================================================
    WA_POLICY_YEAR = 2012
    wa_states = ["WA", "OR", "CO", "MN", "NV", "CA", "VA"]

    wa_panel = panel[panel["state_abbrev"].isin(wa_states)].copy()
    wa_panel["is_pre"] = (wa_panel["year"] < WA_POLICY_YEAR).astype(int)

    # No longer dropping counties for missing deaths (values are imputed)
    # Only drop YEAR-LEVEL rows with missing MME
    before_rows_wa = wa_panel.shape[0]
    wa_panel_clean = wa_panel[
        wa_panel["opioid_shipments_mme"].notna()
    ].copy()
    after_rows_wa = wa_panel_clean.shape[0]

    print(f"\n[WA] Washington + controls panel")
    print(f"   Total rows: {before_rows_wa:,}")
    print(f"   Dropped for missing MME: {before_rows_wa - after_rows_wa:,}")
    print(f"   Final shape: {wa_panel_clean.shape}")
    print(f"   Counties: {wa_panel_clean['fips'].nunique()}")
    print(f"   Imputed death observations: {wa_panel_clean['death_imputed'].sum():,}")

    wa_out = DATA_PROCESSED_DIR / "wa_panel_clean.parquet"
    wa_panel_clean.to_parquet(wa_out, index=False)
    print(f"   Saved: {wa_out}")


if __name__ == "__main__":
    inspect_inputs()
    build_panel()
