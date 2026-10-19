from pathlib import Path
import os,sys,json,zipfile
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'outputs'
sys.path.insert(0,str(ROOT/'vendor'))
os.environ['MPLCONFIGDIR']=str(ROOT/'outputs'/'mpl-cache')
import nbformat
from nbclient import NotebookClient

METHODS='''# ETF comparison: IXN, QQQ and VOO

## Summary
QQQ leads IXN over the common history from IXN's November 12, 2001 launch. IXN leads over recent 1-, 3-, 5- and 10-year periods. IXN has greater global technology and semiconductor exposure, but substantially greater weight concentration than either QQQ or VOO.

## Context & Methods
All retrospective investment windows finish October 19, 2026. USD lump sum, dividends and capital gains reinvested, no contributions, taxes, trading costs or inflation adjustment. ETF returns already reflect historical fund expenses. We do not subtract current expenses again.

### Key assumptions and limitations
- IXN: official daily NAV and ex-distributions from inception to October 16; October 19 is appended using the observed market-price return. This last-day bridge is an estimate of NAV performance. NAV is adjusted for splits in the issuer download.
- VOO: S&P 500 total-return index minus an assumed 0.03% annual expense before its first public daily price, September 9, 2010, then actual VOO adjusted prices. This is a hypothetical index/ETF splice, not actual prelaunch VOO. Its fund inception was September 7.
- IXN before launch: Fidelity Select Technology (FSPTX), an actively managed technology mutual fund. It is a **regime proxy, not reconstructed IXN**, and does not reproduce global weights, classifications or costs.
- QQQ before March 10, 1999: Nasdaq-100 **price** index minus an assumed 0.20% annual expense. Prelaunch dividends are unavailable in these snapshots, so that segment understates a hypothetical total-return Nasdaq-100 portfolio. Do not call the 1990 comparison a total-return ETF backtest. A 0–0.5% assumed prelaunch dividend yield is examined separately.
- January 1 windows begin with the preceding available year-end close. IXN inception begins with the November 12 closing NAV. Returns are close-to-close.
- The strategy and stock-count models replay every requested start window. For 1990/2000, the exclusion changes apply **only after IXN launch**; the prelaunch FSPTX segment remains the same.
- Exclusion: the current 4.68% TSMC and 2.53% ASML weights are held constant and rebalanced monthly. Their USD listed-share/ADR adjusted returns proxy the local shares IXN owns. The residual basket is inferred algebraically from IXN. Actual historical weights, index constituents, taxes, local/ADR premia and fair-value adjustments are unavailable. It is an assumption sensitivity, **not historical stock attribution or an investable replica**. Exclusion removes losses as well as gains. A separate zero-return-cash variant keeps the unremoved sleeve's original exposure. The 0.37% annual fee is retained approximately in the reallocation model; exact historical fee schedules are unavailable.
- Count experiment: each observed monthly technology path is treated as a common factor. Add zero-mean independent individual-stock residuals with assumed 30% annual volatility, average over N equally weighted stocks, and replay 5,000 seeded paths. This isolates the consequence of changing stock count under an unchanged factor path. It is **not a portfolio of actual 1,200 companies**, and its 5th–95th percentiles are conditional model dispersion, not market-risk confidence bounds.
- Equicorrelation experiment assumes every stock has 35% annual volatility and common pairwise correlations of 0.2, 0.6 or 0.8; these are illustrative assumptions, not estimated correlations.
- Bootstrap: 10,000 paired paths, 12-month moving blocks, non-wrapping block starts; calibrations begin at each requested historical window and end with the last complete month, September 2026. Forward horizons are 1, 3, 5 and 10 years. Repeated historical blocks preserve some joint behavior but do not predict AI, valuation changes, structural breaks or geopolitical disasters. Block sampling is not uniform weighting of every individual endpoint month.
- Volatility uses daily simple returns and sqrt(252); drawdown uses daily wealth. Sharpe uses a fixed 3% annual hurdle for comparability, not realized T-bill returns. Overlapping rolling windows are not independent observations and win rates are not forecast probabilities.
- Concentration uses long equity positions only, normalized to 100%; duplicate issuer classes are combined (Alphabet, Samsung). IXN and QQQ holdings are October 16, VOO September 30. Holdings counts can differ from issuer accounting counts because cash, futures and share classes differ. HHI effective stock count = 1/sum(weight squared). It measures weight concentration, not independent risk factors. Stock overlap is matched by ticker with explicit mappings, not full economic/supply-chain overlap.
- Valuation and sector snapshots carry their own dates and provider definitions. IXN uses GICS and QQQ uses ICB, so displayed technology weights are not identical classification universes. IXN's P/E convention excludes loss-makers and caps individual P/E values at 60 in its factsheet definition.

## Data
`../sources/fetch_log.json` records public endpoints, source filenames and retrieval timestamps. `../fetch_data.py` downloads snapshots; `../analyze.py` is the calculation source. All CSV files here are derived from those snapshots. Data requires independent verification before trading; conclusions are research judgments and do not incorporate a personal portfolio or tax situation.
'''

