"""Site audit built from crawled pages."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List

from .models import Page

TITLE_MAX = 60
META_MAX = 160
THIN_WORDS = 150


def build_report(pages: List[Page], thin_words: int = THIN_WORDS) -> Dict[str, Any]:
    ok = [p for p in pages if p.ok]
    failed = [p for p in pages if not p.ok]

    by_title = defaultdict(list)
    for p in ok:
        if p.title:
            by_title[p.title].append(p.url)

    emails = sorted({e for p in ok for e in p.emails})
    phones = sorted({ph for p in ok for ph in p.phones})

    return {
        "total_pages": len(pages),
        "ok_pages": len(ok),
        "failed_pages": [{"url": p.url, "status_code": p.status_code, "error": p.error} for p in failed],
        "pages_by_type": dict(Counter(p.page_type for p in pages).most_common()),
        "seo": {
            "missing_title": [p.url for p in ok if not p.title],
            "missing_meta_description": [p.url for p in ok if not p.meta_description],
            "missing_h1": [p.url for p in ok if not p.headings.get("h1")],
            "multiple_h1": [p.url for p in ok if len(p.headings.get("h1", [])) > 1],
            "title_too_long": [p.url for p in ok if len(p.title) > TITLE_MAX],
            "meta_description_too_long": [p.url for p in ok if len(p.meta_description) > META_MAX],
            "thin_content": [p.url for p in ok if p.word_count < thin_words],
            "duplicate_titles": {t: urls for t, urls in by_title.items() if len(urls) > 1},
            "images_missing_alt": sum(1 for p in ok for i in p.images if not i["alt"]),
        },
        "contact": {"emails": emails, "phones": phones},
    }


def _section(title: str, urls: List[str], limit: int = 10) -> List[str]:
    lines = [f"### {title} ({len(urls)})"]
    if not urls:
        lines.append("None.")
    else:
        lines += [f"- {u}" for u in urls[:limit]]
        if len(urls) > limit:
            lines.append(f"- ...and {len(urls) - limit} more")
    return lines + [""]


def render_markdown(report: Dict[str, Any]) -> str:
    seo = report["seo"]
    lines = [
        "# Site audit report",
        "",
        f"- Pages crawled: **{report['total_pages']}**",
        f"- Fetched OK: **{report['ok_pages']}**",
        f"- Failed or blocked: **{len(report['failed_pages'])}**",
        "",
        "## Pages by type",
        "",
    ]
    lines += [f"- {kind}: {count}" for kind, count in report["pages_by_type"].items()]
    lines += ["", "## Failed or blocked pages", ""]
    if report["failed_pages"]:
        lines += [f"- {f['url']} ({f['error'] or f['status_code']})" for f in report["failed_pages"]]
    else:
        lines.append("None.")
    lines += ["", "## SEO checks", ""]
    lines += _section("Missing title", seo["missing_title"])
    lines += _section("Missing meta description", seo["missing_meta_description"])
    lines += _section("Missing H1", seo["missing_h1"])
    lines += _section("More than one H1", seo["multiple_h1"])
    lines += _section(f"Title longer than {TITLE_MAX} characters", seo["title_too_long"])
    lines += _section(f"Meta description longer than {META_MAX} characters", seo["meta_description_too_long"])
    lines += _section(f"Thin content (under {THIN_WORDS} words)", seo["thin_content"])
    lines += [f"### Duplicate titles ({len(seo['duplicate_titles'])})"]
    if seo["duplicate_titles"]:
        for title, urls in seo["duplicate_titles"].items():
            lines.append(f"- \"{title}\" on {len(urls)} pages")
    else:
        lines.append("None.")
    lines += ["", f"### Images without alt text: {seo['images_missing_alt']}", ""]
    lines += ["## Contact details found", ""]
    lines += [f"- Email: {e}" for e in report["contact"]["emails"]] or ["- No emails found"]
    lines += [f"- Phone: {p}" for p in report["contact"]["phones"]] or ["- No phone numbers found"]
    return "\n".join(lines) + "\n"
