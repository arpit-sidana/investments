# Investments

Dated investment research, readable directly in GitHub on a phone. **Markdown is the default delivery format.** Reports are static editions; prices and conclusions do not update automatically.

## Read the reports

| Research | Date | Reading copy |
| --- | --- | --- |
| AI equities through end-2027: 25 companies, K-shaped economy, agents, infrastructure and a $100k scenario portfolio | October 22, 2026; October 16 entry prices | [Full report](research-reports/ai-equities-2027-2026-10-22/REPORT.md) |
| Crypto State of the Union: applications, protocols, economics and risks | October 19, 2026 | [Full report](CRYPTO_REPORT.md) |
| IXN vs QQQ vs VOO: performance, risk, diversification and AI outlook | October 19, 2026 | [Full report](reports/ixn-qqq-voo/REPORT.md) |

The AI report includes all 25 company analyses, 75 bear/base/bull price scenarios, valuation assumptions, catalysts, portfolio weights, stress cases and linked sources. [Source index](ai-equities-source-index.md) · [Model inputs](ai-equities-model.json).

The crypto report includes its 20 chapters, 11 chart images and tables. Its earlier standalone reading link remains available on the [`crypto-report-reading-copy` branch](https://github.com/arpit-sidana/investments/blob/crypto-report-reading-copy/CRYPTO_REPORT.md).

The ETF report covers inception and historical start dates, current-weight TSMC/ASML removal, a synthetic stock-count comparison, historical resampling, fundamentals, fees and a conditional AI outlook. [Methods](etf-research/outputs/METHODS.md) · [Calculation notebook](etf-research/outputs/etf-comparison.ipynb) · [Outputs](etf-research/outputs).

## Standing delivery preference

For completed investment analyses and material revisions in this workspace:

1. Write a complete, dated `.md` reading copy with sources, assumptions, tables and required visual assets.
2. Commit and push the report and relevant reproducible files to this established repository, excluding secrets, personal account records, dependencies, caches and generated build output.
3. Update this index and verify the saved GitHub document.
4. Return the GitHub document link for reading on a phone.

Do not start localhost previews, make a web app the default report, or deploy GitHub Pages/ChatGPT Sites unless explicitly requested. These rules are saved in [AGENTS.md](AGENTS.md) and the [investment delivery skill](.agents/skills/investment-github-reading-copy/SKILL.md).

This checkout uses `codex/investment-reading-copies`, a document branch. The existing Pages site uses `main:/docs`; this report workflow does not modify its source or deployment settings. Earlier browser reports and source projects are retained as archives. The Markdown reading copies remain usable without running an app or server.

## Reproduce the AI report

Run `node scripts/render-ai-equities-markdown.mjs` from the repository. It reads saved narrative, company/scenario inputs and the portfolio snapshot, checks completeness and scenario arithmetic, and writes the Markdown report. It does not refresh quotes or publish anything by itself.

- [Narrative input](research-reports/ai-equities-2027-2026-10-22/narrative.json)
- [Company/scenario model](ai-equities-model.json)
- [Portfolio and evidence snapshot](ai-equities-snapshot.json)
- [Research source index](ai-equities-source-index.md)
- [Original validation notes](ai-equities-validation.json)

The earlier `assemble-ai-equities-report.mjs` and authored report content/data are retained as legacy sources. Generated app framework files and build output are excluded from version control. Use the Markdown renderer for routine updates.

## Other archived research

The September 16 Glean research is preserved in [its snapshot](glean-investment-snapshot.json) and [original narrative source](glean-investment-report/src/content/report/ReportContent.jsx). It has not been refreshed as part of the October AI-report conversion.

For ETF calculations, use Python 3.12+ and `etf-research/requirements.txt`. From `etf-research`, run `python analyze.py`, then `python supplement.py`; `python package_analysis.py` recreates the notebook. These read committed numerical snapshots. [Source retrieval log](etf-research/sources/fetch_log.json).

Source providers retain rights in their materials. Published research does not contain personal brokerage/account records. Scenario probabilities and investment judgments are estimates, with limitations stated in each report.
