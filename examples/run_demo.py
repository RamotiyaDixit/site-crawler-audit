"""Run the offline demo from a fresh checkout, no install needed:

    python examples/run_demo.py [--output-dir output/demo]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from optimity_scraper.cli import main  # noqa: E402

raise SystemExit(main(["demo", *sys.argv[1:]]))
