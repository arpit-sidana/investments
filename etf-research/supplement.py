from pathlib import Path
import json,sys,ast
import numpy as np
import pandas as pd
import analyze

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'outputs'
R=json.loads((OUT/'results.json').read_text())

# Keep the experiment comparison on the same monthly return frequency.
rows=[]
for name,start in analyze.WINDOWS.items():
    z=analyze.LEVELS.loc[start:];m=pd.concat([z.head(1),z.resample('ME').last()]);m=m[~m.index.duplicated()].sort_index()
    vol=m.pct_change(fill_method=None).dropna().std()*np.sqrt(12)
    d={x['stocks']:x for x in R['diversification'] if x['window']==name}
    rows.append({'window':name,'actual_technology_monthly_vol':float(vol.iloc[0]),'model_130_stock_vol':d[130]['median_volatility'],'model_1200_stock_vol':d[1200]['median_volatility'],'qqq_monthly_vol':float(vol.iloc[1]),'voo_monthly_vol':float(vol.iloc[2])})
pd.DataFrame(rows).to_csv(OUT/'matched_frequency_diversification.csv',index=False)

# Sensitivity to omitted dividends in the pre-QQQ price-index segment.
before_launch_years=(pd.Timestamp('1999-03-10')-pd.Timestamp('1989-12-29')).days/365.2425
total_years=(analyze.END-pd.Timestamp('1989-12-29')).days/365.2425
base=next(x for x in R['history'] if x['window']=='1990' and x['fund']=='QQQ*')
dividend_sensitivity=[]
for annual_yield in [0,.0025,.005]:
    terminal=base['ending_10000']*(1+annual_yield)**before_launch_years
    dividend_sensitivity.append({'assumed_prelaunch_dividend_yield':annual_yield,'ending_10000':terminal,'cagr':(terminal/10000)**(1/total_years)-1})
pd.DataFrame(dividend_sensitivity).to_csv(OUT/'prelaunch_dividend_sensitivity.csv',index=False)

assumptions=[]
qqqfee=.0018;ixnfee=.0037
for horizon in [1,3,5,10]:
    ixn_terminal=30.;qqq_terminal=25.;ixn_start=37.17;qqq_start=29.480945
    ixn_pe_drag=(ixn_terminal/ixn_start)**(1/horizon)-1
    qqq_pe_drag=(qqq_terminal/qqq_start)**(1/horizon)-1
    ixn_required=1.12*((qqq_terminal/qqq_start)/(ixn_terminal/ixn_start))**(1/horizon)*(1-qqqfee)/(1-ixnfee)-1
    assumptions.append({'years':horizon,'IXN_start_PE_dated_20261016':ixn_start,'QQQ_start_PE_dated_20260930':qqq_start,'IXN_terminal_PE_assumption':ixn_terminal,'QQQ_terminal_PE_assumption':qqq_terminal,'QQQ_EPS_growth_assumption':.12,'IXN_required_EPS_growth_excluding_dividends':ixn_required,'IXN_PE_annualized_price_drag':ixn_pe_drag,'QQQ_PE_annualized_price_drag':qqq_pe_drag})
pd.DataFrame(assumptions).to_csv(OUT/'valuation_hurdle_sensitivity.csv',index=False)

q=analyze.HOLD['QQQ'].set_index('ticker').weight; i=analyze.HOLD['IXN'].set_index('ticker').weight;v=analyze.HOLD['VOO'].set_index('ticker').weight
exposures=[]
for label,tickers in [('Nvidia',['NVDA']),('Apple',['AAPL']),('Microsoft',['MSFT']),('TSMC',['2330']),('ASML',['ASML']),('Samsung common and preferred',['005930','005935']),('SK Hynix',['000660']),('Amazon',['AMZN']),('Alphabet both classes',['GOOG','GOOGL']),('Meta',['META']),('Oracle',['ORCL']),('Vertiv',['VRT']),('Eaton',['ETN']),('GE Vernova',['GEV'])]:
    exposures.append({'company':label,'IXN':float(i.reindex(tickers,fill_value=0).sum()),'QQQ':float(q.reindex(tickers,fill_value=0).sum()),'VOO':float(v.reindex(tickers,fill_value=0).sum())})
