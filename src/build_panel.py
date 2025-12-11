import pandas as pd
import numpy as np
from pathlib import Path

# Base directory where processed parquet files live
DATA_PROCESSED_DIR = Path("data") / "processed"


def inspect_inputs():
    """Print basic info about the three main processed parquet inputs."""
    deaths_path = DATA_PROCESSED_DIR / "vital_stats_deaths_2006_2015.parquet"
    pop_path = DATA_PROCESSED_DIR / "us_population_condensed_2006_2015.parquet"
    arcos_path = DATA_PROCESSED_DIR / "arcos_county_year_with_fips.parquet"

    print("Loading processed datasets...\n")

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


def build_panel():
    """
    Create merged county-year panel, apply filters, impute suppressed deaths,
    and save FL/WA analysis panels.
    """

    # Paths to the three main input files
    deaths_path = DATA_PROCESSED_DIR / "vital_stats_deaths_2006_2015.parquet"
    pop_path = DATA_PROCESSED_DIR / "us_population_condensed_2006_2015.parquet"
    arcos_path = DATA_PROCESSED_DIR / "arcos_county_year_with_fips.parquet"

    # ----------------- load inputs -----------------
    deaths = pd.read_parquet(deaths_path)
    pop = pd.read_parquet(pop_path)
    arcos = pd.read_parquet(arcos_path)

    # Ensure FIPS is always a 5-character string
    for df in (deaths, pop, arcos):
        df["fips"] = df["fips"].astype(str).str.zfill(5)

    # ----------------- merge to full panel -----------------
    # Start from population (complete county-year grid)
    panel = pop.merge(
        deaths[["fips", "year", "drug_deaths"]],
        on=["fips", "year"],
        how="left",
    )

    # Add ARCOS shipments (MME and total pills)
    panel = panel.merge(
        arcos[["fips", "year", "opioid_shipments_mme", "total_pills"]],
        on=["fips", "year"],
        how="left",
    )

    print("Merged panel created")
    print("   shape:", panel.shape)
    print("   Non-missing drug_deaths:", panel["drug_deaths"].notna().sum())
    print(
        "   Non-missing opioid_shipments_mme:",
        panel["opioid_shipments_mme"].notna().sum(),
    )

    # =====================================================
    # DATA-DRIVEN COUNTY FILTERS (population + suppression)
    # =====================================================

    print("\n" + "=" * 60)
    print("APPLYING POPULATION + SUPPRESSION FILTERS")
    print("=" * 60)

    # Flag suppressed values (CDC suppression -> NA in drug_deaths)
    panel["is_suppressed"] = panel["drug_deaths"].isna().astype(int)

    # Suppression rate per county (share of years suppressed)
    supp_rate = (
        panel.groupby("fips")["is_suppressed"]
        .mean()
        .reset_index()
        .rename(columns={"is_suppressed": "suppression_rate"})
    )

    # Median population per county (used for population cutoff)
    median_pop = (
        panel.groupby("fips")["population"]
        .median()
        .reset_index()
        .rename(columns={"population": "median_population"})
    )

    # Combine into a single county-level summary table
    county_summary = supp_rate.merge(median_pop, on="fips")

    # Cutoffs chosen from notebook elbow plots
    POP_CUTOFF = 50000  # keep counties with median population >= 50k
    SUPPR_CUTOFF = 0.40  # keep counties with suppression rate <= 40%

    # Counties that pass both filters
    kept = county_summary[
        (county_summary["median_population"] >= POP_CUTOFF)
        & (county_summary["suppression_rate"] <= SUPPR_CUTOFF)
    ]

    # Counties that fail at least one of the filters
    dropped = county_summary.loc[~county_summary["fips"].isin(kept["fips"])]

    print("   Total counties:   ", county_summary.shape[0])
    print("   Kept counties:    ", kept.shape[0])
    print("   Dropped counties: ", dropped.shape[0])
    print(
        "   Kept share:       ",
        100.0 * kept.shape[0] / county_summary.shape[0],
        "%\n",
    )

    # Restrict panel to only the kept counties
    panel = panel[panel["fips"].isin(kept["fips"])].copy()

    # =====================================================
    # IMPUTE REMAINING SUPPRESSED VALUES (<10)
    # =====================================================

    print("\n" + "=" * 60)
    print("IMPUTING SUPPRESSED DEATH VALUES (<10)")
    print("=" * 60)

    # Missing (suppressed) rows in the filtered panel
    missing_mask = panel["drug_deaths"].isna()
    n_missing = missing_mask.sum()
    n_total = len(panel)

    print(
        "   Missing suppressed values:",
        n_missing,
        f"({100.0 * n_missing / n_total:.2f}%)",
    )

    # Compute average death rate per 100k using observed data
    observed = panel[~missing_mask].copy()
    observed["death_rate"] = observed["drug_deaths"] / observed["population"] * 100000.0
    avg_rate = observed["death_rate"].mean()

    print("   Average observed death rate:", f"{avg_rate:.2f}", "per 100k")

    # Expected deaths for suppressed rows based on avg rate and population
    expected_raw = avg_rate * panel.loc[missing_mask, "population"] / 100000.0

    # Round and clip to integers in [0, 9], consistent with CDC suppression
    predicted_clipped = np.clip(np.round(expected_raw), 0, 9).astype(int)

    # Fill in imputed values and mark them
    panel["death_imputed"] = 0
    panel.loc[missing_mask, "drug_deaths"] = predicted_clipped
    panel.loc[missing_mask, "death_imputed"] = 1

    # Recompute death rate including imputed values
    panel["drug_death_rate_per_100k"] = (
        panel["drug_deaths"] / panel["population"] * 100000.0
    )

    print("   Imputed rows:", panel["death_imputed"].sum())
    print("=" * 60)

    # Save the full panel with filters + imputation applied
    output_path = DATA_PROCESSED_DIR / "opioid_panel_2006_2015.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, index=False)
    print("\nSaved full panel to", output_path)

    # =====================================================
    # FLORIDA PANEL (FL + controls)
    # =====================================================

    FL_POLICY_YEAR = 2010
    fl_states = ["FL", "GA", "AL", "SC", "NC", "TN", "MS"]

    # Subset to Florida and its control states
    fl_panel = panel[panel["state_abbrev"].isin(fl_states)].copy()
    fl_panel["is_pre"] = (fl_panel["year"] < FL_POLICY_YEAR).astype(int)

    # Drop rows with missing MME (year-level ARCOS gaps)
    before_rows = fl_panel.shape[0]
    fl_panel_clean = fl_panel[fl_panel["opioid_shipments_mme"].notna()].copy()
    after_rows = fl_panel_clean.shape[0]

    print("\n[FL] Florida panel")
    print("   Total rows:         ", before_rows)
    print("   Dropped missing MME:", before_rows - after_rows)
    print("   Final shape:        ", fl_panel_clean.shape)
    print("   Counties:           ", fl_panel_clean["fips"].nunique())

    fl_out = DATA_PROCESSED_DIR / "fl_panel_clean.parquet"
    fl_panel_clean.to_parquet(fl_out, index=False)
    print("   Saved:", fl_out)

    # =====================================================
    # WASHINGTON PANEL (WA + controls)
    # =====================================================

    WA_POLICY_YEAR = 2012
    wa_states = ["WA", "OR", "CO", "MN", "NV", "CA", "VA"]

    # Subset to Washington and its control states
    wa_panel = panel[panel["state_abbrev"].isin(wa_states)].copy()
    wa_panel["is_pre"] = (wa_panel["year"] < WA_POLICY_YEAR).astype(int)

    # Drop rows with missing MME (year-level ARCOS gaps)
    before_rows_wa = wa_panel.shape[0]
    wa_panel_clean = wa_panel[wa_panel["opioid_shipments_mme"].notna()].copy()
    after_rows_wa = wa_panel_clean.shape[0]

    print("\n[WA] Washington panel")
    print("   Total rows:         ", before_rows_wa)
    print("   Dropped missing MME:", before_rows_wa - after_rows_wa)
    print("   Final shape:        ", wa_panel_clean.shape)
    print("   Counties:           ", wa_panel_clean["fips"].nunique())

    wa_out = DATA_PROCESSED_DIR / "wa_panel_clean.parquet"
    wa_panel_clean.to_parquet(wa_out, index=False)
    print("   Saved:", wa_out)


if __name__ == "__main__":
    inspect_inputs()
    build_panel()
