"""
DiD Regression Analysis - Models 1 & 2

This script runs the Difference-in-Differences regressions specified in the
Project Summary PDF:

Model 1 (Levels):
Y_ct = alpha + psi_c + beta1*post_t + beta2*post_t*policy_state + epsilon_ct

Model 2 (Trends):
Y_ct = alpha + ... + beta7*post_t*year_t*policy_state + epsilon_ct

Outputs results for:
- Florida 2010 (Shipments & Deaths)
- Washington 2012 (Shipments & Deaths)
"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from pathlib import Path

# Configuration
DATA_DIR = Path("data/processed")
OUTPUT_DIR = Path("outputs/tables")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def run_regressions(state_code, panel_file, policy_year):
    print(f"\n{'='*60}")
    print(f"RUNNING REGRESSIONS FOR {state_code} (Policy Year: {policy_year})")
    print(f"{'='*60}")
    
    # Load data
    df = pd.read_parquet(DATA_DIR / panel_file)
    
    # Create necessary variables
    df['post'] = (df['year'] >= policy_year).astype(int)
    df['treated'] = (df['state_abbrev'] == state_code).astype(int)
    
    # Centered year for Model 2 (t=0 at policy year)
    df['year_centered'] = df['year'] - policy_year
    
    # Calculate MME per 100k if not present
    if 'mme_per_100k' not in df.columns:
        df['mme_per_100k'] = df['opioid_shipments_mme'] / df['population'] * 100_000
    
    # Outcomes to analyze
    outcomes = {
        'Opioid Shipments (MME per 100k)': 'mme_per_100k',
        'Drug Deaths (per 100k)': 'drug_death_rate_per_100k'
    }
    
    results_summary = []
    
    for label, outcome in outcomes.items():
        print(f"\nOutcome: {label}")
        
        # Prepare data for this outcome - DROP MISSING VALUES explicitly
        # This fixes the "weights and list don't have the same length" error with clustering
        reg_df = df[[outcome, 'post', 'treated', 'fips', 'year', 'year_centered']].dropna()
        
        # --- Model 1: Levels (Standard DiD) ---
        formula_m1 = f"{outcome} ~ post + post:treated + C(fips) + C(year)"
        
        try:
            model1 = smf.ols(formula_m1, data=reg_df).fit(cov_type='cluster', cov_kwds={'groups': reg_df['fips']})
            beta_did_m1 = model1.params['post:treated']
            se_did_m1 = model1.bse['post:treated']
            p_did_m1 = model1.pvalues['post:treated']
            
            print(f"  Model 1 (Levels) DiD Coeff: {beta_did_m1:.2f} (p={p_did_m1:.3f})")
        except Exception as e:
            print(f"  Model 1 Failed: {e}")
            beta_did_m1, se_did_m1, p_did_m1 = np.nan, np.nan, np.nan

        # --- Model 2: Trends ---
        formula_m2 = (
            f"{outcome} ~ year_centered + year_centered:treated + "
            f"post + post:treated + "
            f"post:year_centered + post:year_centered:treated + "
            f"C(fips)"
        )
        
        try:
            model2 = smf.ols(formula_m2, data=reg_df).fit(cov_type='cluster', cov_kwds={'groups': reg_df['fips']})
            
            # Try to find the correct interaction term name
            possible_names = [
                'year_centered:treated:post',
                'post:year_centered:treated', 
                'treated:post:year_centered',
                'year_centered:post:treated'
            ]
            
            term_name = next((name for name in possible_names if name in model2.params), None)
            
            if term_name:
                beta_trend_did = model2.params[term_name]
                se_trend_did = model2.bse[term_name]
                p_trend_did = model2.pvalues[term_name]
            else:
                raise KeyError(f"Interaction term not found. Available: {model2.params.index.tolist()}")
            
            # Also get level shift (beta5): post:treated
            beta_level_did = model2.params.get('post:treated', np.nan)
            
            print(f"  Model 2 (Trends) Slope Change: {beta_trend_did:.2f} (p={p_trend_did:.3f})")
            
        except Exception as e:
            print(f"  Model 2 Failed: {e}") 
            beta_trend_did, se_trend_did, p_trend_did = np.nan, np.nan, np.nan
            beta_level_did = np.nan 

        results_summary.append({
            'State': state_code,
            'Outcome': label,
            'M1_DiD_Level': beta_did_m1,
            'M1_SE': se_did_m1,
            'M1_Pval': p_did_m1,
            'M2_DiD_Slope': beta_trend_did,
            'M2_SE': se_trend_did,
            'M2_Pval': p_trend_did,
            'M2_Level_Shift': beta_level_did
        })
        
    return pd.DataFrame(results_summary)

def main():
    # Run Florida Analysis
    res_fl = run_regressions("FL", "fl_panel_clean.parquet", 2010)
    
    # Run Washington Analysis
    res_wa = run_regressions("WA", "wa_panel_clean.parquet", 2012)
    
    # Combine and save
    final_res = pd.concat([res_fl, res_wa], ignore_index=True)
    
    # Formatting for display
    print("\n" + "="*80)
    print("FINAL REGRESSION RESULTS SUMMARY")
    print("="*80)
    
    display_cols = ['State', 'Outcome', 'M1_DiD_Level', 'M1_Pval', 'M2_DiD_Slope', 'M2_Pval']
    print(final_res[display_cols].to_string(index=False, float_format=lambda x: "{:.3f}".format(x)))
    
    # Save to CSV
    final_res.to_csv(OUTPUT_DIR / "did_regression_results.csv", index=False)
    print(f"\nResults saved to: {OUTPUT_DIR / 'did_regression_results.csv'}")

if __name__ == "__main__":
    main()
