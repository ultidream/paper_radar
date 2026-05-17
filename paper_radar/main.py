from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from paper_radar.analyzer import PaperAnalyzer
from paper_radar.config import deep_get, load_config
from paper_radar.fetchers import fetch_all
from paper_radar.mailer import send_report
from paper_radar.reports.docx_builder import DocxReportBuilder
from paper_radar.storage.sqlite_store import SeenPaperStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily journal paper radar")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--journals", default="journals.yaml", help="Path to journals.yaml")
    parser.add_argument("--no-email", action="store_true", help="Generate report without sending email")
    parser.add_argument("--include-seen", action="store_true", help="Include papers already seen in previous runs")
    return parser.parse_args()


def ensure_config(config_path: Path) -> None:
    if config_path.exists():
        return
    example = config_path.with_name("config.example.yaml")
    if not example.exists():
        raise FileNotFoundError(f"Missing {config_path}; create it from config.example.yaml")
    shutil.copyfile(example, config_path)
    print(f"Created {config_path} from config.example.yaml. Edit it before production use.")


def main() -> None:
    args = parse_args()
    root = Path.cwd()
    config_path = root / args.config
    journals_path = root / args.journals
    ensure_config(config_path)
    config, journals = load_config(config_path, journals_path)

    lookback_days = int(deep_get(config, "run.lookback_days", 2))
    max_papers = int(deep_get(config, "run.max_papers_per_run", 40))
    today = datetime.now(timezone.utc).date()
    from_date = today - timedelta(days=lookback_days)

    print(f"Fetching papers from {from_date.isoformat()} to {today.isoformat()}...")
    papers = fetch_all(config, journals, from_date, today)
    papers = sorted(papers, key=lambda p: (p.published_date, p.journal, p.title), reverse=True)

    store = SeenPaperStore(root / deep_get(config, "run.database_path", "data/seen_papers.sqlite"))
    if not args.include_seen:
        papers = [paper for paper in papers if not store.has_seen(paper)]
    papers = papers[:max_papers]

    analyzer = PaperAnalyzer(config)
    analyzed = []
    for idx, paper in enumerate(papers, start=1):
        print(f"Analyzing {idx}/{len(papers)}: {paper.title[:90]}")
        analyzed.append((paper, analyzer.analyze(paper)))
        store.mark_seen(paper)
    store.close()

    output_dir = root / deep_get(config, "run.output_dir", "reports")
    report_path = output_dir / f"paper_radar_{today.isoformat()}.docx"
    DocxReportBuilder().build(
        report_path,
        analyzed,
        today,
        owner_name=deep_get(config, "profile.owner_name", ""),
    )
    print(f"Report written to {report_path}")

    if not args.no_email:
        send_report(config, report_path, len(analyzed))
        if deep_get(config, "email.enabled", False):
            print("Email sent.")


if __name__ == "__main__":
    main()
