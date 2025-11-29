import os

import pandas as pd
import statsmodels.formula.api as smf

YEAR_COL = "year"
STATE_COL = "state_abbrev"
FIPS_COL = "fips"
POP_COL = "population"
DEATH_RATE_COL = "drug_death_rate_per_100k"
SHIP_MME_COL = "opioid_shipments_mme"


def run_case(policy_state, policy_year, path):
    df = pd.read_parquet(path)

    df["treated"] = (df[STATE_COL] == policy_state).astype(int)
    df["post"] = (df[YEAR_COL] >= policy_year).astype(int)
    df["mme_per_100k"] = df[SHIP_MME_COL] / df[POP_COL] * 100_000

    results = []
    for outcome in [DEATH_RATE_COL, "mme_per_100k"]:
        formula = f"{outcome} ~ treated * post + C({YEAR_COL}) + C({FIPS_COL})"
        d = df.dropna(subset=[outcome])
        model = smf.ols(formula=formula, data=d)
        fit = model.fit(cov_type="cluster", cov_kwds={"groups": d[FIPS_COL]})

        coef = "treated:post"
        results.append(
            {
                "policy_state": policy_state,
                "outcome": outcome,
                "beta_did": fit.params.get(coef),
                "se": fit.bse.get(coef),
                "p_value": fit.pvalues.get(coef),
                "n_obs": int(fit.nobs),
                "r_squared": fit.rsquared,
            }
        )

    return pd.DataFrame(results)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root, "data", "processed")

    fl_path = os.path.join(data_dir, "fl_panel_clean.parquet")
    wa_path = os.path.join(data_dir, "wa_panel_clean.parquet")

    df_fl = run_case("FL", 2010, fl_path)
    df_wa = run_case("WA", 2012, wa_path)

    out = pd.concat([df_fl, df_wa], ignore_index=True)

    out_dir = os.path.join(root, "outputs", "tables")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "did_results_FL_WA.csv")
    out.to_csv(out_path, index=False)

    print(f"Saved DiD results to: {out_path}")
    print(out)


if __name__ == "__main__":
    main()
