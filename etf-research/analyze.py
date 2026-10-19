"""Reproduce the ETF comparison from saved public-source snapshots. No network calls."""
from pathlib import Path
import json, math, io
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'sources'; OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
END=pd.Timestamp('2026-10-19'); LAUNCH=pd.Timestamp('2001-11-12'); SEED=20261019

def read_price(symbol):
    d=json.loads((SRC/('price_'+symbol+'.json')).read_text())['chart']['result'][0]
    ix=pd.to_datetime(d['timestamp'],unit='s',utc=True).tz_convert(d['meta']['exchangeTimezoneName']).tz_localize(None).normalize()
    x=pd.DataFrame(d['indicators']['quote'][0],index=ix)
    x['adjusted']=d['indicators']['adjclose'][0]['adjclose']
    return x.loc[~x.index.duplicated()].loc[:END].dropna(subset=['close','adjusted'])

P={s:read_price(s) for s in ['IXN','QQQ','VOO','SPY','FSPTX','VFINX','TSM','ASML','NDX','SP500TR','GSPC','IRX']}
CAL=P['GSPC'].index

def series(s):return P[s].adjusted.reindex(CAL).ffill()

def splice(before,after,at):
    at=pd.Timestamp(at)
    out=before.copy(); out.loc[at:]=after.loc[at:]/after.loc[at]*before.loc[at]
    return out

def build_levels():
    rows=json.loads((SRC/'ixn_sheet_Historical.json').read_text())
    d=pd.DataFrame(rows[1:],columns=rows[0]); d.index=pd.to_datetime(d['As Of']); d=d.sort_index()
    nav=pd.to_numeric(d['NAV per Share']); div=pd.to_numeric(d['Ex-Dividends'].replace('--','0'))
    r=(nav+div)/nav.shift()-1
    ixn=(1+r.fillna(0)).cumprod()
    # Public NAV feed ends Oct 16; append the actual ETF market return on Oct 19.
    bridge=P['IXN'].adjusted.loc[END]/P['IXN'].adjusted.loc[ixn.index[-1]]
    ixn.loc[END]=ixn.iloc[-1]*bridge
    ixn=ixn.reindex(CAL).ffill()
    tech=splice(series('FSPTX'),ixn,LAUNCH)
    ndx=series('NDX')*np.exp(-.002*(CAL-CAL[0]).days/365.2425)
    qqq=splice(ndx,series('QQQ'),'1999-03-10')
    sp=series('SP500TR')*np.exp(-.0003*(CAL-CAL[0]).days/365.2425)
    voo=splice(sp,series('VOO'),'2010-09-09')
    levels=pd.DataFrame({'IXN / prelaunch FSPTX':tech,'QQQ / prelaunch NDX price':qqq,'VOO / prelaunch S&P TR':voo})
    levels=levels.loc['1989-12-29':]
    levels.to_csv(OUT/'daily_total_return_levels.csv',index_label='date')
    # Independent comparison to issuer monthly returns and standardized calendar returns.
    official=json.loads((SRC/'ixn_sheet_Performance.json').read_text())
    checks=[]
    for row in official[6:]:
        if len(row)!=2 or row[1]=='--':continue
        t=pd.to_datetime(row[0]); prev=t-pd.offsets.MonthEnd(1)
        if t>nav.index[-1] or prev<nav.index[0]:continue
        got=ixn.loc[:t].iloc[-1]/ixn.loc[:prev].iloc[-1]-1
        checks.append({'month':str(t.date()),'computed':got,'issuer':float(row[1])/100,'difference_bp':(got-float(row[1])/100)*10000})
    pd.DataFrame(checks).to_csv(OUT/'ixn_nav_reconciliation.csv',index=False)
    return levels,ixn,{'months_checked':len(checks),'largest_abs_monthly_error_bp':max(abs(z['difference_bp']) for z in checks),'nav_bridge_date':'2026-10-19','nav_bridge_return':float(bridge-1)}

LEVELS,IXN_NAV,RECON=build_levels()
SHORT={'IXN / prelaunch FSPTX':'IXN*','QQQ / prelaunch NDX price':'QQQ*','VOO / prelaunch S&P TR':'VOO*'}
WINDOWS={'1990':'1989-12-29','2000':'1999-12-31','IXN inception':'2001-11-12','2010':'2009-12-31'}

