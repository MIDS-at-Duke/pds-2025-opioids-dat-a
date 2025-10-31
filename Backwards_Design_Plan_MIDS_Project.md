# Backwards Design Plan – Opioid Policy Impact Project

**Course:** Practical Data Science (IDS 720)  
**Team Members:** Tea Tafaj, Diwas , Austin  
**Date:** October 31, 2025  

---

## 1. Project Overview
This project investigates the impact of opioid control policies enacted in Florida (2010) and Washington (2012) on opioid prescription volumes and overdose mortality rates. Using **pre–post** and **difference-in-differences (DiD)** approaches, we aim to identify and visualize the causal effects of these policies through clean, reproducible data science workflows.

---

## 2. Final Deliverables
- **Analytical Outputs**
  - Pre–post plots for both Florida and Washington showing opioid shipments and overdose deaths before and after policy implementation.
  - Difference-in-differences plots comparing treated states (FL, WA) to at least three control states each, with standard error bands.
  - (Optional) Regression tables summarizing DiD models with both level and trend specifications.

- **Written Report / Policy Memo**
  - Stakeholder-friendly summary focused on the key results and implications.
  - Appendix containing methodological details and pre–post plots.

- **Reproducible Repository**
  - Modular Python scripts (no notebooks), structured workflow, and consistent code review process.
  - Proper folder organization for raw, intermediate, and final datasets.
  - Each member commits and reviews code following GitHub best practices.

---

## 3. Final Analysis Dataset
The analysis dataset will be a **county–year panel** (2006–2015), merging ARCOS shipment data with Vital Statistics mortality data. Each observation represents a single county-year.

### Required Variables
| Category | Variables |
|-----------|------------|
| Identifiers | `state_fips`, `county_fips`, `state_name`, `county_name` |
| Time | `year`, `policy_year_relative`, `post_fl`, `post_wa` |
| Treatment | `treated_fl`, `treated_wa` |
| Outcomes | `opioid_shipments_pc`, `overdose_deaths`, `overdose_deaths_pc` |
| Controls | `population`, `censored_flag`, `region_dummies` |

This dataset will enable both graphical and regression-based DiD analyses.

---

## 4. Intermediate Datasets Needed
1. **County-Year Mortality Data (2003–2015)**  
   - Source: U.S. Vital Statistics  
   - Action: Flag censored (<10) values and retain as missing; no artificial imputation.

2. **Opioid Shipments Data (2006–2019)**  
   - Source: Washington Post ARCOS database  
   - Action: Aggregate shipments to county-year level and normalize per capita.

3. **Population and FIPS Crosswalks**  
   - Source: U.S. Census  
   - Action: Join to create consistent county identifiers and compute per-capita metrics.

4. **Policy Reference Table**  
   - States: Florida (Feb 2010), Washington (Jan 2012), optional Texas (Jan 2007).

5. **Control States List**  
   - Identify ≥3 control states per treated state based on pre-policy trend similarity.

---

## 5. Source Data and Processing Workflow
| Dataset | Source | Processing Tasks |
|----------|---------|------------------|
| Vital Statistics | Provided in assignment | Clean, flag censored data, merge with FIPS codes |
| ARCOS Shipments | WaPo / DEA FOIA | Aggregate and merge with population data |
| Population Estimates | U.S. Census | Compute per-capita rates |
| Policy Dates | Class material | Encode treatment and time-relative variables |
| Crosswalks | Public FIPS data | Validate joins and handle naming inconsistencies |

---

## 6. Roles and Responsibilities
| Team Member | Responsibilities |
|--------------|------------------|
| **Tea Tafaj** | Lead on policy encoding and creation of treatment variables; develop DiD plotting script; review Austin’s code. |
| **Diwas** | Lead on ARCOS processing, aggregation, and per-capita calculations; review Tea’s code. |
| **Austin** | Lead on mortality data cleaning and censored-value strategy; review Diwas’s code. |
| **All Members** | Select control states, finalize report, and participate in mutual code reviews. |

---

## 7. Project Timeline
| Phase | Dates | Deliverables |
|--------|--------|--------------|
| Project Planning | Oct 31 – Nov 1 | Finalize backwards design plan |
| Data Cleaning & Integration | Nov 2 – Nov 4 | Intermediate cleaned datasets |
| Unified Dataset Build | Nov 5 – Nov 6 | Complete analysis dataset |
| Visualization Development | Nov 7 – Nov 10 | Pre–post and DiD plots |
| Memo Drafting | Nov 11 – Nov 21 | Draft policy memo and interpretation |

---

## 8. Repository Structure

```plaintext
opioid-policy-impact/
├── README.md
├── backwards-design.md
├── data_raw/                 # Original datasets (excluded from Git)
├── data_intermediate/        # Cleaned datasets (tracked via git-lfs)
├── src/
│   ├── 01_load_mortality.py
│   ├── 02_load_shipments.py
│   ├── 03_build_dataset.py
│   ├── 04_did_plots.py
├── reports/
│   ├── draft_memo.md
│   ├── final_report.pdf
└── Makefile
```

---

## 9. Special Considerations
- **Missing Overdose Counts:** Do not replace censored (<10) observations with arbitrary values. Leave missing and document rationale.  
- **Parallel Trends Check:** Examine pre-policy trajectories between treated and control states to support DiD assumptions.  
- **Exclusions:** Drop Alaska due to inconsistent county definitions.  
- **Version Control Discipline:** Each member must submit at least one PR and conduct one peer review.  

---

### Summary
By following a backwards design approach, our team ensures clarity, accountability, and reproducibility at every stage—from deliverables to data integration. This plan defines what success looks like, what data we need, and who is responsible for each step in completing the Duke MIDS Opioid Policy Impact analysis.