def cell(code):return nbformat.v4.new_code_cell(code)
nb=nbformat.v4.new_notebook()
nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}}
nb.cells=[nbformat.v4.new_markdown_cell(METHODS),cell('''import sys, os
from pathlib import Path
root = Path.cwd().parent
sys.path.insert(0, str(root / 'vendor'))
sys.path.insert(0, str(root))
os.environ['MPLCONFIGDIR'] = str(root / 'outputs' / 'mpl-cache')
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.display import display, Image
import analyze
results = analyze.run()
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,'figure.facecolor':'white'})
colors = ['#2d5b89','#b16a27','#687f45']
'''),nbformat.v4.new_markdown_cell('## Results\n### Returns and risk\nAsterisks identify series that use a prelaunch proxy where needed. The pre-2001 technology proxy must not be interpreted as actual IXN.'),cell('''history = pd.DataFrame(results['history'])
display(history[['window','fund','cagr','ending_10000','volatility','max_drawdown','dd_peak','dd_trough','recovered']].round(4))
display(pd.DataFrame(results['trailing'])[['horizon_years','fund','cagr','volatility','max_drawdown']].round(4))
'''),cell('''levels=analyze.LEVELS.loc[analyze.LAUNCH:]
fig, axs=plt.subplots(2,1,figsize=(11,8),sharex=True,gridspec_kw={'height_ratios':[1.4,1]})
for i,n in enumerate(levels):
    wealth=10000*levels[n]/levels[n].iloc[0]
    axs[0].plot(wealth.index,wealth,color=colors[i],label=analyze.SHORT[n],linestyle=['-','--',':'][i],lw=1.9)
    axs[1].plot(wealth.index,(wealth/wealth.cummax()-1)*100,color=colors[i],linestyle=['-','--',':'][i],lw=1.5)
axs[0].set_yscale('log');axs[0].set_ylabel('USD, logarithmic scale');axs[0].set_title('$10,000 from November 12, 2001 to October 19, 2026');axs[0].legend()
axs[1].set_ylabel('Drawdown (%)');axs[1].set_xlabel('Date');axs[1].set_xlim(levels.index[0],levels.index[-1])
fig.tight_layout();fig.savefig('history-and-drawdowns.png',dpi=170);display(Image(filename='history-and-drawdowns.png'));plt.close(fig)
'''),nbformat.v4.new_markdown_cell('### Current concentration\nMore names do not imply more equal weight or less exposure to a shared economic shock. VOO holdings have a different snapshot date.'),cell('''display(pd.DataFrame(results['concentration']).round(4))
display(pd.DataFrame(results['overlap']).T.round(4))
print('Daily-return correlations since launch:')
display(pd.DataFrame(results['risk']['IXN inception']['correlations']).round(3))
'''),nbformat.v4.new_markdown_cell('### TSMC and ASML exclusion sensitivity\nConstant modern weights and USD ADR/listed-share proxies. This does not establish the contribution of actual historical holdings. The same prelaunch technology proxy is retained for early starts.'),cell('''ex = pd.DataFrame(results['exclusion'])
display(ex.query("weight_sensitivity == 'Current weights'")[['window','method','cagr','ending_10000']].round(4))
display(ex.query("window == 'IXN inception'")[['weight_sensitivity','method','cagr','ending_10000']].round(4))
p=pd.read_csv('exclusion_monthly_paths.csv',index_col='date',parse_dates=True)*10000
fig,ax=plt.subplots(figsize=(11,4.5))
for i,n in enumerate(p):ax.plot(p.index,p[n],label=['IXN observed','IXN excluding TSMC / ASML model','QQQ'][i],color=[colors[0],'#596a7b',colors[1]][i],linestyle=['-','--',':'][i],lw=1.8)
ax.set_title('Fixed-weight exclusion model: $10,000 from IXN launch');ax.set_ylabel('USD');ax.set_xlim(p.index[0],p.index[-1]);ax.legend();fig.tight_layout();fig.savefig('exclusion.png',dpi=170);display(Image(filename='exclusion.png'));plt.close(fig)
'''),nbformat.v4.new_markdown_cell('### Hypothetical stock-count experiment\nCommon observed technology path plus assumed independent individual-stock noise. Bands represent only residual dispersion conditional on the observed common path.'),cell('''display(pd.DataFrame(results['diversification']).round(4))
theory=pd.DataFrame(results['equicorrelation'])
display(theory.round(5))
fig,ax=plt.subplots(figsize=(9,4.5))
for j,rho in enumerate([.2,.6,.8]):
    n=np.arange(20,1201)
    ax.plot(n,35*np.sqrt(rho+(1-rho)/n),color=colors[j],label=f'Pairwise correlation {rho}',linestyle=['-','--',':'][j])
ax.set_xlabel('Equally weighted stock count');ax.set_ylabel('Annual volatility (%)');ax.set_title('Illustrative stock-count effect; each stock has 35% volatility');ax.legend();fig.tight_layout();fig.savefig('diversification.png',dpi=170);display(Image(filename='diversification.png'));plt.close(fig)
'''),nbformat.v4.new_markdown_cell('### Rolling observations and paired historical bootstrap\nAll calibration windows are in the CSV. The table below highlights inception calibration. These are backward-looking distributions, not AI return forecasts.'),cell('''display(pd.DataFrame(results['rolling']).round(4))
boot=pd.DataFrame(results['bootstrap'])
display(boot.query("calibration_window == 'IXN inception'").round(4))
'''),nbformat.v4.new_markdown_cell('### Technical and fee calculations'),cell('''tech=pd.DataFrame(results['technicals'])
display(tech[['fund','asof','close','sma20','sma50','sma200','rsi14','macd','signal','histogram','atr14','realized_vol63']].round(3))
display(pd.DataFrame(results['fees']).round(4))
'''),nbformat.v4.new_markdown_cell('### Validation\nThe issuer reconciliation covers all 298 comparable monthly observations. Small differences remain between daily NAV arithmetic and the separately published monthly series. These are retained rather than forced to match.'),cell('''print(results['reconciliation'])
assert analyze.LEVELS.loc['1989-12-29':].notna().all().all()
assert analyze.LEVELS.index.is_unique
assert analyze.LEVELS.index[-1] == pd.Timestamp('2026-10-19')
assert all(x['effective_stocks'] <= x['issuers'] for x in results['concentration'])
assert all(0 <= x['ixn_beats_qqq_fraction'] <= 1 for x in results['bootstrap'])
assert results['reconciliation']['largest_abs_monthly_error_bp'] < 3
assert abs(float(analyze.IXN_NAV.loc['2026-09-30']) - 20.0364) < .003
checks={'daily_dates_unique':True,'all_series_end':'2026-10-19','no_missing_analysis_levels':True,'max_monthly_nav_discrepancy_bp':results['reconciliation']['largest_abs_monthly_error_bp'],'official_sept2026_cumulative_wealth_multiple':20.0364,'reconstructed_multiple':float(analyze.IXN_NAV.loc['2026-09-30'])}
Path('validation.json').write_text(__import__('json').dumps(checks,indent=2))
display(checks)
'''),nbformat.v4.new_markdown_cell('## Takeaways\nQQQ has the stronger full common-history record and a lower fee. IXN offers a more concentrated global technology/supplier tilt, including direct TSMC and Korean semiconductor exposure. VOO has the broadest sector coverage and lowest fee. None of these historical or synthetic experiments proves which fund will outperform in the AI economy. Exact prelaunch IXN and exact historical constituent removal remain unavailable.\n\nThe 1990 results compare proxies; they are unsuitable as a precise ranking of today’s funds. The 2000 window makes the cost of valuation and technology regime risk visible.')]

