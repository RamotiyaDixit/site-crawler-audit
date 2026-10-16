"""HTTP layer: retries, rate limiting and robots.txt handling."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import CrawlConfig

log = logging.getLogger(__name__)


@dataclass
class FetchResult:
    url: str
    status_code: int = 0
    text: str = ""
    content_type: str = ""
    final_url: str = ""
    error: str = ""


class Fetcher:
    def __init__(self, config: CrawlConfig, session: Optional[requests.Session] = None):
        self.config = config
        self.session = session or self._build_session()
        self._last_request = 0.0
        self._robots: Optional[RobotFileParser] = None

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": self.config.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        retry = Retry(
            total=self.config.retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _throttle(self) -> None:
        wait = self.config.delay - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def _load_robots(self) -> RobotFileParser:
        if self._robots is not None:
            return self._robots
        parser = RobotFileParser()
        robots_url = urljoin(self.config.base_url, "/robots.txt")
        lines: List[str] = []
        try:
            self._throttle()
            resp = self.session.get(robots_url, timeout=self.config.timeout)
            if resp.status_code == 200:
                lines = resp.text.splitlines()
            else:
                log.info("robots.txt returned HTTP %s; treating as allow-all", resp.status_code)
        except requests.RequestException as exc:
            log.warning("Could not fetch robots.txt (%s); treating as allow-all", exc)
        parser.parse(lines)
        parser.modified()  # without this, can_fetch() refuses everything
        self._robots = parser
        return parser

    def allowed(self, url: str) -> bool:
        if not self.config.respect_robots:
            return True
        return self._load_robots().can_fetch(self.config.user_agent, url)

    def sitemap_urls(self) -> List[str]:
        """Sitemap URLs advertised in robots.txt (may be empty)."""
        if not self.config.respect_robots:
            return []
        return list(self._load_robots().site_maps() or [])

    def fetch(self, url: str) -> FetchResult:
        if not self.allowed(url):
            return FetchResult(url=url, error="blocked by robots.txt")
        self._throttle()
        try:
            resp = self.session.get(url, timeout=self.config.timeout)
        except requests.RequestException as exc:
            return FetchResult(url=url, error=f"{type(exc).__name__}: {exc}")
        return FetchResult(
            url=url,
            status_code=resp.status_code,
            text=resp.text,
            content_type=resp.headers.get("Content-Type", ""),
            final_url=resp.url,
        )
