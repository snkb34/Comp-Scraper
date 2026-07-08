from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pdfplumber
from bs4 import BeautifulSoup

MONEY_RE = re.compile(r"\$?\s*\d{2,3}(?:,\d{3})+(?:\.\d{2})?|\$?\s*\d+\.\d{2}")


def clean_cell(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.dropna(how="all").dropna(axis=1, how="all")
    df = df.map(clean_cell)
    df = df.loc[:, [c for c in df.columns if not df[c].astype(str).str.fullmatch("").all()]]
    df = df[~df.astype(str).apply(lambda row: all(x == "" for x in row), axis=1)]
    df.columns = [f"col_{i+1}" for i in range(len(df.columns))]
    return df.reset_index(drop=True)


def extract_pdf_tables(path: Path) -> list[pd.DataFrame]:
    tables: list[pd.DataFrame] = []
    try:
        with pdfplumber.open(path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_tables = page.extract_tables() or []
                for table_number, table in enumerate(page_tables, start=1):
                    if not table:
                        continue
                    df = pd.DataFrame(table)
                    df = clean_frame(df)
                    if not df.empty:
                        df["source_page"] = page_number
                        df["source_table"] = table_number
                        tables.append(df)
    except Exception as exc:
        print(f"PDF extraction failed for {path}: {exc}")
    return tables


def extract_excel_tables(path: Path) -> list[pd.DataFrame]:
    tables: list[pd.DataFrame] = []
    try:
        sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=str)
        for sheet_name, df in sheets.items():
            df = clean_frame(df)
            if not df.empty:
                df["source_sheet"] = sheet_name
                tables.append(df)
    except Exception as exc:
        print(f"Excel extraction failed for {path}: {exc}")
    return tables


def extract_csv_table(path: Path) -> list[pd.DataFrame]:
    try:
        df = pd.read_csv(path, header=None, dtype=str)
        df = clean_frame(df)
        return [df] if not df.empty else []
    except Exception as exc:
        print(f"CSV extraction failed for {path}: {exc}")
        return []


def extract_html_tables(html: str) -> list[pd.DataFrame]:
    tables: list[pd.DataFrame] = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for table in soup.find_all("table"):
            df = pd.read_html(str(table), header=None)[0]
            df = clean_frame(df)
            if not df.empty:
                tables.append(df)
    except Exception:
        pass
    return tables


def extract_tables_from_file(path: Path) -> list[pd.DataFrame]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_tables(path)
    if suffix in {".xlsx", ".xls"}:
        return extract_excel_tables(path)
    if suffix == ".csv":
        return extract_csv_table(path)
    return []


def row_has_money(row: pd.Series) -> bool:
    text = " | ".join(str(x) for x in row.values)
    return bool(MONEY_RE.search(text))


def parse_money(value: str) -> float | None:
    match = MONEY_RE.search(str(value))
    if not match:
        return None
    cleaned = match.group(0).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None
