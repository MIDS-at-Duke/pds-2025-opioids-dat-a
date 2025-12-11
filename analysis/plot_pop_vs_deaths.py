"""
Generate Population vs Deaths scatter plot for the report.
Shows the relationship used for imputation of suppressed values.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from pathlib import Path

# Paths
DATA = Path("data/processed")
OUTPUT = Path("outputs/figures")
OUTPUT.mkdir(parents=True, exist_ok=True)

# Load data
panel = pd.read_parquet(DATA / "opioid_panel_2006_2015.parquet")

# Separate observed vs imputed
observed = panel[panel['death_imputed'] == 0]
imputed = panel[panel['death_imputed'] == 1]

print(f"Observed: {len(observed):,} rows")
print(f"Imputed: {len(imputed):,} rows")

# Create figure
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Plot 1: Population vs Deaths (observed only) with regression line
ax1 = axes[0]
ax1.scatter(observed['population']/1000, observed['drug_deaths'], 
            alpha=0.3, s=10, color='blue', label='Observed')
ax1.axhline(y=10, color='red', linestyle='--', linewidth=1.5, 
            label='Suppression threshold (10)')

# Add regression line
X = observed[['population']].values
y = observed['drug_deaths'].values
model = LinearRegression().fit(X, y)
x_line = np.linspace(0, observed['population'].max(), 100)
y_line = model.predict(x_line.reshape(-1, 1))
ax1.plot(x_line/1000, y_line, 'green', linewidth=2, 
         label=f'Regression (R²={model.score(X, y):.2f})')

ax1.set_xlabel('Population (thousands)', fontsize=11)
ax1.set_ylabel('Drug Deaths', fontsize=11)
ax1.set_title('Population vs Deaths\n(Observed Data Only)', fontsize=12, fontweight='bold')
ax1.legend(loc='upper left')
ax1.set_xlim(0, 1000)
ax1.set_ylim(0, 200)

# Plot 2: Show imputation result
ax2 = axes[1]
ax2.scatter(observed['population']/1000, observed['drug_deaths'], 
            alpha=0.2, s=10, color='blue', label='Observed (≥10)')
ax2.scatter(imputed['population']/1000, imputed['drug_deaths'], 
            alpha=0.3, s=10, color='orange', label='Imputed (0-9)')
ax2.axhline(y=10, color='red', linestyle='--', linewidth=1.5)

ax2.set_xlabel('Population (thousands)', fontsize=11)
ax2.set_ylabel('Drug Deaths', fontsize=11)
ax2.set_title('Population vs Deaths\n(Including Imputed Values)', fontsize=12, fontweight='bold')
ax2.legend(loc='upper left')
ax2.set_xlim(0, 500)
ax2.set_ylim(0, 100)

plt.tight_layout()
plt.savefig(OUTPUT / "population_vs_deaths.png", dpi=150, bbox_inches='tight')
print(f"✓ Saved: {OUTPUT / 'population_vs_deaths.png'}")
plt.close()
