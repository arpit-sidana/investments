"""Package reviewed ETF results into the report; does not fetch or simulate data."""
from pathlib import Path
import csv, json, bisect, datetime

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
APP = ROOT.parent / 'reports' / 'ixn-qqq-voo'
R = json.loads((OUT / 'results.json').read_text())
S = json.loads((APP / 'src/data.json').read_text())
def csvrows(name):
    with (OUT / name).open() as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for k, v in row.items():
            if k in {"window", "calibration_window", "date", "fund", "company", "period"}: continue
            try: row[k] = float(v)
            except (ValueError, TypeError): pass
    return rows

links = [
    {'label':'iShares IXN: holdings, expenses, NAV and valuation', 'href':'https://www.ishares.com/us/products/239750/ishares-global-tech-etf'},
    {'label':'Invesco QQQ: fund facts and methodology', 'href':'https://www.invesco.com/us/en/financial-products/etfs/invesco-qqq-trust-series-1.html'},
    {'label':'Vanguard VOO: fund facts', 'href':'https://advisors.vanguard.com/investments/products/voo/vanguard-sp-500-etf'},
    {'label':'Public adjusted price histories', 'href':'https://finance.yahoo.com/quote/QQQ/history/'},
]
Q = {}
def query(key, rows, files, description, caveats=()):
    Q[key] = {'rows':rows,'source':{'label':description,'files':[{'label':f} for f in files],
        'links':links,'filters':['Research cutoff: October 19, 2026; source snapshot dates may differ.'],
        'caveats':list(caveats),'evidenceFlow':[
          {'title':'Public observations','detail':'Issuer NAV, holdings and characteristics; public adjusted price/index histories. Retrieval URLs and times are recorded in etf-research/sources/fetch_log.json.'},
          {'title':'Reviewed calculation','detail':'analyze.py and supplement.py create the named CSV/JSON files. build_report.py reads those completed results without rerunning market data or simulations.'}],
        'metricDefinitions':[{'label':description,'definition':description}]},
        'methods':[{'language':'text','code':'Read etf-research/outputs/'+', '.join(files)+'. '+description+' See METHODS.md and analyze.py for exact formulas and model seeds.'}]}

history_caveats = [
    'IXN before November 12, 2001 is FSPTX, an active US technology regime proxy, not reconstructed global IXN.',
    'QQQ before March 10, 1999 uses the Nasdaq-100 price index minus assumed 0.20% expense; dividends are omitted.',
    'VOO before September 9, 2010 uses S&P 500 total return minus assumed 0.03% expense.',
    'January 1 windows use the preceding year-end close. IXN uses issuer NAV through October 16 plus an October 19 market-return bridge.',
    'USD reinvested distributions; actual ETF returns are already fee-net. No taxes, trading costs, inflation or contributions.']
query('history', R['history'], ['historical_metrics.csv'], 'Daily-return metrics for every requested start window', history_caveats)
query('trailing', R['trailing'], ['trailing_metrics.csv'], 'Trailing total returns and annualized returns from available trading-day endpoints', history_caveats[3:])

# Sample the reviewed daily wealth levels at actual quarter-end trading dates.
levels = csvrows('daily_total_return_levels.csv'); dates = [r['date'] for r in levels]
fundcols = list(levels[0])[1:]; paths=[]
starts={'1990':'1989-12-29','2000':'1999-12-31','IXN inception':'2001-11-12','2010':'2009-12-31'}
for window, start in starts.items():
    i = bisect.bisect_left(dates,start); subset = levels[i:]; chosen={0,len(subset)-1}
    for j,row in enumerate(subset[:-1]):
        if row['date'][:4] != subset[j+1]['date'][:4] or (int(row['date'][5:7])-1)//3 != (int(subset[j+1]['date'][5:7])-1)//3:
            chosen.add(j)
    for j in sorted(chosen):
        for fund,col in zip(['IXN / tech proxy','QQQ / index proxy','VOO / index proxy'],fundcols):
            paths.append({'window':window,'date':subset[j]['date'],'fund':fund,'wealth_usd':10000*subset[j][col]/subset[0][col]})
