"""Exporters: JSON, CSV and SQLite."""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .config import CrawlConfig
from .models import Page
from .report import build_report, render_markdown

CSV_COLUMNS = [
    "url", "final_url", "status_code", "error", "page_type", "depth", "title",
    "meta_description", "canonical", "h1", "h2_count", "word_count",
    "internal_links", "external_links", "emails", "phones", "images", "fetched_at",
]  # fmt: skip


def save_json(pages: List[Page], path: Path, base_url: str = "") -> Path:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "base_url": base_url,
        "page_count": len(pages),
        "pages": [p.to_dict() for p in pages],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_pages(path: Path) -> List[Page]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Page.from_dict(item) for item in data["pages"]]


def save_csv(pages: List[Page], path: Path) -> Path:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for p in pages:
            writer.writerow(
                {
                    "url": p.url,
                    "final_url": p.final_url,
                    "status_code": p.status_code,
                    "error": p.error,
                    "page_type": p.page_type,
                    "depth": p.depth,
                    "title": p.title,
                    "meta_description": p.meta_description,
                    "canonical": p.canonical,
                    "h1": " | ".join(p.headings.get("h1", [])),
                    "h2_count": len(p.headings.get("h2", [])),
                    "word_count": p.word_count,
                    "internal_links": len(p.internal_links),
                    "external_links": len(p.external_links),
                    "emails": " | ".join(p.emails),
                    "phones": " | ".join(p.phones),
                    "images": len(p.images),
                    "fetched_at": p.fetched_at,
                }
            )
    return path


def save_sqlite(pages: List[Page], path: Path) -> Path:
    con = sqlite3.connect(path)
    try:
        con.executescript(
            """
            DROP TABLE IF EXISTS pages;
            DROP TABLE IF EXISTS links;
            DROP TABLE IF EXISTS images;
            CREATE TABLE pages (
                url TEXT PRIMARY KEY, final_url TEXT, status_code INTEGER, error TEXT,
                page_type TEXT, depth INTEGER, title TEXT, meta_description TEXT,
                canonical TEXT, h1 TEXT, word_count INTEGER, emails TEXT, phones TEXT,
                og TEXT, headings TEXT, json_ld TEXT, fetched_at TEXT
            );
            CREATE TABLE links (
                source TEXT, target TEXT, internal INTEGER,
                PRIMARY KEY (source, target)
            );
            CREATE TABLE images (page_url TEXT, src TEXT, alt TEXT);
            """
        )
        for p in pages:
            con.execute(
                "INSERT OR REPLACE INTO pages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    p.url, p.final_url, p.status_code, p.error, p.page_type, p.depth,
                    p.title, p.meta_description, p.canonical,
                    " | ".join(p.headings.get("h1", [])), p.word_count,
                    json.dumps(p.emails), json.dumps(p.phones), json.dumps(p.og),
                    json.dumps(p.headings), json.dumps(p.json_ld), p.fetched_at,
                ),
            )  # fmt: skip
            con.executemany(
                "INSERT OR IGNORE INTO links VALUES (?,?,?)",
                [(p.url, t, 1) for t in p.internal_links] + [(p.url, t, 0) for t in p.external_links],
            )
            con.executemany(
                "INSERT INTO images VALUES (?,?,?)",
                [(p.url, i["src"], i["alt"]) for i in p.images],
            )
        con.commit()
    finally:
        con.close()
    return path


def save_all(pages: List[Page], config: CrawlConfig) -> Dict[str, Path]:
    """Write every requested format plus a Markdown audit report."""
    out = Path(config.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: Dict[str, Path] = {}
    if "json" in config.formats:
        written["json"] = save_json(pages, out / "pages.json", config.base_url)
    if "csv" in config.formats:
        written["csv"] = save_csv(pages, out / "pages.csv")
    if "sqlite" in config.formats:
        written["sqlite"] = save_sqlite(pages, out / "pages.sqlite")
    report_path = out / "report.md"
    report_path.write_text(render_markdown(build_report(pages)), encoding="utf-8")
    written["report"] = report_path
    return written