def metrics(level):
    r=level.pct_change(fill_method=None).dropna(); yr=(level.index[-1]-level.index[0]).days/365.2425
    dd=level/level.cummax()-1; trough=dd.idxmin(); peak=level.loc[:trough].idxmax()
    rec=level.loc[trough:]; rec=rec[rec>=level.loc[peak]]
    return {'start':str(level.index[0].date()),'end':str(level.index[-1].date()),'years':yr,
            'cagr':float((level.iloc[-1]/level.iloc[0])**(1/yr)-1),'total_return':float(level.iloc[-1]/level.iloc[0]-1),
            'ending_10000':float(10000*level.iloc[-1]/level.iloc[0]),'volatility':float(r.std(ddof=1)*np.sqrt(252)),
            'max_drawdown':float(dd.min()),'dd_peak':str(peak.date()),'dd_trough':str(trough.date()),
            'recovered':str(rec.index[0].date()) if len(rec) else None,
            'sharpe_fixed_3pct':float((r.mean()*252-.03)/(r.std(ddof=1)*np.sqrt(252))),
            'daily_cvar95':float(r[r<=r.quantile(.05)].mean())}

def historical():
    allrows=[]; risks={}; rolling=[]
    for label,start in WINDOWS.items():
        z=LEVELS.loc[start:]
        for name in z:
            m=metrics(z[name]);m.update({'window':label,'fund':SHORT[name]});allrows.append(m)
        ret=z.pct_change(fill_method=None).dropna();cov=ret.cov();corr=ret.corr();eig=np.linalg.eigvalsh(corr)
        risks[label]={'correlations':corr.to_dict(),'effective_independent_funds':float(eig.sum()**2/(eig**2).sum()),
           'beta_vs_sp500':{SHORT[n]:float(cov.loc[n,z.columns[2]]/cov.loc[z.columns[2],z.columns[2]]) for n in z},
           'tracking_error_ixn_qqq':float((ret.iloc[:,0]-ret.iloc[:,1]).std()*np.sqrt(252))}
    m=LEVELS.loc[LAUNCH:].resample('ME').last()
    # Complete month-end observations only; exclude October partial month from rolling win rates.
    m=m.loc[:'2026-09-30']
    for y in [1,3,5,10]:
        rr=m.pct_change(12*y,fill_method=None).dropna();rel=(1+rr.iloc[:,0])/(1+rr.iloc[:,1])
        for i,n in enumerate(rr):
            ar=(1+rr[n])**(1/y)-1
            rolling.append({'years':y,'fund':SHORT[n],'observations':len(rr),'median_cagr':float(ar.median()),'worst_cagr':float(ar.min()),'best_cagr':float(ar.max()),'ixn_beats_qqq_fraction':float((rel>1).mean())})
    # Trailing 1,3,5,10-year common-date returns, Jan1 YTD, and selected historical regimes.
    trailing=[]; regimes=[]
    for y in [1,3,5,10]:
        t=END-pd.DateOffset(years=y)
        for n in LEVELS:
            z=LEVELS[n].loc[:t].tail(1).to_frame().join(LEVELS[n].loc[t+pd.Timedelta(days=1):].rename('rest'),how='outer') if False else LEVELS[n].loc[LEVELS.index[LEVELS.index<=t][-1]:]
            trailing.append({'horizon_years':y,'fund':SHORT[n],**metrics(z)})
    for a,b in [('1999-12-31','2002-12-31'),('2007-12-31','2008-12-31'),('2019-12-31','2020-12-31'),('2021-12-31','2022-12-30'),('2022-12-30','2023-12-29'),('2025-12-31','2026-10-19')]:
        for n in LEVELS:
            z=LEVELS[n].loc[a:b];regimes.append({'period':a+' to '+b,'fund':SHORT[n],'return':float(z.iloc[-1]/z.iloc[0]-1)})
    pd.DataFrame(allrows).to_csv(OUT/'historical_metrics.csv',index=False)
    pd.DataFrame(trailing).to_csv(OUT/'trailing_metrics.csv',index=False)
    pd.DataFrame(regimes).to_csv(OUT/'regime_returns.csv',index=False)
    pd.DataFrame(rolling).to_csv(OUT/'rolling_windows.csv',index=False)
    (OUT/'risk_comparisons.json').write_text(json.dumps(risks,indent=2))
    return allrows,risks,rolling,trailing

