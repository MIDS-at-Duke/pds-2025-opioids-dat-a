"""
Robustness Checks for DiD Analysis
Performs 4 sensitivity analyses to validate main findings
"""

import pandas as pd
import numpy as np
from pathlib import Path
import statsmodels.formula.api as smf

# Paths
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "outputs" / "tables"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# ROBUSTNESS CHECK 1: Alternative Control Groups
# ============================================================================
def robustness_1_alternative_controls():
    """Test FL with only southeastern controls (GA, AL, SC) vs all 6"""
    print("\n" + "="*70)
    print("ROBUSTNESS CHECK 1: Alternative Control Groups")
    print("="*70)
    
    # Load full FL panel
    fl_full = pd.read_parquet(DATA_DIR / "fl_panel_clean.parquet")
    
    # Subset 1: Only southeastern controls (GA, AL, SC)
    fl_subset = fl_full[fl_full['state_abbrev'].isin(['FL', 'GA', 'AL', 'SC'])].copy()
    
    # Create treatment indicators
    for df in [fl_full, fl_subset]:
        df['treated'] = (df['state_abbrev'] == 'FL').astype(int)
        df['post'] = (df['year'] >= 2010).astype(int)
        df['treated_post'] = df['treated'] * df['post']
        df['mme_per_100k'] = df['opioid_shipments_mme'] / df['population'] * 100_000
    
    # Run regressions
    formula = 'mme_per_100k ~ treated_post + C(fips) + C(year)'
    
    model_full = smf.ols(formula, data=fl_full.dropna(subset=['mme_per_100k'])).fit(
        cov_type='cluster', cov_kwds={'groups': fl_full.dropna(subset=['mme_per_100k'])['fips']}
    )
    
    model_subset = smf.ols(formula, data=fl_subset.dropna(subset=['mme_per_100k'])).fit(
        cov_type='cluster', cov_kwds={'groups': fl_subset.dropna(subset=['mme_per_100k'])['fips']}
    )
    
    coef_full = model_full.params['treated_post']
    pval_full = model_full.pvalues['treated_post']
    
    coef_subset = model_subset.params['treated_post']
    pval_subset = model_subset.pvalues['treated_post']
    
    print(f"\nAll 6 controls (GA,AL,SC,NC,TN,MS): {coef_full/1e6:.1f}M (p={pval_full:.3f})")
    print(f"Only 3 SE controls (GA,AL,SC):      {coef_subset/1e6:.1f}M (p={pval_subset:.3f})")
    print(f"Difference: {abs(coef_full - coef_subset)/1e6:.1f}M")
    
    return {
        'check': 'Alternative Control Groups',
        'all_controls_coef': f"{coef_full/1e6:.1f}M",
        'all_controls_p': f"{pval_full:.3f}",
        'subset_controls_coef': f"{coef_subset/1e6:.1f}M",
        'subset_controls_p': f"{pval_subset:.3f}",
        'conclusion': 'Consistent' if abs(coef_full - coef_subset) < 2e6 else 'Sensitive'
    }


