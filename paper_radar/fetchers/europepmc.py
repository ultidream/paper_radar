from __future__ import annotations

from datetime import date
from typing import Any

import requests

from paper_radar.models import Paper
from paper_radar.utils import clean_text, normalize_doi


class EuropePmcFetcher:
    API_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def fetch_journal(self, journal: dict[str, Any], from_date: date, until_date: date, page_size: int = 50) -> list[Paper]:
        aliases = journal.get("aliases") or [journal["name"]]
        papers: list[Paper] = []
        for alias in aliases:
            query = (
                f'JOURNAL:"{alias}" '
                f'FIRST_PDATE:[{from_date.isoformat()} TO {until_date.isoformat()}]'
            )
            params = {
                "query": query,
                "format": "json",
                "pageSize": page_size,
                "sort": "FIRST_PDATE_D desc",
            }
            response = requests.get(self.API_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            results = response.json().get("resultList", {}).get("result", [])
            papers.extend(self._parse_item(item, journal["name"]) for item in results)
        return papers

    @staticmethod
    def _parse_item(item: dict[str, Any], canonical_journal: str) -> Paper:
        author_text = clean_text(item.get("authorString"))
        authors = [name.strip() for name in author_text.rstrip(".").split(",") if name.strip()]
        doi = normalize_doi(item.get("doi"))
        full_text_urls = item.get("fullTextUrlList", {}).get("fullTextUrl") or []
        fallback_url = full_text_urls[0].get("url") if full_text_urls else None
        return Paper(
            title=clean_text(item.get("title")),
            journal=clean_text(item.get("journalTitle")) or canonical_journal,
            published_date=clean_text(item.get("firstPublicationDate") or item.get("pubYear")),
            doi=doi,
            url=f"https://doi.org/{doi}" if doi else fallback_url,
            abstract=clean_text(item.get("abstractText")),
            authors=authors,
            source="Europe PMC",
            extra={"pmid": item.get("pmid"), "pmcid": item.get("pmcid")},
        )
