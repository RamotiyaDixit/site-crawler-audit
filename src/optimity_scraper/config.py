from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

DEFAULT_BASE_URL = "https://optimitylogics.com"
DEFAULT_USER_AGENT = "OptimityScraper/1.0 (+https://optimitylogics.com; first-party site audit)"


@dataclass
class CrawlConfig:
    """All knobs for a crawl. Defaults are deliberately conservative."""

    base_url: str = DEFAULT_BASE_URL
    max_pages: int = 100
    max_depth: int = 3
    delay: float = 1.0  # seconds between requests
    timeout: float = 15.0  # seconds per request
    retries: int = 3  # retries on 429/5xx and connection errors
    user_agent: str = DEFAULT_USER_AGENT
    respect_robots: bool = True
    output_dir: str = "output"
    formats: Tuple[str, ...] = ("json", "csv", "sqlite")
