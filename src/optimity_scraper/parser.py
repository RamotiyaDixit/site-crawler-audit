"""HTML -> Page extraction."""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from .models import Page
from .urls import classify_url, is_http, normalize_url, same_site

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+\d{1,3}[\s-]?\(?\d[\d\s().-]{6,}\d")
WS_RE = re.compile(r"\s+")


def _clean(text: str) -> str:
    return WS_RE.sub(" ", text).strip()


def _unique(items) -> List[str]:
    return list(dict.fromkeys(i for i in items if i))


def _unique_phones(phones: List[str]) -> List[str]:
    """Dedupe by digits, keeping the best-formatted (longest) spelling of each number."""
    best: Dict[str, str] = {}
    for phone in phones:
        key = re.sub(r"\D", "", phone)
        if key and len(phone) > len(best.get(key, "")):
            best[key] = phone
    return list(best.values())


def _meta(soup: BeautifulSoup, name: str) -> str:
    tag = soup.find("meta", attrs={"name": re.compile(f"^{name}$", re.I)})
    return _clean(tag.get("content", "")) if tag else ""


def parse_page(
    html: str,
    url: str,
    status_code: int = 200,
    fetched_at: str = "",
    page_type: Optional[str] = None,
    depth: int = 0,
) -> Page:
    soup = BeautifulSoup(html, "html.parser")

    title = _clean(soup.title.get_text(" ")) if soup.title else ""
    canonical_tag = soup.find("link", rel="canonical")
    canonical = urljoin(url, canonical_tag["href"]) if canonical_tag and canonical_tag.get("href") else ""

    og: Dict[str, str] = {}
    for tag in soup.find_all("meta", attrs={"property": re.compile(r"^og:", re.I)}):
        if tag.get("content"):
            og[tag["property"].lower()] = _clean(tag["content"])

    json_ld = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            json_ld.append(json.loads(script.string or ""))
        except (ValueError, TypeError):
            continue

    headings = {
        level: [t for t in (_clean(h.get_text(" ")) for h in soup.find_all(level)) if t]
        for level in ("h1", "h2", "h3")
    }

    emails: List[str] = []
    phones: List[str] = []
    internal: List[str] = []
    external: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        lowered = href.lower()
        if lowered.startswith("mailto:"):
            emails.append(unquote(href[7:].split("?")[0]).strip().lower())
            continue
        if lowered.startswith("tel:"):
            phones.append(_clean(unquote(href[4:])))
            continue
        if not href or href.startswith("#") or lowered.startswith("javascript:"):
            continue
        absolute = normalize_url(urljoin(url, href))
        if not is_http(absolute):
            continue
        (internal if same_site(absolute, url) else external).append(absolute)

    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src:
            images.append({"src": urljoin(url, src), "alt": _clean(img.get("alt", ""))})

    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    text = _clean(soup.get_text(" "))
    emails += [e.lower() for e in EMAIL_RE.findall(text)]
    phones += [_clean(p) for p in PHONE_RE.findall(text)]

    return Page(
        url=url,
        status_code=status_code,
        fetched_at=fetched_at,
        page_type=page_type or classify_url(url),
        depth=depth,
        title=title,
        meta_description=_meta(soup, "description"),
        canonical=canonical,
        og=og,
        headings=headings,
        word_count=len(text.split()),
        internal_links=_unique(internal),
        external_links=_unique(external),
        emails=_unique(emails),
        phones=_unique_phones(phones),
        images=images,
        json_ld=json_ld,
    )
