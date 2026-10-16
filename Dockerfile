FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first so this layer is cached when only the source changes.
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY pyproject.toml README.md ./
COPY src ./src
COPY examples ./examples
RUN pip install --no-deps -e .

# Run as an unprivileged user; crawl results are written to /app/output.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/output \
    && chown appuser:appuser /app/output
USER appuser

VOLUME ["/app/output"]

ENTRYPOINT ["optimity-scraper"]
CMD ["--help"]