pd.DataFrame(exposures).to_csv(OUT/'selected_ai_exposures.csv',index=False)

# Native chart: quarter ends plus inception/current endpoint; exact start/end retained.
z=analyze.LEVELS.loc[analyze.LAUNCH:]; idx=z.resample('QE').last().index
idx=pd.DatetimeIndex(sorted(set([z.index[0],z.index[-1]]+[t for t in idx if t<=z.index[-1]])))
sample=z.reindex(z.index.union(idx)).sort_index().ffill().loc[idx]
wealth=sample/z.iloc[0]*10000
chartrows=[]
for t,row in wealth.iterrows():
    for name,val in row.items():chartrows.append({'date':str(t.date()),'fund':{'IXN*':'IXN','QQQ*':'QQQ','VOO*':'VOO / prelaunch index'}[analyze.SHORT[name]],'wealth_usd':round(float(val),2)})
source={'label':'Issuer NAV and public adjusted-price histories','links':[{'label':'iShares IXN','href':'https://www.ishares.com/us/products/239750/ishares-global-tech-etf'},{'label':'QQQ price history','href':'https://finance.yahoo.com/quote/QQQ/history/'}],'files':[{'label':'daily_total_return_levels.csv'}],'caveats':['VOO uses a hypothetical S&P 500 total-return index less 0.03% expense before September 9, 2010.','IXN uses daily NAV through October 16 and its October 19 market return as the final-day bridge.','USD, reinvested distributions, pre-tax; no contributions, inflation adjustment or trading costs.'], 'filters':['Start: November 12, 2001','End: October 19, 2026']}
chart={'schemaVersion':1,'id':'etf-common-history','title':'Growth of $10,000 since IXN launched','description':'November 12, 2001–October 19, 2026 · reinvested distributions · VOO uses a prelaunch index proxy','chart':{'type':'line','x':'date','y':'wealth_usd','series':'fund','showXAxisLabel':False,'yLabel':'Portfolio value (USD)','yStartAtZero':True},'rows':chartrows,'source':source,'theme':'codex-classic','height':380}
(OUT/'inline-history.json').write_text(json.dumps(chart,indent=2))
receipt={'schemaVersion':1,'items':[{'id':'common-history','title':'Growth since IXN launch','queries':[{'id':'history-series','source':source,'reportingPeriod':'November 12, 2001–October 19, 2026','rows':chartrows[-3:],'columns':['date','fund','wealth_usd'],'preview':{'kind':'partial','note':'Final values only; the chart contains quarterly samples of the daily wealth series.'}}]}]}
(OUT/'history-sources.json').write_text(json.dumps(receipt,indent=2))

src=Path(ROOT/'analyze.py').read_text();tree=ast.parse(src)
functions={n.name:ast.get_source_segment(src,n) for n in tree.body if isinstance(n,ast.FunctionDef)}
def finding(identity,title,files,caveats,data=None,code=None,links=None):
    query={'id':identity+'-calculation','source':{'label':title,'files':[{'label':f} for f in files],'caveats':caveats}}
    if links:query['source']['links']=[{'label':a,'href':b} for a,b in links]
    if data:
        query.update({'rows':data,'columns':list(data[0]),'preview':{'kind':'aggregate','note':'Derived summary from the saved snapshots.'}})
    if code:query['methods']=[{'language':'python','code':code}]
    return {'id':identity,'title':title,'queries':[query]}

