# School Compensation Scraper — Cloud Web App

This version is designed to run as an internet-accessible web app so users do **not** need to install Python or local desktop software.

## What the app does

- Lets users enter or upload a district list.
- Searches public district websites for compensation, salary, pay plan, collective bargaining, and benefits documents.
- Downloads supported public files.
- Extracts tables from PDF, Excel, CSV, and HTML pages.
- Creates a comparison-ready Excel workbook and CSV files.

## Recommended deployment options

### Option 1: Streamlit Community Cloud

Best for a simple proof of concept.

1. Create a GitHub repository.
2. Upload all files in this folder to the repository.
3. Go to Streamlit Community Cloud.
4. Create a new app from the GitHub repository.
5. Set the main file path to:

```text
app.py
```

6. Deploy.

The app will be available through a public Streamlit URL.

### Option 2: Render

Best for a more durable web app without managing servers.

1. Create a GitHub repository.
2. Upload this folder to the repository.
3. Create a new Render Web Service.
4. Choose the repository.
5. Render will detect `render.yaml` and `Dockerfile`.
6. Deploy.

### Option 3: Azure App Service

Best for a school district / enterprise environment.

Use the included `Dockerfile` to deploy as a containerized web app. Set the container port to `8501` or let the platform provide `$PORT`.

## Required district CSV format

```csv
district,state,start_url
Jeffco Public Schools,CO,https://www.jeffcopublicschools.org/
Denver Public Schools,CO,https://www.dpsk12.org/
```

## Important limitations

This tool should only be used for public information. Some district websites block automated access, use scanned PDFs, or publish salary data in formats that require manual review. For a production version, add district-specific source rules and a human review queue.

## Production upgrade ideas

- Login/password protection.
- Saved district lists.
- Data retention controls.
- Manual source review before extraction.
- Job title crosswalks.
- Benefits comparison fields.
- Board-ready Excel dashboards.
- Scheduled refreshes.