path=OUT/'etf-comparison.ipynb';nbformat.write(nb,path);nbformat.validate(nb)
client=NotebookClient(nb,timeout=240,kernel_name='python3',resources={'metadata':{'path':str(OUT)}})
client.execute(cwd=str(OUT),env={**os.environ,'PYTHONPATH':str(ROOT/'vendor')})
nbformat.write(nb,path);nbformat.validate(nb)
html=['<!doctype html><html><head><meta charset="utf-8"><title>ETF calculations preview</title><style>body{font:16px system-ui;max-width:1080px;margin:40px auto;padding:0 24px;color:#202c36}pre{white-space:pre-wrap;background:#f3f5f7;padding:15px;overflow-wrap:anywhere}table{border-collapse:collapse;font-size:13px}th,td{padding:6px;border-bottom:1px solid #ddd}img{max-width:100%}</style></head><body><h1>ETF comparison: calculations and figures</h1>']
import html as h
for c in nb.cells:
    if c.cell_type=='markdown':html.append('<pre>'+h.escape(c.source)+'</pre>')
    else:
        html.append('<details><summary>Calculation code</summary><pre>'+h.escape(c.source)+'</pre></details>')
        for o in c.get('outputs',[]):
            if 'data' in o:
                if 'image/png' in o.data:html.append('<img src="data:image/png;base64,'+o.data['image/png']+'">')
                elif 'text/html' in o.data:html.append(o.data['text/html'])
                elif 'text/plain' in o.data:html.append('<pre>'+h.escape(o.data['text/plain'])+'</pre>')
            elif o.output_type=='stream':html.append('<pre>'+h.escape(o.text)+'</pre>')
html.append('</body></html>');(OUT/'notebook-preview.html').write_text('\n'.join(html))
(OUT/'METHODS.md').write_text(METHODS)
print('Executed notebook, figures, validation, and preview:',path)
