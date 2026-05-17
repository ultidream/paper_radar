# 每日科研论文雷达

这个项目每天自动追踪指定期刊的新论文，分析题目、摘要、作者和潜在合作机会，生成 Word 报告，并可通过邮件发送给你。

## 目前覆盖

默认期刊列表在 `journals.yaml`：

- Nature 系列：Nature, Nature Climate Change, Nature Geoscience, Nature Communications, Nature Sustainability
- Science, Science Advances
- Cell, One Earth
- The Lancet 系列
- Environmental Science & Technology, ES&T Letters
- Atmospheric Chemistry and Physics, Geoscientific Model Development

可以直接编辑 `journals.yaml` 添加或删除期刊。

## 本地运行

```powershell
cd C:\Users\admin\OneDrive\USST\codex_personal\paper_radar
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item config.example.yaml config.yaml
```

编辑 `config.yaml`，把 `profile.research_interests` 改成你的真实研究方向。

设置 OpenAI key：

```powershell
$env:OPENAI_API_KEY="sk-..."
```

只生成 Word，不发邮件：

```powershell
py -m paper_radar.main --no-email
```

输出文件在 `reports/`。

## 邮件发送

推荐使用 Gmail App Password，而不是普通登录密码。

本地测试：

```powershell
$env:EMAIL_ENABLED="true"
$env:SMTP_USER="your_gmail_address@gmail.com"
$env:SMTP_PASSWORD="your_gmail_app_password"
$env:REPORT_RECIPIENTS="recipient@example.com"
py -m paper_radar.main
```

如果只想先看 Word 附件，不想发邮件，运行时加 `--no-email`。

## GitHub Actions 每天自动运行

把 `paper_radar` 目录上传到一个 GitHub 仓库。 workflow 已经在：

```text
.github/workflows/daily-paper-radar.yml
```

它会在北京时间每天早上 7 点运行。

在 GitHub 仓库里设置这些 Secrets：

- `OPENAI_API_KEY`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `REPORT_RECIPIENTS`

可选设置 Repository Variable：

- `OPENAI_MODEL`，默认 `gpt-4.1-mini`

然后进入 GitHub Actions 页面，可以手动点 `Run workflow` 测试一次。

## 工作方式

1. 查询过去 `lookback_days` 天的新论文。
2. 使用 Crossref 和 Europe PMC 抓取题目、作者、DOI、摘要和链接。
3. 用 DOI 或标题去重。
4. SQLite 保存已处理论文，避免重复推送。
5. 调用 OpenAI 生成中文分析。
6. 生成 Word。
7. 如果启用邮件，发送 Word 附件。

## 常见调整

- 想减少邮件内容：降低 `run.max_papers_per_run`。
- 漏报新论文：把 `run.lookback_days` 从 2 改成 3 或 5。
- 想多关注某个领域：在 `profile.research_interests` 加更具体的关键词。
- 想加期刊：在 `journals.yaml` 增加 `name` 和 `aliases`。

## 重要限制

摘要和期刊元数据来自公开 API，部分出版社可能延迟同步或不提供摘要。AI 分析是筛选辅助，不应替代阅读全文。
