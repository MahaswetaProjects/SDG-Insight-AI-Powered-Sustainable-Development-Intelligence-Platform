# SDG Country Explorer — analysis-only starter

## What's included
- `app.py`: interactive Streamlit dashboard
- `country_overview.csv`: country-level SDG scores, ranks, goal statuses and trends
- `sdr_2026_country_data.csv`: wider country-level table from the SDR2026 Data sheet
- `all_raw_data_cleaned.csv`: country-year indicator table from All Raw Data
- `backdated_sdg_index_cleaned.csv`: historical SDG index values
- `country_ranks_over_time.csv`: historical rankings
- `indicator_codebook.csv`: indicator labels, definitions and metadata
- `analysis.ipynb`: notebook to inspect, clean, analyze and visualize the supplied workbook

## Run the dashboard
1. Put all files in the same folder.
2. Install dependencies:
   `python -m pip install -r requirements.txt`
3. Run:
   `streamlit run app.py`

## Notes
- The supplied workbook is SDR 2026, not SDR 2025.
- Raw indicator values have substantial missingness. Missing observations are preserved rather than silently imputed.
- The backdated SDG Index is retrospectively calculated and uses carried-forward values for some missing years. Use caution when interpreting long-run changes.
- This first version is descriptive analysis only. No chatbot, recommendations, causal claims or forecasting are included yet.