def holdings():
    text=(SRC/'ixn_holdings.csv').read_text(encoding='utf-8-sig'); lines=text.splitlines();j=next(i for i,l in enumerate(lines) if l.startswith('Ticker,'))
    a=pd.read_csv(io.StringIO('\n'.join(lines[j:])),dtype=str,on_bad_lines='skip');a=a[a['Asset Class']=='Equity'].copy()
    a['weight']=pd.to_numeric(a['Weight (%)'])/100;a['ticker']=a.Ticker;a['issuer']=a.Name
    a.loc[a.ticker.isin(['005930','005935']),'issuer']='SAMSUNG ELECTRONICS'
    d=json.loads((SRC/'qqq_api_holdings.json').read_text());b=pd.DataFrame(d['holdings']);b=b[b.securityTypeName.str.contains('Common Stock|Depository Receipt')].copy();b['weight']=b.percentageOfTotalNetAssets/100;b['issuer']=b.issuerName
    b.loc[b.ticker.isin(['GOOG','GOOGL']),'issuer']='Alphabet Inc'
    h=json.loads((SRC/'voo_actual_holdings.json').read_text())['holdingDetails'];c=pd.DataFrame(h['equityHoldings']);c['weight']=c.marketValuePercentage.str.rstrip('%').astype(float)/100;c['ticker']=c.ticker;c['issuer']=c.securityLongDescription
    c.loc[c.ticker.isin(['GOOG','GOOGL']),'issuer']='Alphabet Inc'
    result=[]; allfunds={'IXN':a,'QQQ':b,'VOO':c}
    for name,df in allfunds.items():
        df[['ticker','issuer','weight']].to_csv(OUT/(name.lower()+'_equity_weights.csv'),index=False)
        w=df.groupby('issuer').weight.sum();w=w/w.sum();ordered=w.sort_values(ascending=False)
        result.append({'fund':name,'snapshot_date':'2026-09-30' if name=='VOO' else '2026-10-16','equity_lines':len(df),'issuers':len(w),'equity_weight_total':float(df.weight.sum()),'hhi':float((w*w).sum()),'effective_stocks':float(1/(w*w).sum()),'top3':float(ordered.head(3).sum()),'top10_issuers':float(ordered.head(10).sum()),'top10_lines':float(df.weight.sort_values(ascending=False).head(10).sum()/df.weight.sum())})
    # Common security mappings for cross-listed names, independent of currency/listing.
    aa=a.set_index('ticker').weight.copy();aa.index=[{'2330':'TSM','005930':'SAMSUNG','005935':'SAMSUNG','SHOP':'SHOP'}.get(t,t) for t in aa.index];aa=aa.groupby(level=0).sum();aa=aa/aa.sum()
    overlap={}
    for name,df in [('QQQ',b),('VOO',c)]:
        w=df.groupby('ticker').weight.sum();w=w/w.sum();un=aa.index.union(w.index)
        overlap[name]={'weighted_overlap':float(np.minimum(aa.reindex(un,fill_value=0),w.reindex(un,fill_value=0)).sum()),'ixn_weight_in_common_names':float(aa.reindex(aa.index.intersection(w.index)).sum())}
    pd.DataFrame(result).to_csv(OUT/'concentration.csv',index=False)
    (OUT/'overlap.json').write_text(json.dumps(overlap,indent=2))
    return result,overlap,allfunds

CONC,OVERLAP,HOLD=holdings()