query('wealth', paths, ['daily_total_return_levels.csv'], 'Growth of a USD 10,000 lump sum; actual trading-date quarter-end samples', history_caveats)
query('concentration', R['concentration'], ['concentration.csv'], 'Equity-only normalized issuer concentration: effective count = 1 / sum(weight squared)', ['IXN and QQQ holdings October 16; VOO September 30. Issuer classes are combined. Effective count measures unequal weights, not independent risk factors.'])
query('exclusion', R['exclusion'], ['exclusion_sensitivity.csv'], 'Current-weight TSMC / ASML removal and reallocation sensitivity', [
    'Assumes 4.68% TSMC and 2.53% ASML constant modern weights, monthly rebalancing, USD ADR/share proxies and an algebraically inferred IXN residual.',
    'Not historical stock attribution or an investable ex-stock index. Removes losses as well as gains. Current fee retained approximately, not exact historical schedules.',
    'Before IXN launch, the FSPTX proxy is left untouched; no broader Samsung/Hynix exclusion was validated.'])
expath=[]
for row in csvrows('exclusion_monthly_paths.csv'):
    for field,label in [('No removal','IXN'),('Current weights','IXN excluding TSMC + ASML'),('QQQ','QQQ')]:
        expath.append({'date':row['date'],'fund':label,'wealth_usd':row[field]*10000})
query('exclusion_path', expath, ['exclusion_monthly_paths.csv'], 'Monthly wealth in the constant-current-weight removal model', Q['exclusion']['source']['caveats'])
query('count', csvrows('matched_frequency_diversification.csv'), ['matched_frequency_diversification.csv'], 'Annualized monthly-return volatility: matched-frequency factor replay and actual benchmarks', [
    'Synthetic 5,000-path experiment, seed 20261019. Observed technology path held fixed; independent residuals assume 30% annual single-stock volatility, averaged across N equal-weight positions.',
    'No actual 1,200-stock portfolio was backtested. Dispersion is conditional residual uncertainty, not future market-risk confidence bounds.'])
query('equicorrelation', R['equicorrelation'], ['equicorrelation_diversification.csv'], 'Illustrative variance = stock variance × [rho + (1 − rho) / N]', ['Single-stock volatility assumed 35%; pairwise correlation assumed 0.2, 0.6 or 0.8, not estimated from holdings.'])
query('bootstrap', R['bootstrap'], ['paired_block_bootstrap.csv'], 'Paired 12-month moving-block historical resampling: 10,000 paths per calibration and horizon', ['Calibrations end September 2026, the last complete month. Non-wrapping blocks; seed 20261020. Historical win shares are not forward probabilities; structural and valuation changes are not modeled.'])
query('rolling', R['rolling'], ['rolling_windows.csv'], 'Rolling annualized return comparisons at complete month ends since IXN launch', ['Month ends through September 2026; overlapping windows are not independent and win shares are not forecast probabilities.'])
query('technicals', R['technicals'], ['technicals.json'], 'October 19 closing-price trend, momentum and realized range indicators', ['SMA uses closing prices; RSI/ATR use Wilder smoothing; MACD 12/26/9; Bollinger 20-day ±2 standard deviations. Technical indicators describe prices rather than predict investment returns.'])
query('fees', R['fees'], ['fee_compounding.csv'], 'USD 100,000 compounds at an assumed constant 8% gross annual return, multiplied by 1 − current fee annually', ['Scenario only, not forecast or historical performance. Actual historical ETF series already include their fund expenses.'])
query('exposures', csvrows('selected_ai_exposures.csv'), ['selected_ai_exposures.csv'], 'Selected AI-related company weights, as fractions of fund assets', ['Selected examples, not an exhaustive AI exposure score. Holdings snapshot dates differ; these are current positions, not historical weights.'])
query('valuation', csvrows('valuation_hurdle_sensitivity.csv'), ['valuation_hurdle_sensitivity.csv'], 'Hypothetical earnings-growth hurdle if IXN P/E contracts to 30 and QQQ to 25', ['IXN P/E October 16; QQQ September 30; dates and P/E conventions differ. Assumes QQQ EPS growth 12%, excludes dividends, applies current fees. These are scenarios, not valuations or forecasts.'])
query('dividend', csvrows('prelaunch_dividend_sensitivity.csv'), ['prelaunch_dividend_sensitivity.csv'], 'Sensitivity of 1990 QQQ proxy to assumed prelaunch dividend yield', ['Adds assumed annual reinvested yield only before March 10, 1999, without reconstructing actual dividends.'])
query('regimes', csvrows('regime_returns.csv'), ['regime_returns.csv'], 'Selected historical calendar-regime total returns', history_caveats)
fundamentals=[
 {'fund':'IXN','scope':'Global developed/emerging-market information technology','inception':'2001-11-12','expense':.0037,'equity_lines':130,'pe':37.17,'pb':10.25,'valuation_date':'2026-10-16'},
 {'fund':'QQQ','scope':'Nasdaq-100: large Nasdaq-listed nonfinancial companies','inception':'1999-03-10','expense':.0018,'equity_lines':101,'pe':29.480945,'pb':9.90682,'valuation_date':'2026-09-30'},
 {'fund':'VOO','scope':'S&P 500: US large companies across sectors','inception':'2010-09-07','expense':.0003,'equity_lines':505,'pe':27.5,'pb':5.4,'valuation_date':'2026-06-30'}]
