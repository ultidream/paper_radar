from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Any


def send_report(config: dict[str, Any], attachment_path: Path, paper_count: int) -> None:
    email_cfg = config.get("email", {})
    enabled = str(os.getenv("EMAIL_ENABLED", "")).lower() in {"1", "true", "yes"} or email_cfg.get("enabled", False)
    if not enabled:
        return

    sender = os.getenv("SMTP_USER") or email_cfg.get("sender")
    password = os.getenv("SMTP_PASSWORD")
    env_recipients = os.getenv("REPORT_RECIPIENTS", "")
    recipients = [x.strip() for x in env_recipients.split(",") if x.strip()]
    if not recipients:
        recipients = [x for x in email_cfg.get("recipients", []) if x]
    if not sender or not password or not recipients:
        raise ValueError("Email is enabled, but SMTP_USER/SMTP_PASSWORD/recipients are not configured")

    subject_prefix = email_cfg.get("subject_prefix", "Daily Paper Radar")
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"{subject_prefix}: {paper_count} new papers"
    msg.set_content(
        "今日科研论文追踪报告见附件。\n\n"
        "如果附件为空或论文过少，请检查期刊列表、API 限制和 lookback_days 设置。\n"
    )

    data = attachment_path.read_bytes()
    msg.add_attachment(
        data,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=attachment_path.name,
    )

    host = email_cfg.get("smtp_host", "smtp.gmail.com")
    port = int(email_cfg.get("smtp_port", 587))
    with smtplib.SMTP(host, port) as smtp:
        smtp.starttls()
        smtp.login(sender, password)
        smtp.send_message(msg)
