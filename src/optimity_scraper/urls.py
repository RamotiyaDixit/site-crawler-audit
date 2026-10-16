"""URL helpers: normalisation, same-site checks and page-type classification."""

from __future__ import annotations

import os
import re
from urllib.parse import parse_qsl, urlencode, urldefrag, urlparse, urlunparse

TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "mc_")

SKIP_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".bmp",
    ".zip", ".gz", ".rar", ".7z", ".mp3", ".mp4", ".avi", ".mov", ".webm",
    ".css", ".js", ".json", ".xml", ".woff", ".woff2", ".ttf", ".eot",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
}  # fmt: skip

INFO_PAGES = {"about-us", "contact-us", "career", "privacy-policy", "site-map", "schedule-a-call"}


def normalize_url(url: str) -> str:
    """Lower-case scheme/host, drop fragments, tracking params and trailing slashes."""
    url, _ = urldefrag(url.strip())
    parts = urlparse(url)
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"
    query = urlencode(
        [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if not k.lower().startswith(TRACKING_PREFIXES)
        ]
    )
    return urlunparse((parts.scheme.lower(), parts.netloc.lower(), path, parts.params, query, ""))


def _host(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def same_site(url: str, other: str) -> bool:
    """True when both URLs share a host (ignoring a leading ``www.``)."""
    return _host(url) == _host(other)


def is_http(url: str) -> bool:
    return urlparse(url).scheme in ("http", "https")


def is_crawlable(url: str) -> bool:
    """Skip binary/asset URLs; only HTML pages are worth parsing."""
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    return ext not in SKIP_EXTENSIONS


def classify_url(url: str) -> str:
    """Cheap, path-based page-type guess used for grouping in reports."""
    path = urlparse(url).path.strip("/").lower()
    if not path:
        return "home"
    parts = path.split("/")
    first = parts[0]
    if first in ("our-work", "portfolio", "case-studies"):
        return "portfolio" if len(parts) > 1 else "portfolio_index"
    if first == "blog":
        return "blog_post" if len(parts) > 1 else "blog_index"
    if first in INFO_PAGES:
        return "info"
    if re.search(r"(services?|solutions)$", first):
        return "service"
    return "other"
