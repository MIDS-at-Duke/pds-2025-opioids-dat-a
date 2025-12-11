# Evaluating Opioid Policy Interventions: FL vs. WA (2006-2015)

[![Duke MIDS](https://img.shields.io/badge/Duke-MIDS%20IDS%20720-012169?style=flat-square)](https://datascience.duke.edu/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

> **TL;DR:** Difference-in-differences analysis revealing that Florida's 2010 regulatory crackdown reduced opioid deaths by 2.36 per 100k (≈450 lives/year), while Washington's 2012 voluntary guidelines showed temporary effects that reversed within 2 years.

--

## 📋 Project Overview

This repository contains a comprehensive data science analysis evaluating the effectiveness of two state-level opioid policy interventions:

- **Florida (2010)**: Mandatory pain clinic registration, real-time PDMP, multi-agency enforcement
- **Washington (2012)**: Evidence-based prescribing guidelines with voluntary compliance

**Research Question:** Do strict regulatory interventions work better than voluntary prescribing guidelines for reducing opioid harm?

**Methods:** Difference-in-differences (DiD) regression with county fixed effects, 6 control states per treatment state, 2006-2015 county-year panel data.

**Key Deliverable:** [**Policy Memo (PDF)**](reports/FINAL_REPORT.pdf) - Data Science Memo format for state health policy directors

--

## 🎯 Key Findings

### Florida's Regulatory Approach ✅ **Highly Effective**

| Outcome | Effect Size | Statistical Significance | Interpretation |
|-----|-------|-------------|--------|
| **Opioid Shipments** | -18.1M MME/100k (immediate)<br>-20.0M MME/year (trend) | p<0.001<br>p<0.001 | Sharp drop, accelerating decline |
| **Drug Deaths** | -2.58 per 100k | p<0.001 | ≈500 lives saved annually |

### Washington's Voluntary Approach ⚠️ **Mixed Results**

| Outcome | Effect Size | Statistical Significance | Interpretation |
|-----|-------|-------------|--------|
| **Opioid Shipments** | -13.5M MME/100k (initial)<br>**+6.4M MME/year (reversal)** | p=0.004<br>p<0.001 | Temporary dip, then upward reversal |
| **Drug Deaths** | -1.94 per 100k | p=0.007 | Reduction in urban centers, but supply failed |

### Bottom Line

✅ **Regulatory enforcement produces durable change**  
⚠️ **Voluntary education improves mortality but fails to control supply**

--

## 📁 Repository Structure

```
pds-2025-opioids-dat-a/
│
├── reports/                    # Final deliverables
│   ├── FINAL_REPORT.pdf        # Policy memo (10 pages)
│   └── FINAL_REPORT.tex        # LaTeX source
│
├── analysis/                   # Core analysis scripts
│   ├── run_did_regressions.py  # Main DiD models
│   ├── plot_pop_vs_deaths.py   # Population vs deaths plot
│   ├── fl_did_trends.py        # Florida visualizations
│   ├── wa_did_trends.py        # Washington visualizations
│   └── robustness_checks.py    # Sensitivity analyses
│
├── src/                        # Data processing
│   ├── build_panel.py          # Merge datasets → analysis panels
│   └── requirements.txt        # Packages required
│
├── notebooks/                  # Data preprocessing (Jupyter)
│   ├── Extract_ARCOS_from_ZIP.ipynb
│   ├── Preprocessing_Prescription.ipynb
│   ├── Preprocessing_US_Population.ipynb
│   └── Preprocessing_US_VitalStatistics.ipynb
│
├── data/
│   ├── raw/                    # Original data (not all in repo - too large)
│       ├── US_VitalStatistics/ # Folder for VitalStatistics data
│       ├── arcos_filtered_2006_2015.parquet
│       └── us.1969_2023.singleages.through89.90plus.adjusted.txt.gz
│   └── processed/              # Analysis-ready datasets
│       ├── fl_panel_clean.parquet  (840 rows, 84 counties)
│       ├── wa_panel_clean.parquet  (670 rows, 67 counties)
│       ├── arcos_county_year_with_fips.parquet
│       ├── opioid_panel_2006_2015.parquet
│       ├── us_population_condensed_2006_2015.parquet
│       └── vital_stats_deaths_2006_2015.parquet 
│
├── outputs/
│   ├── figures/                # DiD plots with CI
│       ├── fl_prepost_did_mortality.png
│       ├── fl_prepost_did_shipments.png
│       ├── population_vs_deaths.png
│       ├── population_vs_deaths_scatter.png
│       ├── wa_prepost_did_mortality.png
│       └── wa_prepost_did_shipments.png
│   └── tables/                 # Regression results (CSV)
│       ├── did_comparison_original_vs_imputed.csv
│       ├── did_regression_results.csv
│       ├── did_results_FL_WA.csv
│       ├── pre_post_mean_deaths_FL_WA.csv
│       └── robustness_checks.csv
│
├── reference/
│   └── fips.txt
├── documentation/              # Project planning docs
│   ├── Backwards_Design_Plan_MIDS_Project.md
│   ├── Control_States_Justification.docx
│   ├── PDS_ProjectSummary.pdf
│   ├── Rough_Draft_Policy_Memo.md
│   └── Rough_Draft_Policy_Memo.pdf
```

--

## 🔬 Data Sources

| Source | Description | Coverage | Size |
|----|-------|-----|---|
| **DEA ARCOS** | Complete census of controlled substance shipments | 218.5M transactions, 2006-2015 | ~228GB raw |
| **CDC WONDER** | Vital statistics mortality data | Drug-induced deaths (ICD-10: X40-X44, X60-X64, Y10-Y14) | 2,569 county-years |
| **U.S. Census** | Annual county population estimates | Denominator for per-capita rates | 31K county-years |

### Data Quality & Validation

✅ **MME Calculation Validated:** Florida 2010 MME/capita (~1,649) is 1.7-2.3x higher than CDC retail-only estimates (729-994), as expected since we include hospital/practitioner shipments per CDC guidance for supply-side policy evaluation.

✅ **Privacy Suppression Handled:** CDC suppresses death counts <10. We applied data-driven filters (population ≥50k, suppression rate ≤40%) reducing suppressed values from 28,838 to 203 (0.7%). Remaining values imputed using avg death rate × population, constrained to [0,9].

✅ **Filters Applied:**
- Transaction type: Sales only (`TRANSACTION_CODE = 'S'`)
- Buyer type: Retail endpoints only (pharmacies, hospitals, practitioners)
- Outliers: Excluded MME > 1M per transaction

--

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.8+
pip install pandas numpy statsmodels matplotlib scipy
```

### Reproduce Analysis

```bash
# 1. Build analysis panels (requires processed data)
python src/build_panel.py

# 2. Run DiD regressions
python analysis/run_did_regressions.py

# 3. Generate visualizations
python analysis/fl_did_trends.py
python analysis/wa_did_trends.py

# 4. Run robustness checks
python analysis/robustness_checks.py
```

### View Results

📄 **Main Report:** [`reports/FINAL_REPORT.pdf`](reports/FINAL_REPORT.pdf)

📊 **Figures:** `outputs/figures/*.png`

📈 **Tables:** `outputs/tables/*.csv`

--

## 📊 Methodology

### Difference-in-Differences Design

**Treatment States:** FL (2010), WA (2012)  
**Control States:**
- Florida: GA, AL, SC, NC, TN, MS (n=6)
- Washington: OR, CO, MN, NV, CA, VA (n=6)

**Model Specifications:**
1. **Level Change:** Immediate policy impact (did outcomes jump?)
2. **Trend Change:** Sustained trajectory shift (did the slope change?)

**Fixed Effects:** County + Year  
**Standard Errors:** Clustered at county level  

### Control State Selection Criteria

✅ No major opioid regulations 2006-2015  
✅ Parallel pre-policy trends (visual inspection)  
✅ Similar demographics & healthcare systems  
✅ Complete pre-period data availability  

--

## 🔍 Robustness Checks (Appendix E)

| Test | Result | Interpretation |
|---|----|--------|
| **Alternative Control Groups** | Effect weaker with 3 vs 6 controls | Justifies using broader control group |
| **Population Weighting** | Effect strengthens (−3.05 vs −2.36) | Not driven by small counties |
| **Placebo Test (2008)** | Deaths: no effect; Shipments: pre-trend | Mortality findings robust; shipments caveat |
| **Border Exclusion** | Effects remain robust (−2.33) | No spillover contamination |

**Conclusion:** Mortality findings are robust across all specifications. Shipment results should be interpreted with caution due to pre-existing trends.

--

## 📝 Citation

If you use this analysis, please cite:

```bibtex
@techreport{tafaj2025opioid,
  title={Evaluating Opioid Policy Interventions: Evidence from Florida and Washington},
  author={Tafaj, Tea and Puri, Diwas and Zhang, Xinhao},
  institution={Duke University, MIDS Program},
  year={2025},
  type={Data Science Memo},
  url={https://github.com/MIDS-at-Duke/pds-2025-opioids-dat-a}
}
```

--

## 👥 Authors

**Tea Tafaj** | **Diwas Puri** | **Xinhao Zhang**  
Duke University Master of Interdisciplinary Data Science (MIDS)  
IDS 720: Practical Data Science (Fall 2024)

--

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

--

## 🙏 Acknowledgments

- **Instructor:** Prof. Nick Eubank, Duke University
- **Data Sources:** DEA ARCOS (via Washington Post FOIA), CDC WONDER, U.S. Census Bureau
- **References:**
  - CDC Opioid Dispensing Rates: [cdc.gov/drugoverdose](https://www.cdc.gov/drugoverdose/rxrate-maps/county.html)
  - ARCOS API Issue: [wpinvestigative/arcos-api#1](https://github.com/wpinvestigative/arcos-api/issues/1)

--

**Last Updated:** December 2024  

