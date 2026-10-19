import React, { useState } from "react";
import { DataComponent, DataTable, EvidenceChart, ReportSection, RichNarrative, SectionNavigator, useDataApp } from "../../data-app-public.jsx";
import { sections } from "./report-copy.js";
const pct = v => Number.isFinite(v) ? `${(v*100).toFixed(2)}%` : "—";
const num = v => Number.isFinite(v) ? v.toLocaleString("en-US",{maximumFractionDigits:2}) : "—";
const usd = v => Number.isFinite(v) ? v.toLocaleString("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0}) : "—";
const col=(field,label,format)=>({field,label,...(format?{renderCell:format}:{})});
const windows=["1990","2000","IXN inception","2010"];
const sourcePreviews={
 "https://investor.tsmc.com/english/quarterly-results/2026/q3":{title:"TSMC Q3 2026 results",summary:"Reported revenue of US$46.72bn and gross margin of 66.4%. Supports current foundry demand without establishing future stock returns.",source:"TSMC",approvedForReport:true},
 "https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary":{title:"Key questions on energy and AI",summary:"Projects data-center electricity use rising from about 485 TWh in 2025 to 950 TWh in 2030 and examines delivery constraints.",source:"IEA",approvedForReport:true}
};
export function ReportContent(){
 const {reviewedRows,visible,canEdit,mode,appTitle,setAppTitle}=useDataApp();
 const [windowName,setWindowName]=useState("IXN inception");
 const [calibration,setCalibration]=useState("IXN inception");
 const rows=id=>reviewedRows(id);
 function narrative(id){const s=sections.find(s=>s.id===id);return visible(id)&&<ReportSection id={id} title={s.text.split("\n")[0].replace(/^#+ /,"")} queryId={s.queries[0]} queryIds={s.queries} sourceRowsByQuery={Object.fromEntries(s.queries.map(q=>[q,rows(q)]))} showHeading={false}><RichNarrative id={`${id}:body`} value={s.text} sourcePreviews={sourcePreviews}/></ReportSection>;}
 function table(id,title,q,sourceRows,columns,displayRows=sourceRows){return visible(id)&&<DataComponent id={id} title={title} queryId={q} kind="table" sourceRows={sourceRows} displayRows={displayRows}><DataTable rows={displayRows} columns={columns} searchable={false} caption={title} compactNumbers={false}/></DataComponent>;}
 function chart(id,title,q,data,spec,height=340){return visible(id)&&<EvidenceChart id={id} title={title} queryId={q} rows={data} sourceRows={data} spec={{...spec,stackable:false}} height={height}/>;}
 const hist=rows("history").filter(r=>r.window===windowName);
 const wealth=rows("wealth").filter(r=>r.window===windowName);
 const trailing=rows("trailing");
 const trailingWide=[1,3,5,10].map(h=>({period:`${h} year${h>1?"s":""}`,...Object.fromEntries(["IXN","QQQ","VOO"].map(f=>[f,trailing.find(r=>r.horizon_years===h&&r.fund===`${f}*`)?.cagr]))}));
 const exclusion=rows("exclusion").filter(r=>r.method==="Exclude and reallocate"&&["No removal","Current weights"].includes(r.weight_sensitivity));
 const exclusionWide=windows.map(w=>({window:w,IXN:exclusion.find(r=>r.window===w&&r.weight_sensitivity==="No removal")?.cagr,removed:exclusion.find(r=>r.window===w&&r.weight_sensitivity==="Current weights")?.cagr,QQQ:rows("history").find(r=>r.window===w&&r.fund==="QQQ*")?.cagr}));
 const bootstrap=rows("bootstrap").filter(r=>r.calibration_window===calibration);
 const bootWide=[1,3,5,10].map(h=>({years:h,...Object.fromEntries(windows.map(w=>[w,rows("bootstrap").find(r=>r.calibration_window===w&&r.horizon_years===h&&r.fund==="IXN*")?.ixn_beats_qqq_fraction]))}));
 const countLong=rows("count").flatMap(r=>["model_130_stock_vol","model_1200_stock_vol","qqq_monthly_vol","voo_monthly_vol"].map(k=>({window:r.window,series:({model_130_stock_vol:"Synthetic 130",model_1200_stock_vol:"Synthetic 1,200",qqq_monthly_vol:"QQQ / proxy",voo_monthly_vol:"VOO / proxy"})[k],"Volatility (%)":r[k]*100})));
 const rho=rows("equicorrelation").filter(r=>r.rho===0.6).map(r=>({...r,"Volatility (%)":r.portfolio_volatility*100}));
 return <article className="report-content" aria-label="IXN QQQ VOO investment research report">
 <header className="report-hero"><h1 data-data-app-title contentEditable={canEdit&&mode==="edit"} suppressContentEditableWarning onBlur={canEdit&&mode==="edit"?e=>setAppTitle(e.currentTarget.textContent.trim()||appTitle):undefined}>{appTitle}</h1><RichNarrative id="report:deck" value="IXN, QQQ and VOO · Performance, concentration, AI economics and scenario analysis · Research as of October 19, 2026" className="report-deck"/></header>
 {narrative("executive-summary")}
 <SectionNavigator sections={sections.slice(1).map(s=>({id:s.id,label:s.text.split("\n")[0].replace(/^#+ /,"")}))}/>
 <section className="report-section" aria-label="Fund structure">{narrative("fund-structure")}
 {table("fund-facts","Fund design and costs","fundamentals",rows("fundamentals"),[col("fund","Fund"),col("inception","Launch"),col("expense","Annual fee",pct),col("equity_lines","Equity lines",num),col("scope","Investment universe")])}
 {table("selected-holdings","Selected company weights","exposures",rows("exposures"),[col("company","Company"),col("IXN","IXN",pct),col("QQQ","QQQ",pct),col("VOO","VOO",pct)])}</section>
 <section className="report-section" aria-label="Historical performance">{narrative("history-analysis")}
 <label className="etf-control">Historical start window <select aria-label="Historical start window" value={windowName} onChange={e=>setWindowName(e.target.value)}>{windows.map(w=><option key={w}>{w}</option>)}</select></label>
 {chart("wealth-chart",`Growth of $10,000 · ${windowName} through October 19, 2026`,"wealth",wealth,{type:"line",x:"date",y:"wealth_usd",series:"fund",currency:"USD",showXAxisLabel:false},400)}
 {table("history-table",`Annualized returns and ending wealth · ${windowName}`,"history",hist,[col("fund","Fund / proxy"),col("cagr","CAGR",pct),col("ending_10000","Ending $10k",usd),col("total_return","Total return",pct)])}
 {table("trailing-table","Trailing annualized returns · October 19, 2026","trailing",trailing,[col("period","Period"),col("IXN","IXN",pct),col("QQQ","QQQ",pct),col("VOO","VOO",pct)],trailingWide)}
 <RichNarrative id="history:labels" value="Chart labels flag prelaunch proxies. The 2010 IXN and QQQ lines are actual fund histories; only early VOO uses an index. The historical start selector also updates the risk table below. Other sections identify their own windows."/></section>
 <section className="report-section" aria-label="Risk and drawdowns">{narrative("risk-analysis")}
 {table("risk-table",`Daily risk statistics · ${windowName}`,"history",hist,[col("fund","Fund / proxy"),col("volatility","Annualized vol.",pct),col("max_drawdown","Max drawdown",pct),col("sharpe_fixed_3pct","Sharpe (3% hurdle)",num),col("daily_cvar95","Daily expected shortfall",pct)])}
 {table("rolling-table","IXN versus QQQ across overlapping windows","rolling",rows("rolling").filter(r=>r.fund==="IXN*"),[col("years","Years",num),col("observations","Windows",num),col("ixn_beats_qqq_fraction","IXN win share",pct),col("worst_cagr","Worst IXN CAGR",pct),col("best_cagr","Best IXN CAGR",pct)])}</section>
 <section className="report-section" aria-label="Excluding TSMC and ASML">{narrative("exclusion-analysis")}
 {chart("exclusion-chart","Current-weight removal sensitivity · since IXN launch","exclusion_path",rows("exclusion_path"),{type:"line",x:"date",y:"wealth_usd",series:"fund",currency:"USD",showXAxisLabel:false},380)}
 <ExclusionWindows rows={exclusion} displayRows={exclusionWide} history={rows("history")} visible={visible}/>
 {table("exclusion-sensitivity-table","Removal assumptions · IXN inception window","exclusion",rows("exclusion").filter(r=>r.window==="IXN inception"),[col("weight_sensitivity","Weight assumption"),col("method","Treatment"),col("cagr","CAGR",pct),col("ending_10000","Ending $10k",usd)])}</section>
 <section className="report-section" aria-label="Diversification models">{narrative("diversification-analysis")}
 {table("concentration-table","Diversification by issuer weights","concentration",rows("concentration"),[col("fund","Fund"),col("equity_lines","Equity lines",num),col("effective_stocks","Effective holdings",num),col("top3","Top 3",pct),col("top10_issuers","Top 10 issuers",pct),col("hhi","HHI",v=>v.toFixed(4))])}
 {visible("count-chart")&&<EvidenceChart id="count-chart" title="More technology stocks barely change modeled volatility" queryId="count" sourceRows={rows("count")} rows={countLong} spec={{type:"bar",x:"window",y:"Volatility (%)",series:"series",stackable:false,valueDecimals:2}} height={360}/>}
 {table("count-table","Matched-frequency annualized volatility · all starts","count",rows("count"),[col("window","Start"),col("model_130_stock_vol","Synthetic 130",pct),col("model_1200_stock_vol","Synthetic 1,200",pct),col("qqq_monthly_vol","QQQ / proxy",pct),col("voo_monthly_vol","VOO / proxy",pct)])}
 {chart("rho-chart","Illustration: common correlation limits diversification","equicorrelation",rho,{type:"line",x:"stocks",y:"Volatility (%)",valueDecimals:2,xLabel:"Equal-weight stocks",yStartAtZero:true},300)}
 <RichNarrative id="rho:assumptions" value="Illustration assumes 35% individual-stock volatility and 0.60 pairwise correlation. These are assumptions, not measured holdings correlations. The near-flat line shows that the shared component dominates once the portfolio contains many stocks."/></section>
 <section className="report-section" aria-label="AI investment thesis">{narrative("ai-thesis")}</section>
 <section className="report-section" aria-label="Valuation">{narrative("valuation-analysis")}
 {table("valuation-table","Dated valuation context · methods differ","fundamentals",rows("fundamentals"),[col("fund","Fund"),col("pe","P/E",num),col("pb","P/B",num),col("valuation_date","Source date")])}
 {table("valuation-sensitivity","IXN earnings growth needed in the stated P/E scenario","valuation",rows("valuation"),[col("years","Years",num),col("QQQ_EPS_growth_assumption","Assumed QQQ EPS growth",pct),col("IXN_required_EPS_growth_excluding_dividends","Required IXN EPS growth",pct),col("IXN_PE_annualized_price_drag","IXN P/E headwind",pct),col("QQQ_PE_annualized_price_drag","QQQ P/E headwind",pct)])}</section>
 <section className="report-section" aria-label="Historical resampling">{narrative("bootstrap-analysis")}
 {table("bootstrap-win-table","Historical-bootstrap IXN win share · all calibration starts","bootstrap",rows("bootstrap"),[col("years","Horizon years",num),...windows.map(w=>col(w,w,pct))],bootWide)}
 <label className="etf-control">Resampling calibration starts <select aria-label="Resampling calibration starts" value={calibration} onChange={e=>setCalibration(e.target.value)}>{windows.map(w=><option key={w}>{w}</option>)}</select></label>
 {table("bootstrap-ranges",`Modeled CAGR distribution · ${calibration} calibration`,"bootstrap",bootstrap,[col("fund","Fund / proxy"),col("horizon_years","Years",num),col("p05_cagr","5th percentile",pct),col("median_cagr","Median",pct),col("p95_cagr","95th percentile",pct),col("loss_fraction","Loss share",pct)])}</section>
 <section className="report-section" aria-label="Technical analysis">{narrative("technical-analysis")}
 {table("trend-table","Closing price and moving averages · October 19","technicals",rows("technicals"),[col("fund","Fund"),col("close","Close ($)",num),col("sma20","20-day SMA",num),col("sma50","50-day SMA",num),col("sma200","200-day SMA",num)])}
 {table("momentum-table","Momentum and trading range · October 19","technicals",rows("technicals"),[col("fund","Fund"),col("rsi14","RSI 14",num),col("histogram","MACD histogram",num),col("atr14","ATR ($)",num),col("high52","52-week high",num),col("low52","52-week low",num)])}</section>
 <section className="report-section" aria-label="Costs and conclusion">{narrative("fee-analysis")}
 {chart("fee-chart","Fee-only scenario · identical assumed 8% gross returns","fees",rows("fees"),{type:"line",x:"years",y:"ending_100000",series:"fund",currency:"USD",xLabel:"Years"},330)}
 {table("fee-table","Ending $100,000 after ten years · fee-only scenario","fees",rows("fees").filter(r=>r.years===10),[col("fund","Fund"),col("fee","Annual fee",pct),col("ending_100000","Ending wealth",usd),col("loss_vs_no_fee","Drag vs zero fee",usd)])}</section>
 <section className="report-section" aria-label="Methods and sources">{narrative("methods-and-sources")}</section>
 </article>;
}

function ExclusionWindows({rows,displayRows,history,visible}){return visible("exclusion-windows")&&<DataComponent id="exclusion-windows" title="Modeled annualized return after removal · all starts" queryId="exclusion" queryIds={["exclusion","history"]} sourceRowsByQuery={{exclusion:rows,history:history.filter(r=>r.fund==="QQQ*")}} displayRows={displayRows} kind="table"><DataTable rows={displayRows} columns={[col("window","Start"),col("IXN","Original IXN / proxy",pct),col("removed","Remove TSMC + ASML",pct),col("QQQ","QQQ / proxy",pct)]} searchable={false} caption="Current-weight exclusion sensitivity for all start windows"/></DataComponent>;}
