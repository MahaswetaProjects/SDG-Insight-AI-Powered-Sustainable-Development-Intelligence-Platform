
from pathlib import Path
import re
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="SDG Country Explorer", page_icon="🌍", layout="wide")

st.title("🌍 SDG Country Explorer")
st.caption("Explore SDG performance, indicator data and historical progress using the Sustainable Development Report 2026 database.")

BASE = Path(__file__).resolve().parent

@st.cache_data
def load_data():
    overview = pd.read_csv(BASE / "country_overview.csv")
    raw = pd.read_csv(BASE / "all_raw_data_cleaned.csv")
    backdated = pd.read_csv(BASE / "backdated_sdg_index_cleaned.csv")
    codebook = pd.read_csv(BASE / "indicator_codebook.csv")
    ranks = pd.read_csv(BASE / "country_ranks_over_time.csv")
    # Ensure expected numeric types
    for c in ["2026 SDG Index Score", "2026 SDG Index Rank", "International Spillovers Score (0-100)"]:
        if c in overview:
            overview[c] = pd.to_numeric(overview[c], errors="coerce")
    raw["year"] = pd.to_numeric(raw["year"], errors="coerce")
    backdated["year"] = pd.to_numeric(backdated["year"], errors="coerce")
    backdated["sdgi_s"] = pd.to_numeric(backdated["sdgi_s"], errors="coerce")
    return overview, raw, backdated, codebook, ranks

overview, raw, backdated, codebook, ranks = load_data()

# Sidebar filters
st.sidebar.header("Explore the data")
regions = sorted(overview["Regions used for the SDR"].dropna().astype(str).unique()) if "Regions used for the SDR" in overview else []
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
filtered_overview = overview[overview["Regions used for the SDR"].astype(str).isin(selected_regions)] if selected_regions else overview.iloc[0:0]
country_options = sorted(filtered_overview["country"].dropna().unique())
if not country_options:
    country_options = sorted(overview["country"].dropna().unique())
selected_country = st.sidebar.selectbox("Country profile", country_options, index=0)
min_year = int(raw["year"].min())
max_year = int(raw["year"].max())
year_range = st.sidebar.slider("Raw indicator years", min_value=min_year, max_value=max_year, value=(max(min_year, 2015), max_year))

# KPI row
country_row = overview.loc[overview["country"] == selected_country]
score_col = "2026 SDG Index Score"
rank_col = "2026 SDG Index Rank"
spill_col = "International Spillovers Score (0-100)"
k1, k2, k3, k4 = st.columns(4)
k1.metric("2026 SDG Index score", f"{country_row[score_col].iloc[0]:.1f}" if len(country_row) and pd.notna(country_row[score_col].iloc[0]) else "N/A")
k2.metric("2026 rank", f"{int(country_row[rank_col].iloc[0])}" if len(country_row) and pd.notna(country_row[rank_col].iloc[0]) else "N/A")
k3.metric("Spillovers score", f"{country_row[spill_col].iloc[0]:.1f}" if len(country_row) and pd.notna(country_row[spill_col].iloc[0]) else "N/A")
k4.metric("Countries in selected regions", f"{len(filtered_overview):,}")

tab1, tab2, tab3, tab4 = st.tabs(["Global overview", "Country profile", "Indicator explorer", "Data quality"])

