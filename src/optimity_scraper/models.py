from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any, Dict, List


@dataclass
class Page:
    """Everything extracted from one crawled URL."""

    url: str
    status_code: int = 0
    fetched_at: str = ""
    page_type: str = "other"
    depth: int = 0
    final_url: str = ""  # set only when the server redirected somewhere else
    error: str = ""  # non-empty when the page could not be fetched/parsed
    title: str = ""
    meta_description: str = ""
    canonical: str = ""
    og: Dict[str, str] = field(default_factory=dict)
    headings: Dict[str, List[str]] = field(default_factory=lambda: {"h1": [], "h2": [], "h3": []})
    word_count: int = 0
    internal_links: List[str] = field(default_factory=list)
    external_links: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)
    json_ld: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Page":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    @property
    def ok(self) -> bool:
        return self.status_code == 200 and not self.error
