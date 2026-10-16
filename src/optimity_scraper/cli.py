"""Command-line interface: ``optimity-scraper crawl | report | demo``."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .config import DEFAULT_BASE_URL, DEFAULT_USER_AGENT, CrawlConfig
from .crawler import crawl
from .report import build_report, render_markdown
from .storage import load_pages, save_all


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="optimity-scraper",
        description="Crawl optimitylogics.com and export structured page data plus an SEO audit.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="log every request")
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("crawl", help="crawl a site and write JSON/CSV/SQLite + report.md")
    c.add_argument("--url", default=DEFAULT_BASE_URL, help="start URL (default: %(default)s)")
    c.add_argument("--max-pages", type=int, default=100)
    c.add_argument("--max-depth", type=int, default=3)
    c.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    c.add_argument("--timeout", type=float, default=15.0)
    c.add_argument("--output-dir", default="output")
    c.add_argument("--formats", nargs="+", default=["json", "csv", "sqlite"], choices=["json", "csv", "sqlite"])
    c.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    c.add_argument("--ignore-robots", action="store_true", help="do not obey robots.txt (own sites only)")

    r = sub.add_parser("report", help="rebuild the Markdown audit from a saved pages.json")
    r.add_argument("--input", default="output/pages.json")
    r.add_argument("--output", help="write to this file instead of stdout")

    d = sub.add_parser("demo", help="run the full pipeline against the bundled sample site (no internet needed)")
    d.add_argument("--output-dir", default="output/demo")
    return parser


def _cmd_crawl(args: argparse.Namespace) -> int:
    config = CrawlConfig(
        base_url=args.url,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        delay=args.delay,
        timeout=args.timeout,
        user_agent=args.user_agent,
        respect_robots=not args.ignore_robots,
        output_dir=args.output_dir,
        formats=tuple(args.formats),
    )
    pages = crawl(config, on_page=lambda p: print(f"  {p.status_code or '---'}  {p.url}  {p.error}".rstrip()))
    written = save_all(pages, config)
    ok = sum(1 for p in pages if p.ok)
    print(f"\nCrawled {len(pages)} pages ({ok} OK).")
    for kind, path in written.items():
        print(f"  {kind:<7} {path}")
    return 0 if pages else 1


def _cmd_report(args: argparse.Namespace) -> int:
    path = Path(args.input)
    if not path.is_file():
        print(f"error: {path} not found. Run `optimity-scraper crawl` first.", file=sys.stderr)
        return 1
    text = render_markdown(build_report(load_pages(path)))
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(text)
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    from .demo import run_demo

    return run_demo(args.output_dir)


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    handlers = {"crawl": _cmd_crawl, "report": _cmd_report, "demo": _cmd_demo}
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