items=[
 finding('extended','Extended historical windows and risk',['historical_metrics.csv','rolling_windows.csv','risk_comparisons.json'],['1990 and 2000 use FSPTX as a prelaunch technology regime proxy, not reconstructed IXN.','Pre-March 1999 Nasdaq-100 price returns omit dividends and assume a 0.20% expense.','VOO uses an S&P 500 total-return index proxy less 0.03% fee before September 2010.','Rolling observations overlap and are not independent.'],[{k:x[k] for k in ['window','fund','cagr','ending_10000','volatility','max_drawdown']} for x in R['history']],functions['metrics']),
 finding('exclusion','TSMC and ASML fixed-weight sensitivity',['exclusion_sensitivity.csv','exclusion_monthly_paths.csv'],['Current weights of 4.68% and 2.53% are held constant; historical constituent weights are unavailable.','USD ADR/listed-share returns proxy the local securities. This is not exact historical attribution or an investable replica.','The 1990/2000 variants retain the same prelaunch technology proxy and change the path only after IXN launch.'],[{k:x[k] for k in ['window','method','cagr','ending_10000']} for x in R['exclusion'] if x['weight_sensitivity']=='Current weights'],functions['exclusion']),
 finding('diversification','Weight concentration and stock-count experiments',['concentration.csv','factor_replay_diversification.csv','equicorrelation_diversification.csv'],['Holdings are October 16 for IXN/QQQ and September 30 for VOO. Long equity weights are normalized; issuer share classes are combined.','HHI effective stock count measures weight concentration, not independent economic risk.','The 1,200-stock model is synthetic: replay observed tech monthly returns plus independent 30% annual-volatility stock residuals; 5,000 paths.'],R['concentration'],functions['diversification_experiment'],[('IXN holdings','https://www.ishares.com/us/products/239750/ishares-global-tech-etf/latest-holdings.csv'),('Vanguard portfolio','https://investor.vanguard.com/irr/funds/profile/VOO-AdditionalFundData'),('Invesco QQQ','https://www.invesco.com/qqq-etf/en/about.html')]),
 finding('bootstrap','Paired historical block simulation',['paired_block_bootstrap.csv'],['10,000 paired paths with 12-month moving blocks. Calibration ends September 2026, the last full month.','Historical bootstrap distributions are not forward market probabilities or an AI earnings model.','Early calibrations inherit the prelaunch proxy limitations.'],[x for x in R['bootstrap'] if x['calibration_window']=='IXN inception'],functions['bootstrap']),
 finding('technical','Technical and fee calculations',['technicals.json','fee_compounding.csv','valuation_hurdle_sensitivity.csv'],['Technicals use October 19 closing prices; they describe trends, not investment value.','Fee example assumes identical 8% gross annual returns and constant current fee rates.','Valuation compression scenarios are assumptions, not forecasts; issuer P/E dates and conventions differ.'],[{k:x[k] for k in ['fund','asof','close','sma20','sma50','sma200','rsi14','histogram','atr14']} for x in R['technicals']],functions['fee_math']),
 finding('fundamental','Fund structures and AI exposure',['ixn_page.html','qqq_api_stats.json','qqq_api_sector.json','voo_factsheet.pdf','selected_ai_exposures.csv'],['IXN uses GICS and QQQ uses ICB; technology-sector weights are not directly identical classifications.','P/E and P/B snapshots have different dates and provider calculation conventions.','AI horizon preferences are research judgments, not established future returns.'],exposures,None,[('iShares IXN','https://www.ishares.com/us/products/239750/ishares-global-tech-etf'),('Invesco QQQ','https://www.invesco.com/qqq-etf/en/about.html'),('Vanguard factsheet','https://fund-docs.vanguard.com/F0968.pdf'),('TSMC Q3 results','https://investor.tsmc.com/english/quarterly-results/2026/q3'),('ASML Q3 results','https://www.investor.asml.com/news-releases/news-release-details/asml-reports-eu11.7-billion-total-net-sales-and-eu5.0-billion-net-income-q3-2026'),('IEA energy and AI','https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary')])
]
(OUT/'additional-sources.json').write_text(json.dumps({'schemaVersion':1,'items':items},indent=2))
print('Chart payload, source receipts and additional comparison tables saved.')
