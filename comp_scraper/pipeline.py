from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from .config import District, MAX_LINKS_PER_DISTRICT, SourceRecord, ensure_dirs
from .extractors import extract_html_tables, extract_tables_from_file
from .normalizer import build_comparison_rows
from .web_utils import discover_links, download_file, fetch_html, get_session, is_supported_file


def load_districts(path: str | Path) -> list[District]:
    df = pd.read_csv(path)
    required = {"district", "state", "start_url"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"districts.csv is missing columns: {missing}")
    return [District(str(r.district), str(r.state), str(r.start_url)) for r in df.itertuples(index=False)]


def add_metadata(df: pd.DataFrame, district: District, source_url: str, local_path: Path | None) -> pd.DataFrame:
    df = df.copy()
    df["district"] = district.district
    df["state"] = district.state
    df["source_url"] = source_url
    df["source_file"] = str(local_path) if local_path else None
    return df


def scrape_district(district: District, output_dirs: dict[str, Path]) -> tuple[list[pd.DataFrame], list[SourceRecord]]:
    session = get_session()
    tables: list[pd.DataFrame] = []
    sources: list[SourceRecord] = []

    links = discover_links(session, district.start_url, MAX_LINKS_PER_DISTRICT)
    if district.start_url not in links:
        links.insert(0, district.start_url)

    for url in tqdm(links, desc=district.district, leave=False):
        if is_supported_file(url):
            local_path = download_file(session, url, district.district, output_dirs["downloads"])
            if not local_path:
                sources.append(SourceRecord(district.district, district.state, url, None, "file", "failed", "Download failed or file too large"))
                continue
            extracted = extract_tables_from_file(local_path)
            for table in extracted:
                tables.append(add_metadata(table, district, url, local_path))
            sources.append(SourceRecord(district.district, district.state, url, str(local_path), local_path.suffix.lower(), "ok", f"{len(extracted)} tables"))
        else:
            html = fetch_html(session, url)
            if not html:
                sources.append(SourceRecord(district.district, district.state, url, None, "html", "failed", "Could not fetch HTML"))
                continue
            extracted = extract_html_tables(html)
            for table in extracted:
                tables.append(add_metadata(table, district, url, None))
            sources.append(SourceRecord(district.district, district.state, url, None, "html", "ok", f"{len(extracted)} tables"))

    return tables, sources


def write_outputs(raw_tables: list[pd.DataFrame], sources: list[SourceRecord], output_dirs: dict[str, Path]) -> None:
    base = output_dirs["base"]

    if raw_tables:
        raw_df = pd.concat(raw_tables, ignore_index=True, sort=False)
    else:
        raw_df = pd.DataFrame()

    sources_df = pd.DataFrame([s.__dict__ for s in sources])
    comparison_df = build_comparison_rows(raw_df) if not raw_df.empty else pd.DataFrame()
    possible_salary_rows = comparison_df[comparison_df["min_pay"].notna()].copy() if not comparison_df.empty else pd.DataFrame()

    raw_csv = base / "raw_tables.csv"
    sources_csv = base / "sources.csv"
    comparison_csv = base / "comparison_pivot_ready.csv"
    excel_path = base / "normalized_compensation.xlsx"

    raw_df.to_csv(raw_csv, index=False)
    sources_df.to_csv(sources_csv, index=False)
    comparison_df.to_csv(comparison_csv, index=False)

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        raw_df.to_excel(writer, index=False, sheet_name="Raw Tables")
        possible_salary_rows.to_excel(writer, index=False, sheet_name="Possible Salary Rows")
        sources_df.to_excel(writer, index=False, sheet_name="Sources")
        comparison_df.to_excel(writer, index=False, sheet_name="Comparison Pivot Ready")

        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            for col in sheet.columns:
                max_len = 12
                col_letter = col[0].column_letter
                for cell in col[:100]:
                    try:
                        max_len = max(max_len, min(len(str(cell.value)), 60))
                    except Exception:
                        pass
                sheet.column_dimensions[col_letter].width = max_len + 2

    print(f"Wrote: {raw_csv}")
    print(f"Wrote: {sources_csv}")
    print(f"Wrote: {comparison_csv}")
    print(f"Wrote: {excel_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape public school district compensation data.")
    parser.add_argument("--districts", default="districts.csv", help="CSV with district,state,start_url columns")
    parser.add_argument("--output", default="output", help="Output directory")
    args = parser.parse_args()

    output_dirs = ensure_dirs(args.output)
    districts = load_districts(args.districts)

    all_tables: list[pd.DataFrame] = []
    all_sources: list[SourceRecord] = []

    for district in tqdm(districts, desc="Districts"):
        tables, sources = scrape_district(district, output_dirs)
        all_tables.extend(tables)
        all_sources.extend(sources)

    write_outputs(all_tables, all_sources, output_dirs)


if __name__ == "__main__":
    main()