def exclusion():
    # Stress only. Constant modern weights are NOT historical constituent weights.
    # Rebalance monthly; remove positive and negative returns symmetrically.
    endpoints=IXN_NAV.loc[LAUNCH:].resample('ME').last().index.to_list()
    endpoints=[LAUNCH]+[min(t,END) for t in endpoints]
    endpoints=pd.DatetimeIndex(sorted(set(endpoints)))
    levels=LEVELS.reindex(LEVELS.index.union(endpoints)).sort_index().ffill().loc[endpoints]
    adrs=pd.DataFrame({s:series(s) for s in ['TSM','ASML']}).reindex(CAL.union(endpoints)).sort_index().ffill().loc[endpoints]
    r=levels.pct_change(fill_method=None);ar=adrs.pct_change(fill_method=None)
    w=HOLD['IXN'].set_index('ticker').weight;wt=float(w['2330']);wa=float(w['ASML']);total=wt+wa
    sets={'No removal':(0,0),'Half current weights':(wt*.5,wa*.5),'Current weights':(wt,wa),'Twice current weights':(wt*2,wa*2)}
    output=[]; paths={}
    for label,(t,a) in sets.items():
        ww=t+a;fees=.0037/12
        residual=(r.iloc[:,0]+fees-t*ar.TSM-a*ar.ASML)/(1-ww)-fees
        # Gain freeze: eliminated sleeve earns 0; remaining original exposure retained.
        freeze=r.iloc[:,0]-t*ar.TSM-a*ar.ASML
        for method,ret in [('Exclude and reallocate',residual),('Replace removed sleeve with zero-return cash',freeze)]:
            chain=(1+ret.fillna(0)).cumprod()
            ext=splice(LEVELS.iloc[:,0],chain.reindex(CAL.union(chain.index)).sort_index().ffill().reindex(CAL),LAUNCH)
            for win,start in WINDOWS.items():
                z=ext.loc[start:];yr=(z.index[-1]-z.index[0]).days/365.2425
                output.append({'window':win,'weight_sensitivity':label,'method':method,'TSM_weight':t,'ASML_weight':a,'cagr':float((z.iloc[-1]/z.iloc[0])**(1/yr)-1),'ending_10000':float(10000*z.iloc[-1]/z.iloc[0])})
            if label in ['No removal','Current weights'] and method=='Exclude and reallocate':paths[label]=chain
    pd.DataFrame(output).to_csv(OUT/'exclusion_sensitivity.csv',index=False)
    pd.DataFrame(paths).assign(QQQ=levels.iloc[:,1]/levels.iloc[0,1]).to_csv(OUT/'exclusion_monthly_paths.csv',index_label='date')
    return output

