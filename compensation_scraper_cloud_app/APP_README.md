# School Compensation Scraper App

This version adds a simple browser-based app using Streamlit.

## One-time setup

1. Install Python 3.12 or newer.
2. Open Command Prompt or PowerShell in this folder.
3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Run the app

From this folder, run:

```bash
python -m streamlit run app.py
```

or:

```bash
python run_app.py
```

A browser window should open. If it does not, copy the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Using the app

1. Add or edit district rows in the table.
2. Use a district homepage, HR page, compensation page, transparency page, or salary schedule page as the starting URL.
3. Click **Run Scraper**.
4. Review sources and comparison-ready rows.
5. Download the Excel workbook.

## Important notes

- The app only attempts to collect publicly available information.
- Some district websites block automated requests.
- PDF tables vary widely. Some will extract cleanly; others will need manual cleanup.
- The first run may take several minutes depending on the number of districts and PDFs.

## Suggested starting URLs

Use pages likely to link to compensation documents, such as:

- Human Resources
- Careers / Employment
- Salary Schedules
- Financial Transparency
- Collective Bargaining Agreements
- Board documents

