from __future__ import annotations

import re

import pandas as pd
from rapidfuzz import process, fuzz

from .extractors import parse_money, row_has_money

TITLE_MAP = {
    "Superintendent": ["superintendent"],
    "Chief Human Resources Officer": ["chief human resources", "chief of human resources", "chro", "chief talent"],
    "Chief Financial Officer": ["chief financial", "cfo"],
    "Principal": ["principal", "elementary principal", "middle school principal", "high school principal"],
    "Assistant Principal": ["assistant principal", "dean"],
    "Teacher": ["teacher", "licensed", "certified"],
    "Bus Driver": ["bus driver", "transportation driver"],
    "Paraeducator": ["paraeducator", "paraprofessional", "instructional aide"],
}


def detect_role(text: str) -> str | None:
    lower = text.lower()
    for canonical, patterns in TITLE_MAP.items():
        if any(p in lower for p in patterns):
            return canonical
    choices = list(TITLE_MAP.keys())
    match = process.extractOne(text, choices, scorer=fuzz.WRatio)
    if match and match[1] >= 88:
        return match[0]
    return None


def infer_values(row_text: str) -> dict:
    money_values = []
    for part in re.split(r"\s+|\|", row_text):
        val = parse_money(part)
        if val is not None:
            money_values.append(val)
    # fallback: parse across full text
    if not money_values:
        val = parse_money(row_text)
        if val is not None:
            money_values.append(val)

    unique_vals = []
    for val in money_values:
        if val not in unique_vals:
            unique_vals.append(val)

    result = {"min_pay": None, "mid_pay": None, "max_pay": None, "hourly_or_annual": None}
    if unique_vals:
        sorted_vals = sorted(unique_vals)
        result["min_pay"] = sorted_vals[0]
        result["max_pay"] = sorted_vals[-1]
        if len(sorted_vals) >= 3:
            result["mid_pay"] = sorted_vals[len(sorted_vals) // 2]
        elif len(sorted_vals) == 2:
            result["mid_pay"] = round((sorted_vals[0] + sorted_vals[1]) / 2, 2)
        else:
            result["mid_pay"] = sorted_vals[0]
        result["hourly_or_annual"] = "hourly" if sorted_vals[-1] < 500 else "annual"
    return result


def build_comparison_rows(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame()

    rows = []
    data_cols = [c for c in raw_df.columns if c.startswith("col_")]
    for _, row in raw_df.iterrows():
        if not row_has_money(row[data_cols]):
            continue
        row_text = " | ".join(str(row.get(c, "")) for c in data_cols)
        role = detect_role(row_text)
        values = infer_values(row_text)
        rows.append({
            "district": row.get("district"),
            "state": row.get("state"),
            "canonical_role": role,
            "raw_row_text": row_text,
            "min_pay": values["min_pay"],
            "mid_pay": values["mid_pay"],
            "max_pay": values["max_pay"],
            "hourly_or_annual": values["hourly_or_annual"],
            "source_url": row.get("source_url"),
            "source_file": row.get("source_file"),
            "source_page": row.get("source_page"),
            "source_sheet": row.get("source_sheet"),
        })
    return pd.DataFrame(rows)