def diversification_experiment():
    # Conditional factor replay experiment, not a historical 1200-stock portfolio.
    # Replay each observed monthly tech-fund path as the common return. Synthetic
    # independent residuals have 30% annual volatility for an individual security.
    rng=np.random.default_rng(SEED); rows=[]; theory=[]
    for rho in [.2,.6,.8]:
        for n in [100,130,500,1200]:theory.append({'rho':rho,'stocks':n,'stock_volatility':.35,'portfolio_volatility':float(.35*np.sqrt(rho+(1-rho)/n))})
    for win,start in WINDOWS.items():
        l=LEVELS.iloc[:,0].loc[start:];m=pd.concat([l.head(1),l.resample('ME').last()]);m=m[~m.index.duplicated()].sort_index();m.index=[min(t,END) for t in m.index]
        rr=m.pct_change(fill_method=None).dropna().values
        y=(l.index[-1]-l.index[0]).days/365.2425
        z=rng.standard_normal((5000,len(rr))) # common random numbers across stock counts
        for n in [100,130,500,1200]:
            r=rr[None,:]+z*.30/np.sqrt(12*n)
            wealth=10000*np.exp(np.log1p(r).sum(axis=1))
            vol=np.std(r,axis=1,ddof=1)*np.sqrt(12)
            cg=(wealth/10000)**(1/y)-1
            rows.append({'window':win,'stocks':n,'paths':5000,'median_ending_10000':float(np.median(wealth)),'p05_ending_10000':float(np.quantile(wealth,.05)),'p95_ending_10000':float(np.quantile(wealth,.95)),'median_cagr':float(np.median(cg)),'median_volatility':float(np.median(vol))})
    pd.DataFrame(theory).to_csv(OUT/'equicorrelation_diversification.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/'factor_replay_diversification.csv',index=False)
    return rows,theory

def bootstrap():
    # Paired 12-month moving-block bootstrap; backward-looking, no AI forecast.
    r=LEVELS.loc[LAUNCH:].resample('ME').last().loc[:'2026-09-30'].pct_change(fill_method=None).dropna().to_numpy()
    rng=np.random.default_rng(SEED+1); rows=[]
    for win,start in WINDOWS.items():
        sample=LEVELS.loc[start:].resample('ME').last().loc[:'2026-09-30'].pct_change(fill_method=None).dropna().to_numpy()
        # Block starts only where full blocks exist; no artificial wrap at endpoints.
        for y in [1,3,5,10]:
            starts=rng.integers(0,len(sample)-11,size=(10000,y))
            idx=(starts[:,:,None]+np.arange(12)[None,None,:]).reshape(10000,12*y)
            wealth=np.exp(np.log1p(sample[idx]).sum(axis=1));cagr=wealth**(1/y)-1
            for j,n in enumerate(LEVELS):
                rows.append({'calibration_window':win,'horizon_years':y,'fund':SHORT[n],'paths':10000,'p05_cagr':float(np.quantile(cagr[:,j],.05)),'median_cagr':float(np.median(cagr[:,j])),'p95_cagr':float(np.quantile(cagr[:,j],.95)),'loss_fraction':float((wealth[:,j]<1).mean()),'ixn_beats_qqq_fraction':float((wealth[:,0]>wealth[:,1]).mean())})
    pd.DataFrame(rows).to_csv(OUT/'paired_block_bootstrap.csv',index=False)
    return rows

def wilder(x,n=14):
    vals=x.to_numpy();out=np.full(len(vals),np.nan)
    ix=next(i for i in range(n-1,len(vals)) if np.isfinite(vals[i-n+1:i+1]).all())
    out[ix]=vals[ix-n+1:ix+1].mean()
    for i in range(ix+1,len(vals)):out[i]=(out[i-1]*(n-1)+vals[i])/n
    return pd.Series(out,index=x.index)

def technicals():
    output=[]
    for s in ['IXN','QQQ','VOO']:
        d=P[s].copy();c=d.close
        for n in [20,50,100,200]:d['sma'+str(n)]=c.rolling(n).mean()
        delta=c.diff();d['rsi14']=100-100/(1+wilder(delta.clip(lower=0))/wilder((-delta).clip(lower=0)))
        d['macd']=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean();d['signal']=d.macd.ewm(span=9,adjust=False).mean();d['histogram']=d.macd-d.signal
        tr=pd.concat([d.high-d.low,(d.high-c.shift()).abs(),(d.low-c.shift()).abs()],axis=1).max(axis=1);d['atr14']=wilder(tr)
        sd=c.rolling(20).std(ddof=0);d['bb_lower']=d.sma20-2*sd;d['bb_upper']=d.sma20+2*sd
        z=d.iloc[-1].to_dict();z.update({'fund':s,'asof':str(d.index[-1].date()),'high52':float(d.high.tail(252).max()),'low52':float(d.low.tail(252).min()),'volume_ratio20':float(d.volume.iloc[-1]/d.volume.tail(20).mean()),'realized_vol63':float(d.adjusted.pct_change(fill_method=None).tail(63).std()*np.sqrt(252))})
        output.append(z);d.to_csv(OUT/(s.lower()+'_technical_history.csv'),index_label='date')
    (OUT/'technicals.json').write_text(json.dumps(output,indent=2));return output

def fee_math():
    out=[]
    for years in [1,3,5,10]:
        for f,fee in [('IXN',.0037),('QQQ',.0018),('VOO',.0003),('QQQM',.0015)]:
            out.append({'years':years,'fund':f,'fee':fee,'annual_gross_assumption':.08,'ending_100000':float(100000*(1.08*(1-fee))**years),'loss_vs_no_fee':float(100000*1.08**years-100000*(1.08*(1-fee))**years)})
    pd.DataFrame(out).to_csv(OUT/'fee_compounding.csv',index=False);return out

def run():
    hist,risk,roll,trail=historical();ex=exclusion();div,theory=diversification_experiment();boot=bootstrap();tech=technicals();fee=fee_math()
    result={'reconciliation':RECON,'history':hist,'trailing':trail,'concentration':CONC,'overlap':OVERLAP,'rolling':roll,'technicals':tech,'risk':risk,'exclusion':ex,'diversification':div,'equicorrelation':theory,'bootstrap':boot,'fees':fee}
    (OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print('Reconciliation:',RECON)
    print(pd.DataFrame(hist)[['window','fund','cagr','ending_10000','volatility','max_drawdown']].to_string(index=False))
    print('Concentration:',pd.DataFrame(CONC).to_string(index=False))
    print('Exclusion:',pd.DataFrame(ex).query("weight_sensitivity=='Current weights' and method=='Exclude and reallocate'").to_string(index=False))
    return result

if __name__=='__main__':run()
