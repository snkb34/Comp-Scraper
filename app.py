from __future__ import annotations

import io
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from comp_scraper.config import District, ensure_dirs
from comp_scraper.pipeline import scrape_district, write_outputs, load_districts

APP_TITLE = "School Compensation Data Scraper"
DEFAULT_DISTRICTS = Path("districts.csv")
OUTPUT_ROOT = Path("app_output")

st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.caption("Find public compensation documents, extract tables, and create comparison-ready Excel files.")

with st.sidebar:
    st.header("How this works")
    st.write(
        "1. Add district names and starting URLs.\n"
        "2. Click Run Scraper.\n"
        "3. Review discovered sources and download the Excel workbook."
    )
    st.warning(
        "Use this only for publicly available district pages and documents. Some websites block automated access or publish tables in formats that need manual cleanup."
    )

@st.cache_data(show_spinner=False)
def load_default_districts() -> pd.DataFrame:
    if DEFAULT_DISTRICTS.exists():
        return pd.read_csv(DEFAULT_DISTRICTS)
    return pd.DataFrame(
        [
            {"district": "Jeffco Public Schools", "state": "CO", "start_url": "https://www.jeffcopublicschools.org/"},
            {"district": "Cherry Creek Schools", "state": "CO", "start_url": "https://www.cherrycreekschools.org/"},
            {"district": "Denver Public Schools", "state": "CO", "start_url": "https://www.dpsk12.org/"},
        ]
    )

uploaded = st.file_uploader("Optional: upload your own districts CSV", type=["csv"])
if uploaded:
    districts_df = pd.read_csv(uploaded)
else:
    districts_df = load_default_districts()

required_columns = ["district", "state", "start_url"]
for col in required_columns:
    if col not in districts_df.columns:
        districts_df[col] = ""

districts_df = districts_df[required_columns]

st.subheader("District List")
edited_df = st.data_editor(
    districts_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "district": st.column_config.TextColumn("District", required=True),
        "state": st.column_config.TextColumn("State", required=True),
        "start_url": st.column_config.LinkColumn("Starting URL", required=True),
    },
)

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    run = st.button("Run Scraper", type="primary", use_container_width=True)
with col2:
    clear = st.button("Clear App Output", use_container_width=True)

if clear:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    st.success("App output cleared.")

if run:
    clean_df = edited_df.copy()
    clean_df = clean_df.dropna(how="all")
    clean_df = clean_df[(clean_df["district"].astype(str).str.strip() != "") & (clean_df["start_url"].astype(str).str.strip() != "")]

    if clean_df.empty:
        st.error("Add at least one district with a starting URL.")
        st.stop()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_ROOT / f"run_{timestamp}"
    output_dirs = ensure_dirs(output_dir)

    districts = [District(str(r.district), str(r.state), str(r.start_url)) for r in clean_df.itertuples(index=False)]
    all_tables: list[pd.DataFrame] = []
    all_sources = []

    progress = st.progress(0)
    status = st.empty()

    for idx, district in enumerate(districts, start=1):
        status.info(f"Searching {district.district}...")
        tables, sources = scrape_district(district, output_dirs)
        all_tables.extend(tables)
        all_sources.extend(sources)
        progress.progress(idx / len(districts))

    status.info("Writing Excel and CSV outputs...")
    write_outputs(all_tables, all_sources, output_dirs)
    status.success("Done.")

    st.session_state["latest_output_dir"] = str(output_dir)

latest_output_dir = Path(st.session_state.get("latest_output_dir", "")) if st.session_state.get("latest_output_dir") else None

if latest_output_dir and latest_output_dir.exists():
    st.subheader("Latest Results")
    sources_path = latest_output_dir / "sources.csv"
    comparison_path = latest_output_dir / "comparison_pivot_ready.csv"
    excel_path = latest_output_dir / "normalized_compensation.xlsx"

    if sources_path.exists():
        sources_df = pd.read_csv(sources_path)
        st.markdown("**Sources Found / Attempted**")
        st.dataframe(sources_df, use_container_width=True)

    if comparison_path.exists():
        comparison_df = pd.read_csv(comparison_path)
        st.markdown("**Comparison Pivot Ready Rows**")
        st.dataframe(comparison_df, use_container_width=True)

    download_cols = st.columns(3)
    if excel_path.exists():
        with open(excel_path, "rb") as f:
            download_cols[0].download_button(
                "Download Excel Workbook",
                data=f,
                file_name="normalized_compensation.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    if comparison_path.exists():
        download_cols[1].download_button(
            "Download Comparison CSV",
            data=comparison_path.read_bytes(),
            file_name="comparison_pivot_ready.csv",
            mime="text/csv",
            use_container_width=True,
        )
    if sources_path.exists():
        download_cols[2].download_button(
            "Download Sources CSV",
            data=sources_path.read_bytes(),
            file_name="sources.csv",
            mime="text/csv",
            use_container_width=True,
        )
else:
    st.info("No app run yet. Add districts and click Run Scraper.")

st.divider()
st.subheader("Recommended Next Features")
st.write(
    "This first app is intentionally simple. The next upgrades would be: title matching/crosswalks, district-specific source rules, "
    "manual review queue, compensation category tagging, and a polished board-ready comparison workbook."
)
