import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

POLICY_STATE = "FL"
POLICY_YEAR = 2010


def fit_segment(years: np.ndarray, values: np.ndarray):
    """Fit a straight line y = a + b x on given years and values."""
    if len(years) < 2:
        return years, values  # not enough points, just return original
    coef = np.polyfit(years, values, 1)  # [slope, intercept]
    years_sorted = np.sort(years)
    fitted = np.polyval(coef, years_sorted)
    return years_sorted, fitted


def prepost_and_did_plot(
    df: pd.DataFrame,
    outcome: str,
    y_label: str,
    title_prefix: str,
    out_path: str,
):
    """
    Make a two-panel figure:
      left: Pre-Post for Florida
      right: DiD-style Florida vs Controls
    """

    # Aggregate to state-year means
    state_year = (
        df.groupby(["state_abbrev", "year"], as_index=False)[outcome]
        .mean()
    )

    # --- Left panel: Pre-Post for Florida only ---
    fl = state_year[state_year["state_abbrev"] == POLICY_STATE].copy()
    fl_pre = fl[fl["year"] < POLICY_YEAR]
    fl_post = fl[fl["year"] >= POLICY_YEAR]

    pre_years, pre_fit = fit_segment(fl_pre["year"].to_numpy(),
                                     fl_pre[outcome].to_numpy())
    post_years, post_fit = fit_segment(fl_post["year"].to_numpy(),
                                       fl_post[outcome].to_numpy())

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)

    ax0 = axes[0]
    if len(pre_years) > 0:
        ax0.plot(pre_years, pre_fit, label="Pre-policy", linewidth=2)
    if len(post_years) > 0:
        ax0.plot(post_years, post_fit, label="Post-policy", linewidth=2)
    ax0.axvline(POLICY_YEAR, linestyle="--", linewidth=1)
    ax0.set_xlabel("Year")
    ax0.set_ylabel(y_label)
    ax0.set_title(f"{title_prefix}: Pre-Post (Florida)")
    ax0.legend()

    # --- Right panel: Florida vs Controls (DiD-style) ---
    ax1 = axes[1]
    # Florida segments
    if len(pre_years) > 0:
        ax1.plot(pre_years, pre_fit, label="Florida pre", linewidth=2)
    if len(post_years) > 0:
        ax1.plot(post_years, post_fit, label="Florida post", linewidth=2)

    # Controls: all non-FL states in this panel
    ctrl = state_year[state_year["state_abbrev"] != POLICY_STATE].copy()
    ctrl_pre = ctrl[ctrl["year"] < POLICY_YEAR]
    ctrl_post = ctrl[ctrl["year"] >= POLICY_YEAR]

    c_pre_years, c_pre_fit = fit_segment(ctrl_pre["year"].to_numpy(),
                                         ctrl_pre[outcome].to_numpy())
    c_post_years, c_post_fit = fit_segment(ctrl_post["year"].to_numpy(),
                                           ctrl_post[outcome].to_numpy())

    if len(c_pre_years) > 0:
        ax1.plot(c_pre_years, c_pre_fit, label="Controls pre", linestyle="--")
    if len(c_post_years) > 0:
        ax1.plot(c_post_years, c_post_fit, label="Controls post", linestyle="--")

    ax1.axvline(POLICY_YEAR, linestyle="--", linewidth=1)
    ax1.set_xlabel("Year")
    ax1.set_title(f"{title_prefix}: DiD (Florida vs Controls)")
    ax1.legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
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
        y_label="MME per 100k",
        title_prefix="Effect of Regulations on Opioid Shipments (FL)",
        out_path=out_ship,
    )

    # Mortality figure
    out_mort = os.path.join(fig_dir, "fl_prepost_did_mortality.png")
    prepost_and_did_plot(
        df=df,
        outcome="drug_death_rate_per_100k",
        y_label="Drug deaths per 100k",
        title_prefix="Effect of Regulations on Mortality (FL)",
        out_path=out_mort,
    )


if __name__ == "__main__":
    main()
