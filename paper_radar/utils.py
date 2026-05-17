from __future__ import annotations

import html
import re
from datetime import date, datetime, timedelta, timezone


TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = TAG_RE.sub(" ", value)
    value = html.unescape(value)
    return SPACE_RE.sub(" ", value).strip()


def iso_date(days_ago: int = 0) -> str:
    return (datetime.now(timezone.utc).date() - timedelta(days=days_ago)).isoformat()


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().lower().removeprefix("https://doi.org/")


def parse_date_parts(parts: list[list[int]] | None) -> str:
    if not parts:
        return ""
    vals = parts[0]
    try:
        if len(vals) == 1:
            return date(vals[0], 1, 1).isoformat()
        if len(vals) == 2:
            return date(vals[0], vals[1], 1).isoformat()
        return date(vals[0], vals[1], vals[2]).isoformat()
    except ValueError:
        return ""
