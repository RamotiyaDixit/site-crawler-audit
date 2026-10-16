from optimity_scraper import CrawlConfig, crawl
from optimity_scraper.crawler import discover_sitemap_urls


def _by_path(pages, base):
    return {p.url.replace(base, "") or "/": p for p in pages}


def test_crawl_visits_expected_pages(crawled_pages, sample_site_url):
    paths = set(_by_path(crawled_pages, sample_site_url))
    assert {"/", "/about-us", "/contact-us", "/web-development-services", "/our-work", "/our-work/hts"} <= paths


def test_robots_disallowed_page_is_never_fetched(crawled_pages, sample_site_url):
    page = _by_path(crawled_pages, sample_site_url)["/private/internal"]
    assert page.error == "blocked by robots.txt"
    assert page.status_code == 0


def test_broken_link_is_recorded(crawled_pages, sample_site_url):
    page = _by_path(crawled_pages, sample_site_url)["/old-page"]
    assert page.status_code == 404
    assert page.error == "HTTP 404"


def test_tracking_params_and_fragments_do_not_create_duplicates(crawled_pages):
    urls = [p.url for p in crawled_pages]
    assert len(urls) == len(set(urls))
    assert not any("utm_" in u or "#" in u for u in urls)


def test_page_types(crawled_pages, sample_site_url):
    pages = _by_path(crawled_pages, sample_site_url)
    assert pages["/"].page_type == "home"
    assert pages["/web-development-services"].page_type == "service"
    assert pages["/our-work/hts"].page_type == "portfolio"
    assert pages["/contact-us"].page_type == "info"


def test_contact_extraction(crawled_pages, sample_site_url):
    contact = _by_path(crawled_pages, sample_site_url)["/contact-us"]
    assert set(contact.emails) == {"hello@example.com", "sales@example.com"}
    assert contact.phones == ["+91 98765 43210"]


def test_max_pages_is_respected(sample_site_url):
    pages = crawl(CrawlConfig(base_url=sample_site_url, delay=0.0, max_pages=3))
    assert len(pages) == 3


def test_max_depth_zero_only_fetches_start_page(sample_site_url):
    pages = crawl(CrawlConfig(base_url=sample_site_url, delay=0.0, max_depth=0))
    assert len(pages) == 1


def test_ignore_robots_fetches_blocked_page(sample_site_url):
    pages = crawl(CrawlConfig(base_url=sample_site_url, delay=0.0, respect_robots=False))
    private = _by_path(pages, sample_site_url)["/private/internal"]
    assert private.status_code == 200


class _FakeResult:
    def __init__(self, text, status_code=200):
        self.text, self.status_code = text, status_code


class _FakeFetcher:
    """Serves sitemap documents from a dict, no network involved."""

    def __init__(self, docs, advertised=()):
        self.docs, self.advertised = docs, list(advertised)

    def sitemap_urls(self):
        return self.advertised

    def fetch(self, url):
        return _FakeResult(self.docs[url]) if url in self.docs else _FakeResult("", 404)


def test_sitemap_index_is_followed():
    docs = {
        "https://s.test/sitemap.xml": "<sitemapindex><sitemap><loc>https://s.test/pages.xml</loc></sitemap></sitemapindex>",
        "https://s.test/pages.xml": "<urlset><url><loc>https://s.test/a</loc></url><url><loc>https://s.test/b?x=1&amp;y=2</loc></url></urlset>",
    }
    urls = discover_sitemap_urls(_FakeFetcher(docs), CrawlConfig(base_url="https://s.test"))
    assert urls == ["https://s.test/a", "https://s.test/b?x=1&y=2"]


def test_missing_sitemap_returns_empty():
    assert discover_sitemap_urls(_FakeFetcher({}), CrawlConfig(base_url="https://s.test")) == []
