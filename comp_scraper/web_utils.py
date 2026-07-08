from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    COMPENSATION_KEYWORDS,
    FILE_EXTENSIONS,
    MAX_DOWNLOAD_MB,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT,
    USER_AGENT,
)


def get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def is_probably_compensation_link(text: str, href: str) -> bool:
    haystack = f"{text or ''} {href or ''}".lower()
    return any(keyword in haystack for keyword in COMPENSATION_KEYWORDS)


def is_supported_file(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(FILE_EXTENSIONS)


def same_domain(url_a: str, url_b: str) -> bool:
    return urlparse(url_a).netloc.replace("www.", "") == urlparse(url_b).netloc.replace("www.", "")


def fetch_html(session: requests.Session, url: str) -> str | None:
    try:
        time.sleep(REQUEST_DELAY_SECONDS)
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        content_type = resp.headers.get("content-type", "").lower()
        if resp.ok and "html" in content_type:
            return resp.text
    except requests.RequestException:
        return None
    return None


def discover_links(session: requests.Session, start_url: str, max_links: int) -> list[str]:
    """Discover likely compensation links from the starting page and one shallow level."""
    seen: set[str] = set()
    candidates: list[str] = []

    def scan_page(url: str, shallow: bool = False) -> None:
        html = fetch_html(session, url)
        if not html:
            return
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            text = " ".join(a.get_text(" ").split())
            if href in seen:
                continue
            if not same_domain(start_url, href):
                # Allow document/CDN links if the link itself looks like a salary doc.
                if not is_supported_file(href):
                    continue
            if is_probably_compensation_link(text, href) or is_supported_file(href):
                seen.add(href)
                candidates.append(href)
            elif not shallow and any(k in f"{text} {href}".lower() for k in ["human resources", "hr", "finance", "transparency"]):
                seen.add(href)
                candidates.append(href)

    scan_page(start_url)

    # One shallow pass through promising internal pages.
    for url in list(candidates)[:20]:
        if len(candidates) >= max_links:
            break
        if not is_supported_file(url) and same_domain(start_url, url):
            scan_page(url, shallow=True)

    return candidates[:max_links]


def safe_filename(url: str, district: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name or "document"
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    prefix = re.sub(r"[^A-Za-z0-9._-]+", "_", district)[:40]
    if "." not in name:
        name += ".html"
    return f"{prefix}_{digest}_{name}"


def download_file(session: requests.Session, url: str, district: str, download_dir: Path) -> Path | None:
    try:
        time.sleep(REQUEST_DELAY_SECONDS)
        with session.get(url, timeout=REQUEST_TIMEOUT, stream=True) as resp:
            if not resp.ok:
                return None
            size = int(resp.headers.get("content-length", 0) or 0)
            if size > MAX_DOWNLOAD_MB * 1024 * 1024:
                return None
            path = download_dir / safe_filename(url, district)
            with path.open("wb") as f:
                downloaded = 0
                for chunk in resp.iter_content(chunk_size=1024 * 128):
                    if not chunk:
                        continue
                    downloaded += len(chunk)
                    if downloaded > MAX_DOWNLOAD_MB * 1024 * 1024:
                        return None
                    f.write(chunk)
            return path
    except requests.RequestException:
        return None
