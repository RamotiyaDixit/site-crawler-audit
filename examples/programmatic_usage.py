"""Use the scraper as a library against the live site.

    pip install -e .
    python examples/programmatic_usage.py
"""

from optimity_scraper import CrawlConfig, build_report, crawl, save_all

config = CrawlConfig(
    base_url="https://optimitylogics.com",
    max_pages=25,  # keep test runs small
    max_depth=2,
    delay=1.5,  # be gentle with your own server
    output_dir="output/live",
)

pages = crawl(config)
paths = save_all(pages, config)

report = build_report(pages)
print(f"{report['ok_pages']}/{report['total_pages']} pages fetched")
print("Portfolio pages:", [p.url for p in pages if p.page_type == "portfolio"])
print("Contact details:", report["contact"])
print("Saved:", {k: str(v) for k, v in paths.items()})
