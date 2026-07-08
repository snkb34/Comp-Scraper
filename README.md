# School District Compensation Scraper

A configurable Python starter project for collecting compensation/salary schedule data from school district websites and turning it into comparison-ready CSV/Excel files.

## What it does

- Starts from a list of district compensation/HR pages.
- Finds links likely to contain salary schedules, compensation plans, job classifications, wage schedules, and administrator/teacher/support pay documents.
- Downloads PDFs, Excel files, CSVs, and web tables.
- Extracts tabular data from PDFs and spreadsheets where possible.
- Adds district/source metadata.
- Produces normalized CSV and Excel outputs for comparison.

## Important notes

This tool is intended for public documents only. Always follow each website's terms of use and robots.txt expectations, and keep request rates modest.

PDF table extraction is imperfect. District salary schedules vary widely, so the included normalization logic is intentionally conservative and should be customized for your preferred job-title structure.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
```

## Configure districts

Edit `districts.csv` with one row per district.

```csv
district,state,start_url
Jeffco Public Schools,CO,https://www.jeffcopublicschools.org/...
Denver Public Schools,CO,https://www.dpsk12.org/...
```

## Run

```bash
python run_scraper.py --districts districts.csv --output output
```

## Outputs

- `output/downloads/` downloaded source files
- `output/raw_tables.csv` all extracted rows, minimally cleaned
- `output/normalized_compensation.xlsx` Excel workbook with:
  - Raw Tables
  - Possible Salary Rows
  - Sources
  - Comparison Pivot Ready

## Customization ideas

- Add known compensation page URLs for each district rather than relying only on discovery.
- Add title-matching dictionaries for Superintendent, CHRO, CFO, Principal, Teacher, Bus Driver, Paraeducator, etc.
- Add schedule-specific parsers for common formats such as licensed salary lanes/steps or admin min/mid/max ranges.
