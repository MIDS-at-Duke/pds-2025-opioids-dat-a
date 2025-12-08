import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.nonparametric.smoothers_lowess import lowess

POLICY_STATE = "FL"
POLICY_YEAR = 2010

def calculate_ci(data, confidence=0.95):
    """Calculate confidence interval for mean."""
    n = len(data)
    if n < 2:
        return 0, 0
    mean = np.mean(data)
    se = stats.sem(data)
    ci = se * stats.t.ppf((1 + confidence) / 2., n-1)
    return mean - ci, mean + ci

def prepost_and_did_plot(
    df: pd.DataFrame,
    outcome: str,
    y_label: str,
    title_prefix: str,
    out_path: str,
):
    """
    Make a single-panel DiD plot with:
    - Consistent colors (red for treatment, blue for controls)
    - Confidence intervals
    - LOWESS smoothing
    - Proper spacing to prevent title overlap
    """
    
    # Aggregate to state-year means with confidence intervals
    state_year = df.groupby(["state_abbrev", "year"])[outcome].agg(['mean', 'std', 'count']).reset_index()
    
    # Calculate confidence intervals
    state_year['se'] = state_year['std'] / np.sqrt(state_year['count'])
    state_year['ci_lower'] = state_year['mean'] - 1.96 * state_year['se']
    state_year['ci_upper'] = state_year['mean'] + 1.96 * state_year['se']
    
    # Florida data
    fl = state_year[state_year["state_abbrev"] == POLICY_STATE].copy()
    
    # Controls: aggregate all non-FL states
    ctrl = state_year[state_year["state_abbrev"] != POLICY_STATE].copy()
    ctrl_agg = ctrl.groupby('year').agg({
        'mean': 'mean',
        'ci_lower': 'mean',
        'ci_upper': 'mean'
    }).reset_index()
    
    # Create figure with extra top margin to prevent title overlap
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    fig.subplots_adjust(top=0.88)  # Add space at top for title
    
    # Plot Florida with confidence interval
    ax.plot(fl['year'], fl['mean'], 
            color='#d62728', linewidth=2.5, label='Florida', zorder=3)
    ax.fill_between(fl['year'], fl['ci_lower'], fl['ci_upper'],
                     color='#d62728', alpha=0.2, zorder=2)
    
    # Plot Controls with confidence interval
    ax.plot(ctrl_agg['year'], ctrl_agg['mean'],
            color='#1f77b4', linewidth=2.5, linestyle='--', 
            label='Control States (avg)', zorder=3)
    ax.fill_between(ctrl_agg['year'], ctrl_agg['ci_lower'], ctrl_agg['ci_upper'],
                     color='#1f77b4', alpha=0.2, zorder=2)
    
    # Add LOWESS smoothing
    if len(fl) > 3:
        fl_lowess = lowess(fl['mean'].values, fl['year'].values, frac=0.3)
        ax.plot(fl_lowess[:, 0], fl_lowess[:, 1], 
                color='#d62728', linewidth=1, linestyle=':', alpha=0.7, zorder=1)
    
    if len(ctrl_agg) > 3:
        ctrl_lowess = lowess(ctrl_agg['mean'].values, ctrl_agg['year'].values, frac=0.3)
        ax.plot(ctrl_lowess[:, 0], ctrl_lowess[:, 1],
                color='#1f77b4', linewidth=1, linestyle=':', alpha=0.7, zorder=1)
    
    # Policy line
    ax.axvline(POLICY_YEAR, color='black', linestyle='--', linewidth=1.5, 
               alpha=0.7, label=f'{POLICY_YEAR} Policy')
    
    # Labels and formatting
    ax.set_xlabel("Year", fontsize=11, fontweight='bold')
    ax.set_ylabel(y_label, fontsize=11, fontweight='bold')
    ax.set_title(title_prefix, fontsize=12, fontweight='bold', pad=20)  # pad=20 for spacing
    ax.legend(loc='best', frameon=True, shadow=True, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle=':')
    
    # Tight layout with extra padding
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved figure to: {out_path}")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(root, "data", "processed", "fl_panel_clean.parquet")
    fig_dir = os.path.join(root, "outputs", "figures")
    os.makedirs(fig_dir, exist_ok=True)

    df = pd.read_parquet(data_path).copy()
    df["mme_per_100k"] = df["opioid_shipments_mme"] / df["population"] * 100_000

    # Shipments figure
    out_ship = os.path.join(fig_dir, "fl_prepost_did_shipments.png")
    prepost_and_did_plot(
        df=df,
        outcome="mme_per_100k",
        y_label="MME per 100,000 Population",
        title_prefix="Florida Opioid Shipments: Treatment vs. Controls (2006-2015)",
        out_path=out_ship,
    )

    # Mortality figure
    out_mort = os.path.join(fig_dir, "fl_prepost_did_mortality.png")
    prepost_and_did_plot(
        df=df,
        outcome="drug_death_rate_per_100k",
        y_label="Drug Deaths per 100,000 Population",
        title_prefix="Florida Drug Mortality: Treatment vs. Controls (2006-2015)",
        out_path=out_mort,
    )


if __name__ == "__main__":
    main()
