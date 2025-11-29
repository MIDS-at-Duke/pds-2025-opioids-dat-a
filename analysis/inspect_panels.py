## Quick inspection script for FL & WA panel parquet files.

from __future__ import annotations

import os
import textwrap

import pandas as pd


def load_panel(path: str) -> pd.DataFrame:
    print(f"\n=== Loading panel: {path} ===")
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    df = pd.read_parquet(path)
    print(f"Rows: {len(df):,}, Columns: {len(df.columns)}")
    return df


def summarize_df(name: str, df: pd.DataFrame) -> None:
    print(f"\n=== Summary for {name} ===")

    print("\n[1] Columns & dtypes:")
    print(df.dtypes)

    print("\n[2] Head (first 5 rows):")
    print(df.head())

    year_like_cols = [c for c in df.columns if "year" in c.lower() or "date" in c.lower()]
    if year_like_cols:
        print("\n[3] Year-like columns and ranges:")
        for col in year_like_cols:
            ymin = df[col].min()
            ymax = df[col].max()
            print(f"  - {col}: {ymin} — {ymax}")
    else:
        print("\n[3] No obvious year column found (no 'year' in column names).")

    geo_cols = [c for c in df.columns if any(
        k in c.lower()
        for k in ["state", "county", "fips"]
    )]
    if geo_cols:
        print("\n[4] Potential geographic columns (unique counts):")
        for col in geo_cols:
            nunique = df[col].nunique(dropna=True)
            print(f"  - {col}: {nunique} unique values")
    else:
        print("\n[4] No obvious geographic columns (state/county/fips) found.")

    death_like = [c for c in df.columns if any(
        k in c.lower() for k in ["death", "overdose", "mortality"]
    )]
    pop_like = [c for c in df.columns if any(
        k in c.lower() for k in ["pop", "population"]
    )]

    print("\n[5] Candidate death-related columns:")
    print("    " + (", ".join(death_like) if death_like else "(none detected)"))

    print("\n[6] Candidate population-related columns:")
    print("    " + (", ".join(pop_like) if pop_like else "(none detected)"))

    if death_like:
        print("\n[7] .describe() for death-like columns:")
        print(df[death_like].describe())


def main() -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data", "processed")

    fl_path = os.path.join(project_root, "data", "processed", "fl_panel_clean.parquet")
    wa_path = os.path.join(project_root, "data", "processed", "wa_panel_clean.parquet")

    print(
        textwrap.dedent(
            """
            --------------------------------------------------------
            Inspecting FL & WA panel parquet files.

            This will print:
              - columns & dtypes
              - head()
              - year range
              - possible state/county/fips columns
              - possible death & population columns
            --------------------------------------------------------
            """
        )
    )

    fl_df = load_panel(fl_path)
    summarize_df("Florida panel", fl_df)

    wa_df = load_panel(wa_path)
    summarize_df("Washington panel", wa_df)


if __name__ == "__main__":
    main()
