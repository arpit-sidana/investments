# Investments

Dated investment research, with browser reports, calculation code and versioned evidence.

## IXN vs QQQ vs VOO — October 19, 2026

**[Read the interactive report](https://arpit-sidana.github.io/investments/reports/ixn-qqq-voo-2026-10-19/)**

- [Read the report directly on GitHub](reports/ixn-qqq-voo/REPORT.md)
- [Download the self-contained HTML](https://arpit-sidana.github.io/investments/downloads/ixn-qqq-voo-2026-10-19.html) — save it to read locally without a server
- [Methods and limitations](etf-research/outputs/METHODS.md)
- [Executed calculation notebook](etf-research/outputs/etf-comparison.ipynb)
- [Full-precision calculation outputs](etf-research/outputs)
- [Calculation source](etf-research/analyze.py) and [source retrieval log](etf-research/sources/fetch_log.json)

The comparison covers IXN inception, January 1990, January 2000 and January 2010 through October 19, 2026; historical risk; current-weight TSMC/ASML removal; synthetic stock-count diversification; historical resampling; fundamentals, technicals, fees and a conditional AI outlook.

Prelaunch results use explicitly identified proxies. The stock-removal model is an assumption sensitivity, not historical attribution. The 1,200-stock model holds the technology factor fixed; it does not backtest 1,200 actual stocks. Historical resampling shares are not forecast probabilities. Figures and conclusions do not update automatically.

## How this stays available

GitHub Pages serves the already-built files in `docs/` from the `main` branch. It needs no running computer, backend, API key, build service or paid market-data subscription. Git stores the report, authoring source, derived results and the numerical source snapshots needed by the calculations. Full provider articles, web pages and PDFs are linked rather than republished.

The Markdown report remains readable on GitHub even if Pages is disabled. The offline HTML contains the same reviewed data and application in one file. Keep a local clone and a separate backup for independence from GitHub. GitHub Pages is durable hosting, not a promise of permanent availability; deleting or renaming the repository/account, disabling Pages or a provider policy change can affect its URL.

Published presentation edits in this static report are browser-local; they do not commit research changes to GitHub. To make a shared update, revise the source and evidence, build, verify, commit and push a new version. Preserve dated report URLs when adding later reports.

## Reproduce and maintain

For numerical calculations, use Python 3.12+ and `etf-research/requirements.txt`. From `etf-research`, run `python analyze.py`, then `python supplement.py`. These read the committed numerical snapshots; no market-data refresh is required. `python package_analysis.py` recreates the executed notebook. Use a virtual environment; the local `vendor/` dependency cache is excluded from Git.

`python etf-research/build_report.py` packages the reviewed outputs into the report snapshot and Markdown companion without fetching data or simulating new results. The interactive authoring project is `reports/ixn-qqq-voo/`; its `AGENTS.md` documents the Data report runtime and build commands. The installed Data plugin is required to rebuild that app, but **reading or hosting the committed report requires no plugin**. A fresh clone can serve `docs/` unchanged with `python -m http.server --directory docs`.

After a verified report build and offline export, run `python scripts/package_pages.py`. It copies the verified bundle and offline HTML into `docs/`, checks content hashes and writes a release manifest. Commit and push the resulting files. Pages automatically deploys changes from `main:/docs`.

Research judgments are general analysis, without a personal tax or portfolio assessment. Source providers retain rights in their materials.
