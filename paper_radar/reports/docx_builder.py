from __future__ import annotations

from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.shared import Inches, Pt, RGBColor

from paper_radar.models import Paper, PaperAnalysis


class DocxReportBuilder:
    def build(
        self,
        output_path: Path,
        papers: list[tuple[Paper, PaperAnalysis]],
        report_date: date,
        owner_name: str = "",
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = Document()
        self._set_styles(doc)

        title = doc.add_paragraph(style="Title")
        title.add_run("每日科研论文雷达")
        subtitle = doc.add_paragraph(style="Subtitle")
        subtitle.add_run(f"{report_date.isoformat()} | {owner_name or 'Research briefing'}")

        lead = doc.add_paragraph()
        lead.add_run(f"今日共发现 {len(papers)} 篇新论文。").bold = True
        lead.add_run(" 本报告按期刊新发表记录自动整理，AI 分析用于辅助筛选，重要论文建议继续阅读全文核查。")

        self._add_summary_table(doc, papers)

        for index, (paper, analysis) in enumerate(papers, start=1):
            if index > 1:
                doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            self._add_paper_section(doc, index, paper, analysis)

        doc.save(output_path)
        return output_path

    @staticmethod
    def _set_styles(doc: Document) -> None:
        section = doc.sections[0]
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

        styles = doc.styles
        normal = styles["Normal"]
        normal.font.name = "Arial"
        normal.font.size = Pt(10.5)

        for style_name, size, color in [
            ("Title", 22, RGBColor(31, 78, 121)),
            ("Subtitle", 10.5, RGBColor(89, 89, 89)),
            ("Heading 1", 15, RGBColor(31, 78, 121)),
            ("Heading 2", 12, RGBColor(55, 96, 146)),
        ]:
            style = styles[style_name]
            style.font.name = "Arial"
            style.font.size = Pt(size)
            style.font.color.rgb = color

    @staticmethod
    def _add_summary_table(doc: Document, papers: list[tuple[Paper, PaperAnalysis]]) -> None:
        doc.add_heading("今日速览", level=1)
        table = doc.add_table(rows=1, cols=4)
        table.style = "Table Grid"
        headers = ["#", "期刊", "论文题目", "一句话判断"]
        for cell, header in zip(table.rows[0].cells, headers):
            cell.text = header
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold = True
        for idx, (paper, analysis) in enumerate(papers, start=1):
            cells = table.add_row().cells
            cells[0].text = str(idx)
            cells[1].text = paper.journal
            cells[2].text = paper.title
            cells[3].text = analysis.one_sentence

    def _add_paper_section(self, doc: Document, index: int, paper: Paper, analysis: PaperAnalysis) -> None:
        doc.add_heading(f"{index}. {paper.title}", level=1)

        meta = doc.add_paragraph()
        meta.add_run("期刊：").bold = True
        meta.add_run(f"{paper.journal}  ")
        meta.add_run("日期：").bold = True
        meta.add_run(f"{paper.published_date or 'Unknown'}  ")
        if paper.doi:
            meta.add_run("DOI：").bold = True
            meta.add_run(paper.doi)

        if paper.authors:
            authors = ", ".join(paper.authors[:18])
            if len(paper.authors) > 18:
                authors += " et al."
            para = doc.add_paragraph()
            para.add_run("作者：").bold = True
            para.add_run(authors)

        if paper.url:
            para = doc.add_paragraph()
            para.add_run("链接：").bold = True
            para.add_run(paper.url)

        self._add_labeled_paragraph(doc, "这篇论文做了什么", analysis.one_sentence)
        self._add_labeled_paragraph(doc, "为什么重要", analysis.why_it_matters)
        self._add_labeled_paragraph(doc, "方法 / 数据 / 模型", analysis.methods_data)
        self._add_bullets(doc, "我能学习什么", analysis.what_to_learn)
        self._add_labeled_paragraph(doc, "和我的研究方向的关系", analysis.relevance)
        self._add_bullets(doc, "可关注或合作的作者", analysis.collaboration_authors)
        self._add_bullets(doc, "合作切入点", analysis.collaboration_ideas)
        self._add_labeled_paragraph(doc, "联系作者的邮件角度", analysis.outreach_angle)

        if paper.abstract:
            self._add_labeled_paragraph(doc, "摘要", paper.abstract)

    @staticmethod
    def _add_labeled_paragraph(doc: Document, label: str, text: str) -> None:
        doc.add_heading(label, level=2)
        doc.add_paragraph(text or "未提供。")

    @staticmethod
    def _add_bullets(doc: Document, label: str, items: list[str]) -> None:
        doc.add_heading(label, level=2)
        if not items:
            doc.add_paragraph("未提供。")
            return
        for item in items:
            doc.add_paragraph(str(item), style="List Bullet")