# ============================================================================
# ROBUSTNESS CHECK 2: Population-Weighted Analysis
# ============================================================================
def robustness_2_population_weighted():
    """Re-run FL regressions with population weights"""
    print("\n" + "="*70)
    print("ROBUSTNESS CHECK 2: Population-Weighted Analysis")
    print("="*70)
    
    fl_full = pd.read_parquet(DATA_DIR / "fl_panel_clean.parquet")
    
    fl_full['treated'] = (fl_full['state_abbrev'] == 'FL').astype(int)
    fl_full['post'] = (fl_full['year'] >= 2010).astype(int)
    fl_full['treated_post'] = fl_full['treated'] * fl_full['post']
    
    # Unweighted (main analysis)
    formula_deaths = 'drug_death_rate_per_100k ~ treated_post + C(fips) + C(year)'
    model_unweighted = smf.ols(formula_deaths, data=fl_full.dropna(subset=['drug_death_rate_per_100k'])).fit(
        cov_type='cluster', cov_kwds={'groups': fl_full.dropna(subset=['drug_death_rate_per_100k'])['fips']}
    )
    
    # Weighted by population
    model_weighted = smf.wls(
        formula_deaths, 
        data=fl_full.dropna(subset=['drug_death_rate_per_100k']),
        weights=fl_full.dropna(subset=['drug_death_rate_per_100k'])['population']
    ).fit(cov_type='cluster', cov_kwds={'groups': fl_full.dropna(subset=['drug_death_rate_per_100k'])['fips']})
    
    coef_unw = model_unweighted.params['treated_post']
    pval_unw = model_unweighted.pvalues['treated_post']
    
    coef_w = model_weighted.params['treated_post']
    pval_w = model_weighted.pvalues['treated_post']
    
    print(f"\nUnweighted (main): {coef_unw:.2f} deaths/100k (p={pval_unw:.3f})")
    print(f"Pop-weighted:      {coef_w:.2f} deaths/100k (p={pval_w:.3f})")
    print(f"Difference: {abs(coef_unw - coef_w):.2f}")
    
    return {
        'check': 'Population Weighting',
        'unweighted_coef': f"{coef_unw:.2f}",
        'unweighted_p': f"{pval_unw:.3f}",
        'weighted_coef': f"{coef_w:.2f}",
        'weighted_p': f"{pval_w:.3f}",
        'conclusion': 'Robust' if pval_w < 0.05 else 'Weakened'
    }


# ============================================================================
# ROBUSTNESS CHECK 3: Placebo Test (Pre-Policy Year)
# ============================================================================
def robustness_3_placebo_test():
    """Test for effects in 2008 (fake policy year)"""
    print("\n" + "="*70)
    print("ROBUSTNESS CHECK 3: Placebo Test (2008 Fake Policy)")
    print("="*70)
    
    fl_full = pd.read_parquet(DATA_DIR / "fl_panel_clean.parquet")
    
    # Only use 2006-2009 data (pre-actual-policy)
    fl_pre = fl_full[fl_full['year'] <= 2009].copy()
    
    fl_pre['treated'] = (fl_pre['state_abbrev'] == 'FL').astype(int)
    fl_pre['post'] = (fl_pre['year'] >= 2008).astype(int)  # Fake policy in 2008
    fl_pre['treated_post'] = fl_pre['treated'] * fl_pre['post']
    fl_pre['mme_per_100k'] = fl_pre['opioid_shipments_mme'] / fl_pre['population'] * 100_000
    
    # Run placebo regressions
    formula_mme = 'mme_per_100k ~ treated_post + C(fips) + C(year)'
    formula_deaths = 'drug_death_rate_per_100k ~ treated_post + C(fips) + C(year)'
    
    model_mme = smf.ols(formula_mme, data=fl_pre.dropna(subset=['mme_per_100k'])).fit(
        cov_type='cluster', cov_kwds={'groups': fl_pre.dropna(subset=['mme_per_100k'])['fips']}
    )
    
    model_deaths = smf.ols(formula_deaths, data=fl_pre.dropna(subset=['drug_death_rate_per_100k'])).fit(
        cov_type='cluster', cov_kwds={'groups': fl_pre.dropna(subset=['drug_death_rate_per_100k'])['fips']}
    )
    
    pval_mme = model_mme.pvalues['treated_post']
    pval_deaths = model_deaths.pvalues['treated_post']
    
    print(f"\nPlacebo MME effect (2008): p={pval_mme:.3f} {'✓ No effect' if pval_mme > 0.10 else '✗ Spurious effect!'}")
    print(f"Placebo Death effect (2008): p={pval_deaths:.3f} {'✓ No effect' if pval_deaths > 0.10 else '✗ Spurious effect!'}")
    
    return {
        'check': 'Placebo Test (2008)',
        'mme_p': f"{pval_mme:.3f}",
        'deaths_p': f"{pval_deaths:.3f}",
        'conclusion': 'Passes' if (pval_mme > 0.10 and pval_deaths > 0.10) else 'FAILS'
    }


