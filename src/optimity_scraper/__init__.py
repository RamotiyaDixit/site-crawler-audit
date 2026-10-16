"""optimity_scraper: a polite crawler and data extractor for optimitylogics.com."""

from .config import CrawlConfig
from .crawler import crawl
from .models import Page
from .report import build_report, render_markdown
from .storage import save_all

__all__ = ["CrawlConfig", "Page", "build_report", "crawl", "render_markdown", "save_all"]
__version__ = "1.0.0"