with tab1:
    st.subheader("Highest SDG Index scores")
    rank_data = filtered_overview.dropna(subset=[score_col]).sort_values(score_col, ascending=False).head(15)
    if not rank_data.empty:
        fig = px.bar(rank_data.sort_values(score_col), x=score_col, y="country", orientation="h",
                     labels={score_col:"SDG Index score", "country":"Country"},
                     title="Top 15 countries by 2026 SDG Index score", hover_data=[rank_col])
        fig.update_layout(height=560, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.subheader("Score distribution")
        fig = px.histogram(filtered_overview.dropna(subset=[score_col]), x=score_col, nbins=20,
                           labels={score_col:"SDG Index score"}, title="Distribution of country scores")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        if spill_col in filtered_overview and score_col in filtered_overview:
            st.subheader("SDG score vs international spillovers")
            fig = px.scatter(filtered_overview, x=score_col, y=spill_col, hover_name="country",
                             color="Regions used for the SDR",
                             labels={score_col:"SDG Index score", spill_col:"Spillovers score"},
                             title="Country scores and international spillovers")
            st.plotly_chart(fig, use_container_width=True)
    st.subheader("Country ranking table")
    show_cols = [c for c in ["country", "Regions used for the SDR", score_col, rank_col, spill_col] if c in filtered_overview]
    st.dataframe(filtered_overview[show_cols].sort_values(rank_col), use_container_width=True, hide_index=True)

with tab2:
    st.subheader(f"{selected_country}: SDG performance")
    row = overview.loc[overview["country"] == selected_country]
    goal_cols = [f"Goal {i} Dash" for i in range(1, 18) if f"Goal {i} Dash" in overview.columns]
    goal_trend_cols = [f"Goal {i} Trend" for i in range(1, 18) if f"Goal {i} Trend" in overview.columns]
    if len(row):
        goal_records = []
        for i in range(1,18):
            dash_col, trend_col = f"Goal {i} Dash", f"Goal {i} Trend"
            if dash_col in overview.columns:
                goal_records.append({"Goal": f"SDG {i}", "Dashboard status": row[dash_col].iloc[0],
                                     "Trend": row[trend_col].iloc[0] if trend_col in overview.columns else "Unknown"})
        goals = pd.DataFrame(goal_records)
        status_order = ["green", "yellow", "orange", "red", "grey"]
        goals["Dashboard status"] = pd.Categorical(goals["Dashboard status"], categories=status_order, ordered=True)
        fig = px.bar(goals, x="Goal", y=[1]*len(goals), color="Dashboard status",
                     hover_data=["Trend"], title="Goal dashboard status (color categories from the source workbook)",
                     labels={"y":"Goal"})
        fig.update_layout(showlegend=True, yaxis={"visible":False}, height=330)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(goals.astype({"Dashboard status":"string"}), use_container_width=True, hide_index=True)
    hist = backdated.loc[backdated["country"] == selected_country].dropna(subset=["sdgi_s"]).sort_values("year")
    if not hist.empty:
        st.subheader("Historical SDG Index score")
        fig = px.line(hist, x="year", y="sdgi_s", markers=True,
                      labels={"year":"Year", "sdgi_s":"Backdated SDG Index score"},
                      title="Retrospectively calculated index over time")
        fig.update_layout(yaxis_range=[0,100])
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Historical scores are retrospectively calculated using the report's methodology and carried-forward values where data are missing. Interpret changes with that caveat.")
    else:
        st.info("No historical index-score series is available for this country.")

with tab3:
    st.subheader("Explore raw indicator observations")
    indicator_cols = [c for c in raw.columns if re.match(r"^sdg\d+_", str(c))]
    code_lookup = codebook.copy()
    if "IndCode" in code_lookup.columns:
        code_lookup["IndCode"] = code_lookup["IndCode"].astype(str)
    label_by_code = {}
    if {"IndCode","Indicator"}.issubset(code_lookup.columns):
        label_by_code = dict(zip(code_lookup["IndCode"], code_lookup["Indicator"]))
    display_labels = {c: f"{label_by_code.get(c, c)} [{c}]" for c in indicator_cols}
    selected_label = st.selectbox("Indicator", list(display_labels.values()))
    selected_indicator = next(c for c, label in display_labels.items() if label == selected_label)
    country_subset = st.checkbox("Show all countries (instead of selected country)", value=False)
    indicator_data = raw[(raw["year"] >= year_range[0]) & (raw["year"] <= year_range[1])].copy()
    if not country_subset:
        indicator_data = indicator_data[indicator_data["country"] == selected_country]
    indicator_data[selected_indicator] = pd.to_numeric(indicator_data[selected_indicator], errors="coerce")
    indicator_data = indicator_data.dropna(subset=[selected_indicator])
    if not indicator_data.empty:
        if country_subset:
            latest_year = indicator_data["year"].max()
            latest = indicator_data[indicator_data["year"] == latest_year].sort_values(selected_indicator, ascending=False)
            fig = px.bar(latest.head(20), x=selected_indicator, y="country", orientation="h",
                         labels={selected_indicator:label_by_code.get(selected_indicator, selected_indicator), "country":"Country"},
                         title=f"Countries with highest reported values in {int(latest_year)} (top 20)")
            fig.update_layout(height=600, yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Higher raw values are not always better. Check the indicator definition and direction in the codebook.")
        else:
            fig = px.line(indicator_data.sort_values("year"), x="year", y=selected_indicator, markers=True,
                          labels={"year":"Year", selected_indicator:label_by_code.get(selected_indicator, selected_indicator)},
                          title=f"{label_by_code.get(selected_indicator, selected_indicator)} — {selected_country}")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(indicator_data[["country","year",selected_indicator]].sort_values(["year","country"]), use_container_width=True, hide_index=True)
    else:
        st.warning("No non-missing observations for this selection and year range.")

with tab4:
    st.subheader("Data quality and coverage")
    numeric_indicators = [c for c in raw.columns if re.match(r"^sdg\d+_", str(c))]
    if numeric_indicators:
        miss = raw[numeric_indicators].isna().mean().sort_values(ascending=False).reset_index()
        miss.columns = ["Indicator code","Missing fraction"]
        miss["Missing percentage"] = (miss["Missing fraction"]*100).round(1)
        fig = px.bar(miss.head(20).sort_values("Missing percentage"), x="Missing percentage", y="Indicator code",
                     orientation="h", title="20 indicators with the most missing values")
        fig.update_layout(height=620)
        st.plotly_chart(fig, use_container_width=True)
        st.metric("Raw data rows", f"{len(raw):,}")
        st.metric("Indicator columns", f"{len(numeric_indicators):,}")
        st.metric("Overall missingness across indicator cells", f"{raw[numeric_indicators].isna().mean().mean()*100:.1f}%")
        st.caption("Missing values are preserved as missing; this app does not silently impute raw indicator observations.")
    st.download_button("Download filtered country overview", filtered_overview.to_csv(index=False).encode("utf-8"), "filtered_country_overview.csv", "text/csv")
    st.download_button("Download cleaned raw data", raw.to_csv(index=False).encode("utf-8"), "all_raw_data_cleaned.csv", "text/csv")

st.sidebar.markdown("---")
st.sidebar.caption("Source: Sustainable Development Report 2026 database supplied for this project. This dashboard is descriptive analysis only; it does not make causal claims.")
