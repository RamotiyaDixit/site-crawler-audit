import csv
import sqlite3

from optimity_scraper import CrawlConfig, build_report, render_markdown, save_all
from optimity_scraper.storage import load_pages


def test_save_all_writes_every_format(crawled_pages, tmp_path):
    config = CrawlConfig(output_dir=str(tmp_path))
    written = save_all(crawled_pages, config)
    assert {"json", "csv", "sqlite", "report"} == set(written)
    assert all(path.is_file() for path in written.values())


def test_json_round_trip(crawled_pages, tmp_path):
    written = save_all(crawled_pages, CrawlConfig(output_dir=str(tmp_path)))
    loaded = load_pages(written["json"])
    assert [p.to_dict() for p in loaded] == [p.to_dict() for p in crawled_pages]


def test_csv_rows_match_pages(crawled_pages, tmp_path):
    written = save_all(crawled_pages, CrawlConfig(output_dir=str(tmp_path)))
    with written["csv"].open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(crawled_pages)
    assert "title" in rows[0] and "word_count" in rows[0]


def test_sqlite_tables(crawled_pages, tmp_path):
    written = save_all(crawled_pages, CrawlConfig(output_dir=str(tmp_path)))
    con = sqlite3.connect(written["sqlite"])
    try:
        assert con.execute("SELECT COUNT(*) FROM pages").fetchone()[0] == len(crawled_pages)
        assert con.execute("SELECT COUNT(*) FROM links WHERE internal = 1").fetchone()[0] > 0
        assert con.execute("SELECT COUNT(*) FROM images").fetchone()[0] == 2
    finally:
        con.close()


def test_formats_can_be_limited(crawled_pages, tmp_path):
    written = save_all(crawled_pages, CrawlConfig(output_dir=str(tmp_path), formats=("json",)))
    assert set(written) == {"json", "report"}


def test_report_flags_known_issues(crawled_pages, sample_site_url):
    report = build_report(crawled_pages)
    seo = report["seo"]
    assert f"{sample_site_url}/about-us" in seo["missing_meta_description"]
    assert f"{sample_site_url}/about-us" in seo["multiple_h1"]
    assert seo["images_missing_alt"] == 1
    failed = {f["url"].replace(sample_site_url, ""): f["error"] for f in report["failed_pages"]}
    assert failed == {"/old-page": "HTTP 404", "/private/internal": "blocked by robots.txt"}
    assert "hello@example.com" in report["contact"]["emails"]


def test_markdown_rendering(crawled_pages):
    text = render_markdown(build_report(crawled_pages))
    assert text.startswith("# Site audit report")
    assert "## SEO checks" in text
    assert "hello@example.com" in text
