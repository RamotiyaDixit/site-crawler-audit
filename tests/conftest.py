from pathlib import Path

import pytest

from optimity_scraper import CrawlConfig, crawl
from optimity_scraper.devserver import serve_directory

SAMPLE_SITE = Path(__file__).resolve().parents[1] / "examples" / "sample_site"


@pytest.fixture(scope="session")
def sample_site_url():
    server, base_url = serve_directory(SAMPLE_SITE)
    yield base_url
    server.shutdown()
    server.server_close()


@pytest.fixture(scope="session")
def crawled_pages(sample_site_url):
    return crawl(CrawlConfig(base_url=sample_site_url, delay=0.0, max_pages=50))
