from __future__ import annotations

from datetime import date
from typing import Any

import requests

from paper_radar.models import Paper
from paper_radar.utils import clean_text, normalize_doi, parse_date_parts


class CrossrefFetcher:
    API_URL = "https://api.crossref.org/works"

    def __init__(self, mailto: str | None = None, timeout: int = 30) -> None:
        self.mailto = mailto
        self.timeout = timeout

    def fetch_journal(self, journal: dict[str, Any], from_date: date, until_date: date, rows: int = 50) -> list[Paper]:
        aliases = journal.get("aliases") or [journal["name"]]
        papers: list[Paper] = []
        for alias in aliases:
            papers.extend(self._query(alias, journal["name"], from_date, until_date, rows))
        return papers

    def _query(self, alias: str, canonical_journal: str, from_date: date, until_date: date, rows: int) -> list[Paper]:
        params: dict[str, Any] = {
            "query.container-title": alias,
            "filter": f"from-pub-date:{from_date.isoformat()},until-pub-date:{until_date.isoformat()},type:journal-article",
            "select": "DOI,title,container-title,published-print,published-online,published,URL,abstract,author",
            "rows": rows,
            "sort": "published",
            "order": "desc",
        }
        if self.mailto:
            params["mailto"] = self.mailto
        response = requests.get(self.API_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        items = response.json().get("message", {}).get("items", [])
        return [self._parse_item(item, canonical_journal) for item in items if self._is_match(item, alias)]

    @staticmethod
    def _is_match(item: dict[str, Any], alias: str) -> bool:
        containers = item.get("container-title") or []
        alias_norm = alias.casefold()
        return any(str(container).casefold() == alias_norm for container in containers)

    @staticmethod
    def _parse_item(item: dict[str, Any], canonical_journal: str) -> Paper:
        title = clean_text(" ".join(item.get("title") or []))
        journal = clean_text((item.get("container-title") or [canonical_journal])[0])
        date_parts = (
            item.get("published-online", {}).get("date-parts")
            or item.get("published-print", {}).get("date-parts")
            or item.get("published", {}).get("date-parts")
        )
        authors = []
        for author in item.get("author") or []:
            given = clean_text(author.get("given"))
            family = clean_text(author.get("family"))
            name = " ".join(part for part in [given, family] if part)
            if name:
                authors.append(name)
        return Paper(
            title=title,
            journal=journal or canonical_journal,
            published_date=parse_date_parts(date_parts),
            doi=normalize_doi(item.get("DOI")),
            url=item.get("URL"),
            abstract=clean_text(item.get("abstract")),
            authors=authors,
            source="Crossref",
        )
