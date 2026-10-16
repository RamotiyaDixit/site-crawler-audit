"""Tiny local web server used by the demo and the test-suite.

Serves a directory over HTTP and maps extensionless URLs (``/about-us``) to
``about-us.html`` so the sample site behaves like the real one.
"""

from __future__ import annotations

import functools
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Tuple


class _Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        resolved = super().translate_path(path)
        if not os.path.splitext(resolved)[1] and os.path.exists(resolved + ".html"):
            return resolved + ".html"
        return resolved

    def log_message(self, format, *args):  # noqa: A002 - keep the demo output clean
        pass


def serve_directory(directory: Path, host: str = "127.0.0.1", port: int = 0) -> Tuple[ThreadingHTTPServer, str]:
    """Start serving ``directory`` in a background thread; returns (server, base_url)."""
    handler = functools.partial(_Handler, directory=str(directory))
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://{host}:{server.server_address[1]}"
