"""Breadth-first crawler restricted to a single site."""

from __future__ import annotations

import html
import logging
import re
from collections import deque
from datetime import datetime, timezone
from typing import Callable, List, Optional
from urllib.parse import urljoin

from .config import CrawlConfig
from .fetcher import Fetcher
from .models import Page
from .parser import parse_page
from .urls import classify_url, is_crawlable, normalize_url, same_site

log = logging.getLogger(__name__)

LOC_RE = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.I | re.S)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def discover_sitemap_urls(fetcher: Fetcher, config: CrawlConfig, max_urls: int = 1000) -> List[str]:
    """Collect page URLs from sitemap.xml (or the sitemaps listed in robots.txt)."""
    pending = [(u, 0) for u in (fetcher.sitemap_urls() or [urljoin(config.base_url, "/sitemap.xml")])]
    seen_maps = set()
    found: List[str] = []
    while pending and len(found) < max_urls:
        sitemap, level = pending.pop(0)
        if sitemap in seen_maps:
            continue
        seen_maps.add(sitemap)
        result = fetcher.fetch(sitemap)
        if result.status_code != 200 or not result.text:
            continue
        locs = [html.unescape(loc) for loc in LOC_RE.findall(result.text)]
        if "<sitemapindex" in result.text.lower() and level < 2:
            pending.extend((loc, level + 1) for loc in locs)
        else:
            found.extend(locs)
    return found[:max_urls]


def fetch_page(fetcher: Fetcher, url: str, depth: int = 0) -> Page:
    fetched_at = _now()
    page_type = classify_url(url)
    result = fetcher.fetch(url)

    def failed(error: str) -> Page:
        return Page(
            url=url,
            status_code=result.status_code,
            fetched_at=fetched_at,
            page_type=page_type,
            depth=depth,
            error=error,
        )

    if result.error:
        return failed(result.error)
    if result.status_code >= 400:
        return failed(f"HTTP {result.status_code}")
    content_type = result.content_type.lower()
    if "html" not in content_type:
        return failed(f"non-HTML content ({content_type or 'unknown'})")

    base = result.final_url or url
    page = parse_page(result.text, base, result.status_code, fetched_at, page_type, depth)
    page.url = url
    final = normalize_url(base)
    page.final_url = final if final != url else ""
    return page


def crawl(
    config: CrawlConfig,
    fetcher: Optional[Fetcher] = None,
    on_page: Optional[Callable[[Page], None]] = None,
) -> List[Page]:
    """Crawl ``config.base_url`` breadth-first and return every visited page."""
    fetcher = fetcher or Fetcher(config)
    start = normalize_url(config.base_url)
    queue = deque([(start, 0)])
    seen = {start}

    for loc in discover_sitemap_urls(fetcher, config):
        url = normalize_url(loc)
        if url not in seen and same_site(url, start) and is_crawlable(url):
            seen.add(url)
            queue.append((url, 1))

    pages: List[Page] = []
    while queue and len(pages) < config.max_pages:
        url, depth = queue.popleft()
        page = fetch_page(fetcher, url, depth)
        pages.append(page)
        log.info("[%d] %s -> %s", len(pages), url, page.error or page.status_code)
        if on_page:
            on_page(page)
        if page.ok and depth < config.max_depth:
            for link in page.internal_links:
                if link not in seen and is_crawlable(link):
                    seen.add(link)
                    queue.append((link, depth + 1))
    return pages
