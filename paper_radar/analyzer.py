from __future__ import annotations

import json
import os
from typing import Any

from paper_radar.models import Paper, PaperAnalysis


FALLBACK_ANALYSIS = PaperAnalysis(
    one_sentence="未启用 AI 分析；请先配置 LLM_API_KEY 或 OPENAI_API_KEY。",
    why_it_matters="报告已保留标题、作者、期刊、摘要和链接，可先用于每日追踪。",
    methods_data="请阅读摘要和原文判断方法、数据与模型。",
    what_to_learn=["研究问题如何表述", "摘要中的方法和数据来源", "作者团队和机构分工"],
    relevance="需要结合你的具体研究方向进一步判断。",
    collaboration_authors=[],
    collaboration_ideas=["阅读全文后寻找数据、模型、区域或方法上的互补点。"],
    outreach_angle="可从共同研究问题、可复用数据或方法改进切入联系作者。",
)


class PaperAnalyzer:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.enabled = bool(config.get("analysis", {}).get("enabled", True))
        self.model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or config.get("analysis", {}).get("model", "gpt-4.1-mini")
        self.base_url = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or config.get("analysis", {}).get("base_url")
        self.api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.max_abstract_chars = int(config.get("analysis", {}).get("max_abstract_chars", 2200))

    def analyze(self, paper: Paper) -> PaperAnalysis:
        if not self.enabled or not self.api_key:
            return FALLBACK_ANALYSIS

        try:
            from openai import OpenAI

            client_kwargs: dict[str, Any] = {"api_key": self.api_key, "timeout": 45.0}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            client = OpenAI(**client_kwargs)
            response = client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                max_tokens=1200,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": self._paper_prompt(paper)},
                ],
            )
            content = response.choices[0].message.content or "{}"
            return self._parse_response(content)
        except Exception as exc:
            return PaperAnalysis(
                one_sentence="AI 分析失败，已保留论文元数据。",
                why_it_matters=(
                    f"调用模型失败：{type(exc).__name__}: {exc}. "
                    f"当前模型={self.model}; base_url={self.base_url or '未设置，默认 OpenAI 官方接口'}。"
                ),
                methods_data="请检查 LLM_API_KEY、LLM_MODEL、LLM_BASE_URL 是否与同一个服务商匹配。",
                what_to_learn=["先用元数据筛选是否值得精读", "检查摘要中的方法和数据", "待模型配置修复后重新运行日报"],
                relevance="暂未判断。",
                collaboration_authors=[],
                collaboration_ideas=["模型调用恢复后重新生成合作建议。"],
                outreach_angle="暂未生成。",
            )

    def _system_prompt(self) -> str:
        interests = "\n".join(f"- {x}" for x in self.config.get("profile", {}).get("research_interests", []))
        goals = "\n".join(f"- {x}" for x in self.config.get("profile", {}).get("collaboration_goals", []))
        return (
            "你是一个严谨的科研文献助理，服务对象是一位环境、气候、大气或健康相关方向的研究者。\n"
            "请用简洁中文分析论文，不夸大，不编造摘要中没有的信息。\n"
            "如果摘要不足，请明确说明不确定性。\n"
            "研究兴趣：\n"
            f"{interests}\n"
            "合作目标：\n"
            f"{goals}\n"
            "必须只输出 JSON，不要 Markdown，不要代码块。"
        )

    def _paper_prompt(self, paper: Paper) -> str:
        abstract = (paper.abstract or "No abstract available.")[: self.max_abstract_chars]
        return json.dumps(
            {
                "task": "Analyze this newly published paper for a daily research tracking report.",
                "required_json_schema": {
                    "one_sentence": "一句话说明这篇论文做了什么",
                    "why_it_matters": "它为什么重要",
                    "methods_data": "方法、数据、模型或实验设计",
                    "what_to_learn": ["我能学习的具体点 1", "具体点 2", "具体点 3"],
                    "relevance": "与我的研究方向可能有什么关系",
                    "collaboration_authors": ["最值得关注或联系的作者姓名"],
                    "collaboration_ideas": ["具体合作切入点 1", "具体合作切入点 2"],
                    "outreach_angle": "如果联系作者，第一封邮件可以从什么角度切入",
                },
                "paper": {
                    "title": paper.title,
                    "journal": paper.journal,
                    "published_date": paper.published_date,
                    "authors": paper.authors[:20],
                    "first_author": paper.first_author,
                    "first_author_affiliations": paper.first_author_affiliations[:3],
                    "corresponding_authors": paper.corresponding_authors,
                    "doi": paper.doi,
                    "abstract": abstract,
                },
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _parse_response(content: str) -> PaperAnalysis:
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            content = content[start : end + 1]
        data = json.loads(content)
        return PaperAnalysis(
            one_sentence=str(data.get("one_sentence", "")),
            why_it_matters=str(data.get("why_it_matters", "")),
            methods_data=str(data.get("methods_data", "")),
            what_to_learn=[str(x) for x in data.get("what_to_learn") or []],
            relevance=str(data.get("relevance", "")),
            collaboration_authors=[str(x) for x in data.get("collaboration_authors") or []],
            collaboration_ideas=[str(x) for x in data.get("collaboration_ideas") or []],
            outreach_angle=str(data.get("outreach_angle", "")),
        )
