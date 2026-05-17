from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Paper:
    title: str
    journal: str
    published_date: str
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None
    authors: list[str] = field(default_factory=list)
    source: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def stable_id(self) -> str:
        if self.doi:
            return f"doi:{self.doi.lower()}"
        return f"title:{self.title.strip().lower()}|{self.journal.strip().lower()}"


@dataclass(slots=True)
class PaperAnalysis:
    one_sentence: str
    why_it_matters: str
    methods_data: str
    what_to_learn: list[str]
    relevance: str
    collaboration_authors: list[str]
    collaboration_ideas: list[str]
    outreach_angle: str

