from dataclasses import dataclass
from pathlib import Path

USER_AGENT = "CompensationResearchBot/0.1 (+public compensation research; contact: your-email@example.com)"
REQUEST_TIMEOUT = 25
REQUEST_DELAY_SECONDS = 1.0
MAX_LINKS_PER_DISTRICT = 75
MAX_DOWNLOAD_MB = 40

COMPENSATION_KEYWORDS = [
    "salary", "salaries", "compensation", "pay schedule", "pay plan",
    "salary schedule", "wage", "wages", "classification", "classifications",
    "licensed salary", "teacher salary", "administrator salary", "admin salary",
    "support staff", "classified", "benefits", "hr", "human resources",
    "collective bargaining", "agreement", "master agreement", "negotiated agreement"
]

FILE_EXTENSIONS = (".pdf", ".xlsx", ".xls", ".csv")

@dataclass
class District:
    district: str
    state: str
    start_url: str

@dataclass
class SourceRecord:
    district: str
    state: str
    source_url: str
    local_path: str | None
    source_type: str
    status: str
    note: str = ""


def ensure_dirs(output_dir: str | Path) -> dict[str, Path]:
    base = Path(output_dir)
    downloads = base / "downloads"
    tables = base / "tables"
    base.mkdir(parents=True, exist_ok=True)
    downloads.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    return {"base": base, "downloads": downloads, "tables": tables}
