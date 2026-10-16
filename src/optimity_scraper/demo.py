"""End-to-end demo: serve the bundled sample site locally, crawl it, export, report."""

from __future__ import annotations

from pathlib import Path

from .config import CrawlConfig
from .crawler import crawl
from .devserver import serve_directory
from .report import build_report
from .storage import save_all

SAMPLE_SITE = Path(__file__).resolve().parents[2] / "examples" / "sample_site"


def run_demo(output_dir: str = "output/demo") -> int:
    if not SAMPLE_SITE.is_dir():
        print(f"error: sample site not found at {SAMPLE_SITE} (run the demo from a source checkout)")
        return 1

    server, base_url = serve_directory(SAMPLE_SITE)
    print(f"Serving sample site at {base_url}\n")
    config = CrawlConfig(base_url=base_url, delay=0.0, max_pages=50, output_dir=output_dir)
    try:
        pages = crawl(config, on_page=lambda p: print(f"  {p.status_code or '---'}  {p.page_type:<16} {p.url}  {p.error}".rstrip()))
    finally:
        server.shutdown()
        server.server_close()

    written = save_all(pages, config)
    report = build_report(pages)
    seo = report["seo"]
    print(f"\nCrawled {report['total_pages']} pages: {report['ok_pages']} OK, {len(report['failed_pages'])} failed/blocked")
    print(f"Missing meta description: {len(seo['missing_meta_description'])}")
    print(f"Pages with more than one H1: {len(seo['multiple_h1'])}")
    print(f"Images without alt text: {seo['images_missing_alt']}")
    print(f"Contact details: {', '.join(report['contact']['emails'] + report['contact']['phones']) or 'none'}")
    print("\nFiles written:")
    for kind, path in written.items():
        print(f"  {kind:<7} {path}")
    return 0
