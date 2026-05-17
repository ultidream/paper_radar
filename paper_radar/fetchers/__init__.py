from __future__ import annotations

from datetime import date
from typing import Any

from paper_radar.fetchers.crossref import CrossrefFetcher
from paper_radar.fetchers.europepmc import EuropePmcFetcher
from paper_radar.models import Paper


def fetch_all(config: dict[str, Any], journals: list[dict[str, Any]], from_date: date, until_date: date) -> list[Paper]:
    papers: list[Paper] = []
    sources = config.get("sources", {})
    if sources.get("crossref", {}).get("enabled", True):
        fetcher = CrossrefFetcher(mailto=sources.get("crossref", {}).get("mailto"))
        for journal in journals:
            try:
                papers.extend(fetcher.fetch_journal(journal, from_date, until_date))
            except Exception as exc:
                print(f"Warning: Crossref failed for {journal.get('name')}: {exc}")
    if sources.get("europepmc", {}).get("enabled", True):
        fetcher = EuropePmcFetcher()
        for journal in journals:
            try:
                papers.extend(fetcher.fetch_journal(journal, from_date, until_date))
            except Exception as exc:
                print(f"Warning: Europe PMC failed for {journal.get('name')}: {exc}")
    return dedupe_papers(papers)


def dedupe_papers(papers: list[Paper]) -> list[Paper]:
    merged: dict[str, Paper] = {}
    for paper in papers:
        if not paper.title:
            continue
        key = paper.stable_id
        if key not in merged:
            merged[key] = paper
            continue
        current = merged[key]
        if paper.abstract and not current.abstract:
            current.abstract = paper.abstract
        if paper.authors and not current.authors:
            current.authors = paper.authors
        if paper.url and not current.url:
            current.url = paper.url
        current.source = "+".join(sorted(set(current.source.split("+") + paper.source.split("+"))))
    return list(merged.values())
