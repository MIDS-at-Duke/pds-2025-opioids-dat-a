
## Pre-post analysis of overdose deaths for Florida and Washington.

"""
For each policy state (FL / WA), compute:
- mean annual drug_deaths
- mean annual drug_death_rate_per_100k
"""

import os
from dataclasses import dataclass

import pandas as pd


# Column names based on inspect_panels output
YEAR_COL = "year"
DEATHS_COL = "drug_deaths"
RATE_COL = "drug_death_rate_per_100k"
POP_COL = "population"
STATE_COL = "state_abbrev"
PRE_FLAG_COL = "is_pre"  # 1 = pre, 0 = post


@dataclass
class PanelConfig:
    """Configuration for one panel file (Florida or Washington case)."""

    name: str           # Human-readable name, e.g. "Florida case"
    panel_path: str     # Path to parquet file
    policy_state: str   # Policy state abbreviation: "FL" or "WA"


def load_panel(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Panel file not found: {path}")

    df = pd.read_parquet(path)
    print(f"\n=== Loaded panel: {path} ===")
    print(f"Rows: {len(df):,}, Columns: {len(df.columns)}")
    return df


def aggregate_to_state_year(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby([STATE_COL, YEAR_COL], as_index=False)
        .agg(
            total_deaths=(DEATHS_COL, "sum"),
            total_pop=(POP_COL, "sum"),
        )
    )

    grouped["death_rate_per_100k"] = (
        grouped["total_deaths"] / grouped["total_pop"] * 100_000
    )
    return grouped


def compute_pre_post_means(
    df_state_year: pd.DataFrame,
    df_original: pd.DataFrame,
    policy_state: str,
) -> pd.DataFrame:


    # Get a unique (state, year, is_pre) mapping from the original data
    state_year_pre = (
        df_original[[STATE_COL, YEAR_COL, PRE_FLAG_COL]]
        .drop_duplicates(subset=[STATE_COL, YEAR_COL])
    )

    # Merge is_pre back into the state-year table
    df = df_state_year.merge(
        state_year_pre,
        on=[STATE_COL, YEAR_COL],
        how="left",
        validate="one_to_one",
    )

    # Mark whether a row belongs to the policy state
    df["is_policy_state"] = (df[STATE_COL] == policy_state).astype(int)

    # Turn is_pre into a readable label
    df["period"] = df[PRE_FLAG_COL].map({1: "pre", 0: "post"})

    # Group by (policy vs control) and (pre vs post)
    summary = (
        df.groupby(["is_policy_state", "period"], as_index=False)
        .agg(
            mean_total_deaths=("total_deaths", "mean"),
            mean_death_rate_per_100k=("death_rate_per_100k", "mean"),
            n_state_years=("total_deaths", "size"),
        )
    )

    # Use readable group labels
    summary["group"] = summary["is_policy_state"].map(
        {1: "policy_state", 0: "control_states"}
    )

    # Add which policy state this summary refers to
    summary["policy_state_abbrev"] = policy_state

    # Reorder columns for clarity
    summary = summary[
        [
            "policy_state_abbrev",
            "group",
            "period",
            "n_state_years",
            "mean_total_deaths",
            "mean_death_rate_per_100k",
        ]
    ]

    return summary


def run_for_case(cfg: PanelConfig) -> pd.DataFrame:
    """Run the full pre-post pipeline for one policy state case."""
    print(f"\n================ {cfg.name} ================")
    panel = load_panel(cfg.panel_path)

    # Aggregate to state-year level
    df_state_year = aggregate_to_state_year(panel)

    # Compute pre/post means for policy vs control states
    summary = compute_pre_post_means(
        df_state_year=df_state_year,
        df_original=panel,
        policy_state=cfg.policy_state,
    )

    print("\nPre-post summary (preview):")
    print(summary)

    return summary


def main() -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data", "processed")

    fl_cfg = PanelConfig(
        name="Florida case",
        panel_path=os.path.join(data_dir, "fl_panel_clean.parquet"),
        policy_state="FL",
    )

    wa_cfg = PanelConfig(
        name="Washington case",
        panel_path=os.path.join(data_dir, "wa_panel_clean.parquet"),
        policy_state="WA",
    )

    all_results = []

    for cfg in [fl_cfg, wa_cfg]:
        res = run_for_case(cfg)
        all_results.append(res)

    full_summary = pd.concat(all_results, ignore_index=True)

    # Save combined summary table
    output_dir = os.path.join(project_root, "outputs", "tables")
    os.makedirs(output_dir, exist_ok=True)

    out_path = os.path.join(output_dir, "pre_post_mean_deaths_FL_WA.csv")
    full_summary.to_csv(out_path, index=False)

    print(f"\n✅ Saved pre-post summary to: {out_path}")
    print("\nFinal combined summary:")
    print(full_summary)


if __name__ == "__main__":
    main()
