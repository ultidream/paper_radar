from __future__ import annotations

import sqlite3
from pathlib import Path

from paper_radar.models import Paper


class SeenPaperStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_papers (
                stable_id TEXT PRIMARY KEY,
                doi TEXT,
                title TEXT NOT NULL,
                journal TEXT,
                first_seen_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def has_seen(self, paper: Paper) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM seen_papers WHERE stable_id = ?",
            (paper.stable_id,),
        ).fetchone()
        return row is not None

    def mark_seen(self, paper: Paper) -> None:
        self.conn.execute(
            """
            INSERT OR IGNORE INTO seen_papers (stable_id, doi, title, journal)
            VALUES (?, ?, ?, ?)
            """,
            (paper.stable_id, paper.doi, paper.title, paper.journal),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
