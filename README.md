# Opioid Crisis Data Analysis

## Project Overview
Analysis of opioid prescription patterns and mortality outcomes across 14 U.S. states (2006-2015).

## Data Sources
1. **ARCOS Prescription Data**: DEA database tracking opioid shipments
2. **U.S. Population Data**: County-level demographics from census
3. **Vital Statistics**: CDC mortality data for drug-related deaths

## Processed Datasets
- `arcos_county_year_with_fips.parquet` - 10,254 county-year observations with FIPS codes
- `us_population_condensed_2006_2015.parquet` - Population data by county-year
- `vital_stats_deaths_2006_2015.parquet` - Drug mortality counts by county-year

## Key Notebooks
- `Preprocessing_Prescription.ipynb` - ARCOS data cleaning and aggregation
- `Preprocessing_US_Population.ipynb` - Population data processing
- `Preprocessing_US_VitalStatistics.ipynb` - Mortality data processing

## Coverage
- **States**: 14 (AL, CA, CO, FL, GA, MN, MS, NC, NV, OR, SC, TN, VA, WA)
- **Period**: 2006-2015
- **Counties**: 774 unique county-year combinations

