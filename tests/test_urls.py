import pytest

from optimity_scraper.urls import classify_url, is_crawlable, normalize_url, same_site


def test_normalize_strips_fragment_trailing_slash_and_tracking():
    assert normalize_url("HTTPS://OptimityLogics.com/Contact-Us/?utm_source=x&a=1#top") == (
        "https://optimitylogics.com/Contact-Us?a=1"
    )


def test_normalize_keeps_root_slash():
    assert normalize_url("https://optimitylogics.com") == "https://optimitylogics.com/"


def test_same_site_ignores_www():
    assert same_site("https://www.optimitylogics.com/a", "https://optimitylogics.com/b")
    assert not same_site("https://example.com", "https://optimitylogics.com")


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/", "home"),
        ("/our-work", "portfolio_index"),
        ("/our-work/hts", "portfolio"),
        ("/blog", "blog_index"),
        ("/blog/some-post", "blog_post"),
        ("/web-development-services", "service"),
        ("/cloud-computing-solutions", "service"),
        ("/software-product-development-service", "service"),
        ("/contact-us", "info"),
        ("/something-else", "other"),
    ],
)
def test_classify_url(path, expected):
    assert classify_url("https://optimitylogics.com" + path) == expected


def test_is_crawlable():
    assert is_crawlable("https://x.com/about-us")
    assert not is_crawlable("https://x.com/brochure.pdf")
    assert not is_crawlable("https://x.com/logo.PNG")
