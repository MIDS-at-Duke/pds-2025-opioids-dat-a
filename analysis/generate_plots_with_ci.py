"""
Updated plotting script with confidence intervals/standard error bands.
Addresses professor's requirement for confidence intervals in graphs.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats

POLICY_STATE_FL = "FL"
POLICY_YEAR_FL = 2010
POLICY_STATE_WA = "WA"
POLICY_YEAR_WA = 2012


def compute_state_year_means_with_se(df, outcome, state_col="state_abbrev", year_col="year"):
    """
    Compute state-year means with standard errors.
    Returns DataFrame with columns: state_abbrev, year, mean, se, ci_lower, ci_upper
    """
    grouped = df.groupby([state_col, year_col])[outcome].agg(
        mean='mean',
        std='std',
        count='count'
    ).reset_index()
    
    # Standard error of the mean
    grouped['se'] = grouped['std'] / np.sqrt(grouped['count'])
    
    # 95% confidence interval (1.96 * SE for large samples)
    grouped['ci_lower'] = grouped['mean'] - 1.96 * grouped['se']
    grouped['ci_upper'] = grouped['mean'] + 1.96 * grouped['se']
    
    return grouped


def prepost_and_did_plot_with_ci(
    df: pd.DataFrame,
    outcome: str,
    y_label: str,
    title_prefix: str,
    out_path: str,
    policy_state: str,
    policy_year: int,
):
    """
    Make a two-panel figure with confidence intervals:
      left: Pre-Post for policy state
      right: DiD-style policy state vs Controls
    """
    
    # Compute state-year means with standard errors
    state_year = compute_state_year_means_with_se(df, outcome)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # --- Left panel: Pre-Post for policy state only ---
    ax0 = axes[0]
    policy_data = state_year[state_year['state_abbrev'] == policy_state].copy()
    
    # Split pre and post
    pre_data = policy_data[policy_data['year'] < policy_year]
    post_data = policy_data[policy_data['year'] >= policy_year]
    
    # Plot pre-period
    if len(pre_data) > 0:
        ax0.plot(pre_data['year'], pre_data['mean'], 'o-', 
                label='Pre-policy', linewidth=2, markersize=6, color='blue')
        ax0.fill_between(pre_data['year'], 
                        pre_data['ci_lower'], 
                        pre_data['ci_upper'],
                        alpha=0.2, color='blue')
    
    # Plot post-period
    if len(post_data) > 0:
        ax0.plot(post_data['year'], post_data['mean'], 'o-',
                label='Post-policy', linewidth=2, markersize=6, color='red')
        ax0.fill_between(post_data['year'],
                        post_data['ci_lower'],
                        post_data['ci_upper'],
                        alpha=0.2, color='red')
    
    ax0.axvline(policy_year - 0.5, linestyle='--', color='black', linewidth=1.5, alpha=0.7)
    ax0.set_xlabel('Year', fontsize=12)
    ax0.set_ylabel(y_label, fontsize=12)
    ax0.set_title(f'{title_prefix}\nPre-Post ({policy_state})', fontsize=13, fontweight='bold')
    ax0.legend(fontsize=10)
    ax0.grid(True, alpha=0.3)
    
    # --- Right panel: DiD (policy state vs controls) ---
    ax1 = axes[1]
    
    # Policy state
    policy_pre = policy_data[policy_data['year'] < policy_year]
    policy_post = policy_data[policy_data['year'] >= policy_year]
    
    if len(policy_pre) > 0:
        ax1.plot(policy_pre['year'], policy_pre['mean'], 'o-',
                label=f'{policy_state} (pre)', linewidth=2, markersize=6, color='blue')
        ax1.fill_between(policy_pre['year'],
                        policy_pre['ci_lower'],
                        policy_pre['ci_upper'],
                        alpha=0.2, color='blue')
    
    if len(policy_post) > 0:
        ax1.plot(policy_post['year'], policy_post['mean'], 'o-',
                label=f'{policy_state} (post)', linewidth=2, markersize=6, color='red')
        ax1.fill_between(policy_post['year'],
                        policy_post['ci_lower'],
                        policy_post['ci_upper'],
                        alpha=0.2, color='red')
    
    # Control states (aggregate)
    control_data = state_year[state_year['state_abbrev'] != policy_state].copy()
    
    # Aggregate controls by year (weighted by count)
    control_agg = control_data.groupby('year').apply(
        lambda g: pd.Series({
            'mean': np.average(g['mean'], weights=g['count']),
            'se': np.sqrt(np.sum(g['se']**2 * g['count']**2)) / np.sum(g['count']),
            'count': g['count'].sum()
        })
    ).reset_index()
    
    control_agg['ci_lower'] = control_agg['mean'] - 1.96 * control_agg['se']
    control_agg['ci_upper'] = control_agg['mean'] + 1.96 * control_agg['se']
    
    ctrl_pre = control_agg[control_agg['year'] < policy_year]
    ctrl_post = control_agg[control_agg['year'] >= policy_year]
    
    if len(ctrl_pre) > 0:
        ax1.plot(ctrl_pre['year'], ctrl_pre['mean'], 's--',
                label='Controls (pre)', linewidth=2, markersize=6, color='green', alpha=0.7)
        ax1.fill_between(ctrl_pre['year'],
                        ctrl_pre['ci_lower'],
                        ctrl_pre['ci_upper'],
                        alpha=0.15, color='green')
    
    if len(ctrl_post) > 0:
        ax1.plot(ctrl_post['year'], ctrl_post['mean'], 's--',
                label='Controls (post)', linewidth=2, markersize=6, color='orange', alpha=0.7)
        ax1.fill_between(ctrl_post['year'],
                        ctrl_post['ci_lower'],
                        ctrl_post['ci_upper'],
                        alpha=0.15, color='orange')
    
    ax1.axvline(policy_year - 0.5, linestyle='--', color='black', linewidth=1.5, alpha=0.7)
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel(y_label, fontsize=12)
    ax1.set_title(f'{title_prefix}\nDiD: {policy_state} vs Controls', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Saved figure with confidence intervals to: {out_path}")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root, "data", "processed")
    fig_dir = os.path.join(root, "outputs", "figures")
    os.makedirs(fig_dir, exist_ok=True)
    
    # ========== FLORIDA ==========
    print("\n" + "="*60)
    print("GENERATING FLORIDA PLOTS WITH CONFIDENCE INTERVALS")
    print("="*60)
    
    fl_path = os.path.join(data_dir, "fl_panel_clean.parquet")
    df_fl = pd.read_parquet(fl_path).copy()
    df_fl["mme_per_100k"] = df_fl["opioid_shipments_mme"] / df_fl["population"] * 100_000
    
    # Check MME values
    print(f"\nFL MME Statistics:")
    print(f"  Mean: {df_fl['mme_per_100k'].mean():,.2f}")
    print(f"  Median: {df_fl['mme_per_100k'].median():,.2f}")
    print(f"  Max: {df_fl['mme_per_100k'].max():,.2f}")
    print(f"  Min: {df_fl['mme_per_100k'].min():,.2f}")
    
    # Mortality plot
    out_mort_fl = os.path.join(fig_dir, "fl_prepost_did_mortality.png")
    prepost_and_did_plot_with_ci(
        df=df_fl,
        outcome="drug_death_rate_per_100k",
        y_label="Drug Deaths per 100,000",
        title_prefix="Effect of FL 2010 Policy on Mortality",
        out_path=out_mort_fl,
        policy_state=POLICY_STATE_FL,
        policy_year=POLICY_YEAR_FL,
    )
    
    # Shipments plot
    out_ship_fl = os.path.join(fig_dir, "fl_prepost_did_shipments.png")
    prepost_and_did_plot_with_ci(
        df=df_fl,
        outcome="mme_per_100k",
        y_label="Opioid Shipments (MME per 100,000)",
        title_prefix="Effect of FL 2010 Policy on Opioid Shipments",
        out_path=out_ship_fl,
        policy_state=POLICY_STATE_FL,
        policy_year=POLICY_YEAR_FL,
    )
    
    # ========== WASHINGTON ==========
    print("\n" + "="*60)
    print("GENERATING WASHINGTON PLOTS WITH CONFIDENCE INTERVALS")
    print("="*60)
    
    wa_path = os.path.join(data_dir, "wa_panel_clean.parquet")
    df_wa = pd.read_parquet(wa_path).copy()
    df_wa["mme_per_100k"] = df_wa["opioid_shipments_mme"] / df_wa["population"] * 100_000
    
    # Check MME values
    print(f"\nWA MME Statistics:")
    print(f"  Mean: {df_wa['mme_per_100k'].mean():,.2f}")
    print(f"  Median: {df_wa['mme_per_100k'].median():,.2f}")
    print(f"  Max: {df_wa['mme_per_100k'].max():,.2f}")
    print(f"  Min: {df_wa['mme_per_100k'].min():,.2f}")
    
    # Mortality plot
    out_mort_wa = os.path.join(fig_dir, "wa_prepost_did_mortality.png")
    prepost_and_did_plot_with_ci(
        df=df_wa,
        outcome="drug_death_rate_per_100k",
        y_label="Drug Deaths per 100,000",
        title_prefix="Effect of WA 2012 Policy on Mortality",
        out_path=out_mort_wa,
        policy_state=POLICY_STATE_WA,
        policy_year=POLICY_YEAR_WA,
    )
    
    # Shipments plot
    out_ship_wa = os.path.join(fig_dir, "wa_prepost_did_shipments.png")
    prepost_and_did_plot_with_ci(
        df=df_wa,
        outcome="mme_per_100k",
        y_label="Opioid Shipments (MME per 100,000)",
        title_prefix="Effect of WA 2012 Policy on Opioid Shipments",
        out_path=out_ship_wa,
        policy_state=POLICY_STATE_WA,
        policy_year=POLICY_YEAR_WA,
    )
    
    print("\n" + "="*60)
    print("✓ ALL PLOTS GENERATED SUCCESSFULLY WITH CONFIDENCE INTERVALS")
    print("="*60)


if __name__ == "__main__":
    main()
