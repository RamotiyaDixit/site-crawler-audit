# optimitylogics-scraper

[![CI](https://github.com/OWNER/optimitylogics-scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/optimitylogics-scraper/actions/workflows/ci.yml)

A polite, configurable crawler and data extractor for **optimitylogics.com**. It walks the site, pulls out structured data from every page, exports it as JSON, CSV and SQLite, and produces a Markdown SEO/content audit.

Built for first-party use: auditing your own site, feeding its content into other tools, and keeping an eye on broken links and missing metadata.

> Replace `OWNER` in the CI badge with your GitHub username after pushing.

## Features

- **Safe by default**: obeys `robots.txt`, waits 1 second between requests, retries on 429/5xx with backoff, identifies itself with a clear user agent.
- **Site-aware**: same-site only, normalises URLs (fragments, trailing slashes, `utm_*` tracking params), skips binary assets, picks up URLs from `sitemap.xml` when one exists.
- **Rich extraction** per page: title, meta description, canonical URL, Open Graph tags, H1/H2/H3 headings, word count, internal and external links, images with alt text, emails, phone numbers, JSON-LD blocks.
- **Page classification** from the URL path: `home`, `service`, `portfolio`, `portfolio_index`, `blog_index`, `blog_post`, `info`, `other`.
- **Three export formats**: `pages.json` (full fidelity), `pages.csv` (one flat row per page), `pages.sqlite` (tables `pages`, `links`, `images`).
- **Audit report** (`report.md`): failed or blocked pages, missing titles and meta descriptions, missing or multiple H1s, long titles, thin content, duplicate titles, images without alt text, contact details found.
- **Offline demo and tests**: a bundled sample site served from localhost, so everything runs without internet.

## Quick start

```bash
git clone https://github.com/OWNER/optimitylogics-scraper.git
cd optimitylogics-scraper
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Requires Python 3.9 or newer.

### Try the demo (no internet needed)

```bash
python examples/run_demo.py
```

This starts a local copy of a small sample site, crawls it end to end, writes all output files to `output/demo/`, and prints a summary. The sample site deliberately contains a broken link, a robots-blocked page, a page without a meta description, a page with two H1s and an image without alt text, so you can see each check fire.

### Crawl the real site

```bash
optimity-scraper crawl --url https://optimitylogics.com --max-pages 100 --delay 1.5
```

Output lands in `output/`:

| File | Contents |
| --- | --- |
| `pages.json` | Every field for every page, plus crawl metadata |
| `pages.csv` | One row per page: URL, status, type, title, meta description, H1, word count, link and image counts, contacts |
| `pages.sqlite` | Tables `pages`, `links` (source, target, internal flag) and `images` for ad-hoc SQL |
| `report.md` | The audit summary |

Example SQL on the SQLite file:

```sql
-- Pages that link to the most internal URLs
SELECT source, COUNT(*) AS n FROM links WHERE internal = 1 GROUP BY source ORDER BY n DESC LIMIT 10;

-- All portfolio pages and their titles
SELECT url, title FROM pages WHERE page_type = 'portfolio';
```

## Command reference

```
optimity-scraper [-v] crawl  [--url URL] [--max-pages N] [--max-depth N] [--delay S]
                             [--timeout S] [--output-dir DIR] [--formats json csv sqlite]
                             [--user-agent UA] [--ignore-robots]
optimity-scraper [-v] report [--input output/pages.json] [--output report.md]
optimity-scraper [-v] demo   [--output-dir output/demo]
```

You can also run `python -m optimity_scraper ...` without installing the console script.

| Option | Default | Meaning |
| --- | --- | --- |
| `--url` | `https://optimitylogics.com` | Start URL; the crawl stays on this host (a leading `www.` is ignored) |
| `--max-pages` | `100` | Stop after this many pages |
| `--max-depth` | `3` | Link depth from the start page (sitemap URLs count as depth 1) |
| `--delay` | `1.0` | Seconds between requests |
| `--timeout` | `15` | Per-request timeout in seconds |
| `--formats` | `json csv sqlite` | Which exports to write (`report.md` is always written) |
| `--ignore-robots` | off | Skip `robots.txt` checks. Only use this on a site you own |
| `-v` | off | Log every request |

## Use it as a library

```python
from optimity_scraper import CrawlConfig, build_report, crawl, save_all

config = CrawlConfig(base_url="https://optimitylogics.com", max_pages=25, delay=1.5, output_dir="output/live")
pages = crawl(config)
save_all(pages, config)

for page in pages:
    if page.page_type == "portfolio":
        print(page.title, page.url)

print(build_report(pages)["contact"])
```

See `examples/programmatic_usage.py` for a runnable version.

## Project layout

```
src/optimity_scraper/
    cli.py        command-line interface (crawl, report, demo)
    config.py     CrawlConfig defaults
    fetcher.py    HTTP session, retries, rate limiting, robots.txt
    crawler.py    breadth-first crawl, sitemap discovery
    parser.py     HTML -> Page extraction
    urls.py       normalisation, same-site check, page-type rules
    models.py     Page dataclass
    storage.py    JSON, CSV and SQLite export
    report.py     audit checks and Markdown rendering
    devserver.py  local server for the demo and tests
    demo.py       end-to-end offline demo
examples/         demo runner, library example, sample_site/ fixture
tests/            unit and integration tests
scripts/          push_to_github.sh
```

## Customising

- **Different page types**: edit `classify_url()` in `src/optimity_scraper/urls.py`.
- **Extra fields** (for example pricing, team members, case-study sections): add the field to `Page` in `models.py`, then fill it in `parse_page()` in `parser.py`. JSON picks it up automatically; add it to `storage.py` if you want it in CSV or SQLite.
- **Audit rules**: thresholds and checks live in `report.py`.

## Tests

```bash
pytest
```

The integration tests crawl the sample site through a real local HTTP server, so they cover robots.txt handling, 404s, URL de-duplication, max pages and depth limits, and all three exporters.

## Responsible use

This tool is meant for sites you own or have permission to crawl. Keep the default delay unless you know your hosting can take more, leave `robots.txt` handling on, and avoid running several crawls at once. If you point it at someone else's site, check their terms first.

## Publish to GitHub

With the [GitHub CLI](https://cli.github.com) installed:

```bash
scripts/push_to_github.sh                 # private repo named optimitylogics-scraper
scripts/push_to_github.sh my-repo public  # custom name, public
```

The script logs you in if needed, commits any changes, creates the repository and pushes `main`. Manual alternative:

```bash
git init -b main && git add -A && git commit -m "Initial commit"
gh repo create optimitylogics-scraper --private --source=. --remote=origin --push
```

## License

MIT. See [LICENSE](LICENSE).
