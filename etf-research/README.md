# IXN / QQQ / VOO research calculations

Prepared October 19, 2026. The report and interpretation are in ../reports/ixn-qqq-voo/REPORT.md; this folder supplies the calculation audit trail.

Start with `outputs/METHODS.md`, the executed `outputs/etf-comparison.ipynb`, and `outputs/validation.json`. CSVs contain full-precision results and use fractions for rates (0.125 means 12.5%). The notebook preview preserves executed outputs without requiring a running kernel.

`fetch_data.py` retrieves public-source snapshots and records URLs and retrieval times in `sources/fetch_log.json`. Some candidate endpoints failed or returned HTML; only validated snapshots feed `analyze.py`. The failed FRED/Stooq downloads and incomplete XNDX history are not analysis inputs. Korean stock downloads are unused: a full inception-to-current USD history was not validated. The exclusion test covers TSMC and ASML only, with weight sensitivity, rather than silently substituting a wider unverified group.

To recalculate from the saved snapshots, use Python 3.12 or newer, install `requirements.txt`, and run `python analyze.py` followed by `python supplement.py`. To recreate the executed notebook, run `python package_analysis.py`. These commands should run from this folder. The notebook itself assumes its execution working directory is `outputs/`. `supplement.py` also creates optional inline chart payloads in outputs/. The calculations do not require refreshing the data.

`package_analysis.py` and the local notebook use `vendor/` if present; a normal environment containing the same packages also works. The archive excludes that dependency directory. Native inline chart fragments and renderer runtimes are delivered in the chat and are not needed to rerun the numerical calculations.

Interpretation limits: exact prelaunch ETF histories do not exist; FSPTX is an active technology regime proxy, not IXN. Prelaunch QQQ omits dividends, with a separate assumed-dividend sensitivity. Exclusion uses constant current weights, not point-in-time historical holdings. Synthetic stock-count results are conditional factor experiments, not backtests of actual 1,200-stock portfolios. Bootstrap shares are not forecast probabilities. Read all qualifications in METHODS.md before using results.