# ============================================================================
# ROBUSTNESS CHECK 4: Border County Exclusion
# ============================================================================
def robustness_4_border_exclusion():
    """Exclude FL counties bordering GA/AL to test spillover"""
    print("\n" + "="*70)
    print("ROBUSTNESS CHECK 4: Border County Exclusion")
    print("="*70)
    
    fl_full = pd.read_parquet(DATA_DIR / "fl_panel_clean.parquet")
    
    # FL border counties (manually identified - counties touching GA or AL)
    # This is a simplified list - in reality you'd use geographic data
    border_counties = [
        '12003',  # Baker County
        '12031',  # Duval County  
        '12033',  # Escambia County
        '12037',  # Franklin County
        '12039',  # Gadsden County
        '12045',  # Gulf County
        '12059',  # Holmes County
        '12063',  # Jackson County
        '12065',  # Jefferson County
        '12073',  # Leon County
        '12077',  # Liberty County
        '12079',  # Madison County
        '12091',  # Okaloosa County
        '12113',  # Santa Rosa County
        '12121',  # Suwannee County
        '12131',  # Walton County
        '12133',  # Washington County
    ]
    
    # Exclude border counties
    fl_no_border = fl_full[~fl_full['fips'].isin(border_counties)].copy()
    
    fl_no_border['treated'] = (fl_no_border['state_abbrev'] == 'FL').astype(int)
    fl_no_border['post'] = (fl_no_border['year'] >= 2010).astype(int)
    fl_no_border['treated_post'] = fl_no_border['treated'] * fl_no_border['post']
    fl_no_border['mme_per_100k'] = fl_no_border['opioid_shipments_mme'] / fl_no_border['population'] * 100_000
    
    # Run regressions
    formula_mme = 'mme_per_100k ~ treated_post + C(fips) + C(year)'
    formula_deaths = 'drug_death_rate_per_100k ~ treated_post + C(fips) + C(year)'
    
    model_mme = smf.ols(formula_mme, data=fl_no_border.dropna(subset=['mme_per_100k'])).fit(
        cov_type='cluster', cov_kwds={'groups': fl_no_border.dropna(subset=['mme_per_100k'])['fips']}
    )
    
    model_deaths = smf.ols(formula_deaths, data=fl_no_border.dropna(subset=['drug_death_rate_per_100k'])).fit(
        cov_type='cluster', cov_kwds={'groups': fl_no_border.dropna(subset=['drug_death_rate_per_100k'])['fips']}
    )
    
    coef_mme = model_mme.params['treated_post']
    pval_mme = model_mme.pvalues['treated_post']
    
    coef_deaths = model_deaths.params['treated_post']
    pval_deaths = model_deaths.pvalues['treated_post']
    
    print(f"\nExcluding {len(border_counties)} border counties:")
    print(f"MME effect: {coef_mme/1e6:.1f}M (p={pval_mme:.3f})")
    print(f"Death effect: {coef_deaths:.2f} (p={pval_deaths:.3f})")
    
    return {
        'check': 'Border Exclusion',
        'mme_coef': f"{coef_mme/1e6:.1f}M",
        'mme_p': f"{pval_mme:.3f}",
        'deaths_coef': f"{coef_deaths:.2f}",
        'deaths_p': f"{pval_deaths:.3f}",
        'conclusion': 'Robust' if (pval_mme < 0.05 and pval_deaths < 0.05) else 'Weakened'
    }


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("\n" + "="*70)
    print("RUNNING ALL ROBUSTNESS CHECKS")
    print("="*70)
    
    results = []
    
    # Run all checks
    results.append(robustness_1_alternative_controls())
    results.append(robustness_2_population_weighted())
    results.append(robustness_3_placebo_test())
    results.append(robustness_4_border_exclusion())
    
    # Save results
    results_df = pd.DataFrame(results)
    output_path = OUTPUT_DIR / "robustness_checks.csv"
    results_df.to_csv(output_path, index=False)
    
    print("\n" + "="*70)
    print("SUMMARY OF ROBUSTNESS CHECKS")
    print("="*70)
    print(results_df.to_string(index=False))
    print(f"\n✅ Results saved to: {output_path}")


if __name__ == "__main__":
    main()