query('fundamentals', fundamentals, ['concentration.csv','results.json'], 'Issuer fund characteristics and dated valuation snapshots', ['QQQ holds 100 issuers across 101 equity lines; IXN has 130 equity lines, not 1,200. Valuation methods differ; IXN excludes negative P/E and caps individual P/E at 60. Sector definitions are GICS for IXN and ICB for QQQ.'])

query('overlap', [{'comparison':k,**v} for k,v in R['overlap'].items()], ['overlap.json'], 'Current equity ticker overlap with IXN', ['Ticker mappings include issuer share classes but not supply-chain or economic overlap.'])
query('correlations', [{'window':w,'ixn_qqq_correlation':v['correlations']['IXN / prelaunch FSPTX']['QQQ / prelaunch NDX price'],'ixn_voo_correlation':v['correlations']['IXN / prelaunch FSPTX']['VOO / prelaunch S&P TR'],'qqq_voo_correlation':v['correlations']['QQQ / prelaunch NDX price']['VOO / prelaunch S&P TR']} for w,v in R['risk'].items()], ['risk_comparisons.json'], 'Pairwise simple daily-return correlations at each requested start', history_caveats)

S.update(title='QQQ for broad AI growth; IXN for a larger bet on global technology',queries=Q,buildStatus=S.get('buildStatus','creating'))
S['generatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(APP/'src/data.json').write_text(json.dumps(S,indent=2,allow_nan=False))

sections=[
('executive-summary',['history','concentration','fees'],'''## Executive Summary

- **QQQ is the stronger default for a long-term AI growth allocation; IXN is the more concentrated global technology tilt.** Since IXN launched on November 12, 2001, $10k became about **$224.6k in QQQ**, **$188.5k in IXN** and **$108.2k in the VOO/index splice**. Annualized returns were 13.29%, 12.50% and 10.02%, respectively.
- **IXN leads the recent cycle but is less diversified by weight.** Its trailing 10-year CAGR was 23.45%, against QQQ’s 20.63%. Yet 130 IXN equity lines amount to only **17.4 equally weighted holdings** by concentration, versus 29.7 for QQQ and 40.8 for VOO. Global listings do not remove shared technology risk.
- **The semiconductor advantage is real exposure, not proven historical attribution.** Removing TSMC and ASML at constant current weights lowers modeled IXN inception-to-date CAGR from 12.50% to 11.74%. That model cannot establish their actual historical contribution. Expanding an unchanged technology factor to 1,200 synthetic stocks barely reduces volatility.
- **The higher fee buys a different portfolio, not a return guarantee.** IXN costs 0.37% versus QQQ’s 0.18% and VOO’s 0.03%. Prefer IXN when you deliberately want more foundry, memory and equipment exposure; prefer QQQ for a broader mix of AI infrastructure and monetization, and VOO for the broad US equity core.'''),
('fund-structure',['fundamentals','exposures'],'''## 1. What you actually own

The initial holding-count premise needs correcting: **IXN has about 130 equity positions, QQQ 101 equity lines representing 100 issuers, and VOO 505 lines** in these snapshots. IXN does not spread capital across 1,200 stocks.

IXN tracks global information technology. That includes Nvidia, Apple, Microsoft, TSMC, ASML, Samsung and SK Hynix, but excludes major AI beneficiaries classified outside information technology. QQQ selects large nonfinancial Nasdaq-listed companies; it is exchange- and index-rule driven, rather than a pure technology or comprehensive innovation portfolio. VOO spans US large-cap sectors.

**IXN’s additional geography is useful but economically concentrated.** About 77.12% is US exposure, with Taiwan 6.91%, Korea 5.49%, Japan 3.90% and the Netherlands 2.74%. Semiconductors and equipment account for 47.78%, hardware 28.13%, and software/services 23.84%. QQQ’s 68.01% technology allocation uses ICB classification and is not directly comparable to IXN’s GICS figures.

QQQ adds Amazon, Alphabet and Meta, together about 13.69%, which IXN omits. IXN instead adds TSMC, Samsung, SK Hynix and Oracle; QQQ already owns ASML at about 0.67%. VOO also holds suppliers outside technology, including Eaton, Vertiv and GE Vernova. No fund captures the whole AI chain: private firms, utilities, power equipment, construction and data-center assets have different coverage.'''),
('history-analysis',['history','trailing','dividend'],'''## 2. Performance depends heavily on the starting valuation

Select a start window below. **The 1990 and 2000 IXN lines are active US technology proxies before IXN existed, not a reconstructed global IXN backtest.** The 1990 QQQ segment uses a price index before launch and omits dividends; VOO uses a fee-adjusted S&P 500 total-return index before September 2010. January 1 windows begin at the preceding available year-end close. Every retrospective window ends October 19, 2026.

QQQ wins the common inception window and the 2000 and 2010 spliced windows. The technology proxy wins from 1990, but its different strategy and the QQQ dividend omission prevent interpreting that result as evidence that historical IXN beat QQQ. Assuming 0.25% or 0.50% prelaunch QQQ dividend yield raises its 1990-window CAGR from 14.57% to 14.64% or 14.72%; this remains an assumption sensitivity.

IXN’s recent leadership is substantial: trailing 3-, 5- and 10-year CAGRs were **34.11%, 19.21% and 23.45%**, versus QQQ’s **26.60%, 14.54% and 20.63%**. The latest roughly one-year total returns were **34.10%, 19.51% and 16.69%** for IXN, QQQ and VOO. The one-year endpoints span slightly more than one calendar year because the anniversary fell on a non-trading day; total return and CAGR therefore differ slightly.

These are USD lump-sum returns with reinvested distributions. Historical ETF expenses are already reflected; no second fee deduction is applied. IXN uses issuer NAV through October 16 and an October 19 market-return bridge, so the final observation is an estimate of NAV performance.'''),
('risk-analysis',['history','rolling'],'''## 3. Large historical gains came with deep losses

The 2000-start technology proxy lost **83.92%** peak to trough; QQQ lost **82.96%**. A loss near 83% requires almost a sixfold gain from the trough merely to break even. QQQ’s March 2000 peak was not regained until February 2015 in this adjusted series; the FSPTX/IXN proxy recovered its peak in October 2017. Starting in late 2001 omits the first part of that collapse and makes the launch-window drawdown look much milder.

Since IXN’s launch, maximum daily drawdowns were about **54.97% for IXN, 53.40% for QQQ and 55.27% for the VOO/index splice**. VOO’s worst episode was the financial crisis; lower average volatility does not ensure a smaller loss in every recession.

Across overlapping complete-month windows since launch, IXN beat QQQ in **39.72% of 1-year, 37.26% of 3-year, 35.56% of 5-year and 24.02% of 10-year observations**. Those windows are not independent, and the shares are not forecast odds. They show how sensitive the recent IXN victory is to the chosen period.

The table for the selected start reports annualized daily volatility, maximum drawdown, a Sharpe ratio using a fixed 3% annual hurdle, and daily expected shortfall. Expected shortfall is the average return among the worst 5% of daily returns, not a maximum possible loss. The fixed-hurdle Sharpe is a comparison statistic, not a reconstruction of realized Treasury excess returns.'''),
('exclusion-analysis',['exclusion','exclusion_path'],'''## 4. What if TSMC and ASML’s returns are removed?

The modeled experiment fixes their modern IXN weights at **4.68% and 2.53%**, rebalances monthly, infers the remaining basket from IXN, and reallocates the removed sleeve across that residual basket. It removes their losses as well as gains. USD listed-share/ADR returns proxy the local shares IXN owns.

From IXN’s launch, modeled CAGR falls from **12.50% to 11.74%** and the ending $10k value falls from **$188.5k to $159.1k**. QQQ ends at **$224.6k**. Half the assumed stock weights yield 12.13% IXN CAGR, and double weights yield 10.82%; replacing the current-weight removed sleeve with zero-return cash yields 10.97%. This sensitivity shows dependence on the assumed allocation, rather than measuring historical attribution.

**Actual historical weights and constituents are unavailable here.** Today’s winners did not necessarily carry today’s weights in 2001. The residual portfolio is algebraically inferred and the fee retained approximately; this is not an investable historical ex-TSMC/ASML index or a simulation of an economy without those companies. QQQ itself contains ASML. Samsung and SK Hynix were not removed because their full-history USD data were not validated.

The experiment is repeated for every requested start. For 1990 and 2000, removal begins only when IXN launches; the earlier FSPTX segment stays unchanged. The four-window sensitivity table below makes that limitation explicit.'''),
('diversification-analysis',['concentration','count','equicorrelation','correlations','overlap'],'''## 5. Why 1,200 technology stocks need not diversify better

**Count is weaker evidence than weight concentration and shared risk.** The Herfindahl index, or HHI, is the sum of squared issuer weights. Its inverse is the number of equally weighted positions with the same concentration. IXN’s effective count is **17.4**, QQQ’s **29.7**, and VOO’s **40.8**. IXN’s top three take 36.77% and its top ten issuers 60.89%, versus QQQ’s 22.31% and 49.81%.

Since launch, IXN and QQQ have a daily return correlation of about **0.948**. Current weighted stock overlap is about **52.95%**, and 70.87% of IXN’s equity weight is in names also held by QQQ. Holding both mainly changes weights within a similar growth risk exposure. HHI, ticker overlap and return correlation measure different things; none alone measures every source of diversification.

The stock-count model keeps each observed technology path fixed and averages independent stock residuals with assumed 30% annual volatility over 100, 130, 500 or 1,200 equally weighted positions. **These are synthetic portfolios, not 1,200 actual stock histories.** Each requested window is replayed 5,000 times. Increasing from 130 to 1,200 reduces inception-window annualized monthly volatility only from **20.81% to 20.67%**, still above QQQ’s 19.33% and VOO’s 14.76% at the same frequency.

An independent formula makes the reason clear: portfolio variance = single-stock variance × [correlation + (1 − correlation) / N]. With 35% single-stock volatility and assumed 0.60 correlation, moving from 100 to 1,200 stocks reduces volatility only from **27.20% to 27.12%**. The common component survives as N grows. More countries or tickers cannot diversify away a global semiconductor cycle, duration exposure, correlated AI capital spending or a Taiwan disruption.

For the same factor exposure, extra independent names reduce company-specific noise. To reduce total portfolio risk substantially, change the factor mix: sectors, economic sensitivities, asset classes and position weights matter more than moving from hundreds to thousands of correlated technology stocks. The synthetic replay holds expected residual returns at zero and therefore does not claim that adding stocks improves returns.'''),
('ai-thesis',['exposures','fundamentals'],'''## 6. AI value can shift from scarce infrastructure to customers

Your premise is plausible: early capital spending can accrue to chips, foundries, equipment, networking, memory, cloud capacity and power systems before application revenue catches up. Recent operating strength supports the buildout, but does not prove that these stocks offer the best future return at their current price. [TSMC’s Q3 2026 results](https://investor.tsmc.com/english/quarterly-results/2026/q3) reported $46.72bn revenue and a 66.4% gross margin. [ASML’s Q3 release](https://www.investor.asml.com/news-releases/news-release-details/asml-reports-eu11.7-billion-total-net-sales-and-eu5.0-billion-net-income-q3-2026) reported €11.7bn sales and €5.0bn net income. The [IEA energy-and-AI update](https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary) projects data-center electricity use growing from about 485 TWh in 2025 to 950 TWh in 2030, while highlighting delivery constraints.

**IXN expresses the supplier-scarcity thesis more strongly.** It puts 13.46% in Nvidia versus QQQ’s 8.15%, and adds TSMC, Korean memory and more ASML. However, Apple and Microsoft together take another 23.22%: IXN is not a pure AI infrastructure fund. It also omits several power and construction beneficiaries.

**QQQ offers more ways for AI to monetize.** Microsoft and Amazon can sell cloud services, Alphabet and Meta can improve ads and products, and software/platform firms can benefit from cheaper inference. The risks differ: heavy spending can depress free cash flow before revenue arrives; custom silicon can help foundries while reducing merchant chip designers’ pricing power; competition can pass productivity gains to customers rather than shareholders.

| Outlook | Positioning judgment | What would change the judgment? |
| --- | --- | --- |
| 1 year | IXN has the stronger direct supplier exposure; no reliable price-return winner. | Orders, utilization, memory pricing, export restrictions and valuation repricing can outweigh revenue growth. |
| 3 years | Conditional IXN preference if capacity scarcity and supplier margins persist. | A capacity glut, customer concentration or slower AI deployment would weaken it; monetization broadening would favor QQQ. |
| 5 years | QQQ is the default for a broader AI growth thesis. | IXN can win if foundry/equipment/memory economics stay unusually strong enough to offset its concentration and fee. |
| 10 years | QQQ for a growth allocation; VOO for broader productivity diffusion. | Market leadership, index rules and sectors will evolve. Durable supplier rents could still favor IXN, but cannot be assumed. |

These are conditional investment judgments, not price targets or modeled return forecasts. A bullish technology outcome can coexist with disappointing stock returns if expectations were already too high. VOO has less pure technology exposure but captures adopters in health care, finance, industrials and other sectors, as well as the largest AI companies.'''),
('valuation-analysis',['fundamentals','valuation'],'''## 7. Earnings growth must overcome the entry price

IXN’s reported P/E is **37.17** and P/B **10.25** as of October 16. QQQ’s September 30 figures are **29.48** and **9.91**, with forward P/E about **25.75**. VOO’s June 30 snapshot is **27.5** and **5.4**. These are different dates and provider methodologies: IXN excludes loss-making constituents and caps individual P/E values at 60. They are context, not a clean same-day valuation ranking.

As an illustration, let IXN’s P/E fall from 37.17 to 30 and QQQ’s from 29.48 to 25 over five years. Those changes create annualized price headwinds of about **4.20% and 3.24%**, respectively. If QQQ’s earnings grow at an assumed 12% a year, IXN needs about **13.33%** earnings growth to match its modeled net return before dividends. Faster industry growth alone does not settle the ETF comparison.

An ETF-level fundamental thesis should track weighted earnings and free cash flow, revisions, return on invested capital, capex intensity, end-customer monetization, competitive supply and the valuation paid. The current evidence does not support a full point-in-time discounted-cash-flow model of every constituent. High ROE can also reflect buybacks and intangible-heavy accounting rather than a new AI advantage.'''),
('bootstrap-analysis',['bootstrap'],'''## 8. Historical resampling is a stress lens, not an AI forecast

The paired bootstrap samples 12-month historical blocks jointly across the three strategies, using **10,000 paths** for each 1-, 3-, 5- and 10-year horizon. All four requested start dates supply separate calibration sets, ending with the last complete month, September 2026. Using complete months avoids treating a partial October as a full observation.

The inception-calibrated historical resampling puts IXN ahead of QQQ in **40.28%, 33.33%, 29.43% and 22.81%** of the 1-, 3-, 5- and 10-year paths. Changing calibration to 1990 brings these shares close to 49%; using 2010 gives roughly 45%, 43%, 41% and 40%. The outcome is highly dependent on which historical regime is assumed repeatable.

**Do not read these as probabilities of IXN winning from today.** Recycled history cannot incorporate a new AI profit pool, changed valuation, novel geopolitical shocks or future index changes. The percentile table reports modeled CAGR dispersion conditional on historical blocks. It complements, rather than validates, the horizon judgments above.'''),
('technical-analysis',['technicals'],'''## 9. Technical conditions: short-term weakness inside longer uptrends

At the October 19 close, all three ETFs were below their 20- and 50-day simple moving averages but above their 200-day averages. IXN’s RSI was **37.3**, QQQ’s **41.1**, and VOO’s **47.0**. Momentum was soft, with negative MACD histograms across the group. An RSI below 50 is weak momentum; none was below the common 30 oversold threshold, and that threshold would not establish a bottom anyway.

IXN was near its lower 20-day Bollinger band at $139.18, with 14-day average true range about **$2.88, or 2.07% of price**, compared with QQQ’s 1.51% and VOO’s 0.92%. Its 20- and 50-day averages near $147.54 and $143.68 provide observable trend references, not guaranteed resistance; its 200-day average near $126.49 is a longer-term reference, not a floor.

IXN’s price ratio to QQQ was 0.1939, below its 50-day ratio average of 0.1977 but above its 200-day average of 0.1865. That describes a recent relative pullback within stronger longer-term relative performance. Execution choices can use these ranges, but a ten-year allocation should be grounded in earnings, valuation, diversification and the ability to hold through losses.'''),
('fee-analysis',['fees','fundamentals','exposures'],'''## 10. Is IXN’s extra 0.19% annual expense worth paying?

IXN’s 0.37% expense ratio is 19 basis points above QQQ’s 0.18% and 34 basis points above VOO’s 0.03%. On $100k that is about **$190 or $340 a year initially**, before market changes. To overcome QQQ’s fee alone, IXN needs about **0.191% extra annual gross return**, using the ratio of their net-of-fee multipliers.

At a purely assumed 8% gross return for every fund, $100k compounds over ten years to about **$208.0k in IXN, $212.0k in QQQ and $215.2k in VOO**. The roughly $4.0k IXN–QQQ gap is the fee difference compounded; the larger real-world determinant will be the portfolios’ different holdings. Actual historical returns already include expenses.

IXN’s incremental TSMC-plus-ASML allocation over QQQ is about 6.54 percentage points. If everything else were identical, that sleeve would need roughly **2.92 percentage points of annual outperformance against the displaced holdings** to cover the fee gap. This is only a simplified hurdle; the actual funds differ in many other positions and weights.

**My judgment:** the fee is reasonable for an intentional global technology and semiconductor allocation, but recent outperformance alone is not enough reason to pay it. For one long-term AI growth ETF, QQQ offers a broader profit-capture mix at lower cost. For a core equity holding, VOO’s sector breadth and lower fee are stronger foundations. IXN can serve as a deliberate tilt when its supplier exposure is precisely what you want.

QQQM, which tracks the same Nasdaq-100 benchmark at a 0.15% fee in this snapshot, is also relevant for a buy-and-hold comparison. QQQ’s trading liquidity can matter for frequent or large trades; compare spreads and trading needs rather than assuming the lower stated fee is the only implementation cost.'''),
('methods-and-sources',['history','exclusion','count','bootstrap'],'''## Methods, source dates and limits

This is a dated research snapshot, **October 19, 2026**, rather than a live price service or a personalized portfolio recommendation. It assumes USD investments, reinvested distributions and no contributions, taxes, trading costs or inflation adjustment. Read the proxy and simulation qualifications beside the related results.

- **Market history:** public adjusted prices plus official IXN daily NAV and distributions. IXN’s final NAV observation is October 16; the October 19 market-price return is the bridge. The monthly NAV reconstruction was checked against 298 issuer monthly observations: the largest absolute discrepancy was **2.75 basis points** in a monthly return. The September 2026 cumulative multiple was 20.0381 reconstructed versus 20.0364 published.
- **Portfolio characteristics:** IXN and QQQ holdings October 16; VOO September 30. Valuation dates are disclosed separately. Share classes, cash and derivatives can cause counts to differ from issuer summary counts. Ticker-matched overlap is not a complete economic-risk map.
- **Historical windows:** 1990, 2000, IXN launch and 2010; all end October 19. Exact prelaunch ETF histories do not exist. FSPTX is a regime proxy, prelaunch QQQ omits dividends, and prelaunch VOO is an index splice. Results before launch cannot be called actual fund returns.
- **Models:** current-weight removal is an assumption sensitivity, not attribution; the 1,200-stock exercise is an unchanged-factor synthetic model; paired resampling repeats historical blocks. Seeds, formulas, raw result rows and the executed notebook are versioned with the report.
- **What remains unmeasured:** point-in-time historical holdings for an exact ex-stock backtest, a validated broad Samsung/Hynix removal, actual 1,200-stock global technology backtesting, security-level valuation forecasts, personal taxes and portfolio suitability.

Primary fund sources: [iShares IXN](https://www.ishares.com/us/products/239750/ishares-global-tech-etf), [Invesco QQQ](https://www.invesco.com/us/en/financial-products/etfs/invesco-qqq-trust-series-1.html), [Vanguard VOO](https://advisors.vanguard.com/investments/products/voo/vanguard-sp-500-etf), and [Vanguard factsheet](https://fund-docs.vanguard.com/F0968.pdf). Operating evidence: [TSMC](https://investor.tsmc.com/english/quarterly-results/2026/q3), [ASML](https://www.investor.asml.com/news-releases/news-release-details/asml-reports-eu11.7-billion-total-net-sales-and-eu5.0-billion-net-income-q3-2026), and [IEA](https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary).

The report’s source menus expose the reviewed rows and caveats. The [GitHub repository](https://github.com/arpit-sidana/investments) contains calculation code, full-precision derived CSVs, the executed notebook and detailed methodology. Provider source documents are linked rather than republished as full articles or PDFs. The [self-contained HTML download](https://arpit-sidana.github.io/investments/downloads/ixn-qqq-voo-2026-10-19.html) can be saved for local reading; updating the research requires a new reviewed version.''')]

(APP/'src/content/report/report-copy.js').write_text('export const sections = '+json.dumps([{'id':i,'queries':qs,'text':t} for i,qs,t in sections],ensure_ascii=False,indent=2)+';\n')
print(json.dumps({'queries':len(Q),'reviewedRows':sum(len(q['rows']) for q in Q.values()),'narrativeSections':len(sections)}))


# A plain Markdown companion remains readable directly in GitHub without JavaScript.
def p(v): return f'{v*100:.2f}%'
def dollars(v): return f'${v:,.0f}'
def mdtable(headers, values):
    return '\n| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in values)+'\n'
companion=['# '+S['title'], '\nResearch cutoff: October 19, 2026. [Interactive report](https://arpit-sidana.github.io/investments/reports/ixn-qqq-voo-2026-10-19/) · [Offline HTML](https://arpit-sidana.github.io/investments/downloads/ixn-qqq-voo-2026-10-19.html)\n']
for id, qs, text in sections:
    companion.append(text)
    if id=='fund-structure': companion.append(mdtable(['Fund','Fee','Equity lines','P/E date'],[[r['fund'],p(r['expense']),r['equity_lines'],r['valuation_date']] for r in fundamentals]))
    if id=='history-analysis':
        companion.append(mdtable(['Start','Fund / proxy','CAGR','Ending $10k','Annualized vol.','Max drawdown'],[[r['window'],r['fund'],p(r['cagr']),dollars(r['ending_10000']),p(r['volatility']),p(r['max_drawdown'])] for r in R['history']]))
        companion.append('![Historical performance and drawdowns](../../etf-research/outputs/history-and-drawdowns.png)')
    if id=='exclusion-analysis':
        companion.append(mdtable(['Start','Weight assumption','Treatment','CAGR','Ending $10k'],[[r['window'],r['weight_sensitivity'],r['method'],p(r['cagr']),dollars(r['ending_10000'])] for r in R['exclusion'] if r['weight_sensitivity']=='Current weights']))
        companion.append('![Current-weight exclusion sensitivity](../../etf-research/outputs/exclusion.png)')
    if id=='diversification-analysis':
        companion.append(mdtable(['Fund','Effective holdings','Top 3','Top 10 issuers'],[[r['fund'],f"{r['effective_stocks']:.2f}",p(r['top3']),p(r['top10_issuers'])] for r in R['concentration']]))
        companion.append(mdtable(['Start','Synthetic 130 vol.','Synthetic 1,200 vol.','QQQ / proxy vol.','VOO / proxy vol.'],[[r['window'],p(r['model_130_stock_vol']),p(r['model_1200_stock_vol']),p(r['qqq_monthly_vol']),p(r['voo_monthly_vol'])] for r in Q['count']['rows']]))
    if id=='bootstrap-analysis': companion.append(mdtable(['Calibration start','Years','IXN win share','IXN median CAGR','IXN 5th percentile','IXN 95th percentile'],[[r['calibration_window'],r['horizon_years'],p(r['ixn_beats_qqq_fraction']),p(r['median_cagr']),p(r['p05_cagr']),p(r['p95_cagr'])] for r in R['bootstrap'] if r['fund']=='IXN*']))
    if id=='technical-analysis': companion.append(mdtable(['Fund','Close','SMA 20','SMA 50','SMA 200','RSI 14'],[[r['fund']]+[f"{r[k]:.2f}" for k in ['close','sma20','sma50','sma200','rsi14']] for r in R['technicals']]))
    if id=='fee-analysis': companion.append(mdtable(['Fund','Annual fee','10-year ending $100k'],[[r['fund'],p(r['fee']),dollars(r['ending_100000'])] for r in R['fees'] if r['years']==10]))
(APP/'REPORT.md').write_text('\n\n'.join(companion)+'\n')
