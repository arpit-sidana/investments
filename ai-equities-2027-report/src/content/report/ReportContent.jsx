import React, {useState} from 'react';
import {DataComponent, DataTable, EvidenceChart, ReportSection, RichNarrative, useDataApp} from '../../data-app-public.jsx';
import sections from './narrative.json';
import './report.css';

const pct=n=>`${n>=0?'+':''}${(n*100).toFixed(1)}%`;
const money=(v,currency='USD')=>new Intl.NumberFormat('en-US',{style:'currency',currency,maximumFractionDigits:currency==='KRW'?0:2}).format(v);
const number=n=>new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(n);
const sourceIds={executive:['rankings','portfolio','stress'],scope:['research'],macro:['research','macro'],capture:['research'],infra:['research','rankings'],'data-thesis':['research'],consumers:['research'],timing:['research'],screen:['research'],methods:['rankings','research'],portfolio:['portfolio','stress','rankings'],monitor:['research']};
const returnSpec={type:'horizontalBar',x:'ticker',y:'expectedGrowth',fields:['expectedGrowth','downsideGrowth'],stackable:false,valueDecimals:1,startAtZero:true,legend:{labels:{expectedGrowth:'Expected price return',downsideGrowth:'Operating bear return'}}};

function previews(text){const matches=[...text.matchAll(/\]\((https:\/\/[^)]+)\)/g)];return Object.fromEntries(matches.map(x=>[x[1],{title:new URL(x[1]).hostname,summary:'Public source supporting the adjacent reported fact. Forward-looking valuation and behavioral interpretations are analyst judgments.',source:new URL(x[1]).hostname,approvedForReport:true}]));}

export function ReportContent(){
 const {snapshot,appTitle,canEdit,mode,setAppTitle,visible}=useDataApp();
 const rows=snapshot.queries.rankings.rows;
 const [selected,setSelected]=useState('all');
 const section=id=>{
  const s=sections.find(x=>x.id===id);const queryIds=sourceIds[id];
  const sourceRowsByQuery=Object.fromEntries(queryIds.map(q=>[q,q==='research'?snapshot.queries[q].rows.filter(r=>r.section===s.title):snapshot.queries[q].rows]));
  return visible('section-'+id)&&<div id={id} key={id} className="eq-section"><ReportSection id={'section-'+id} title={s.title} queryId={queryIds[0]} queryIds={queryIds} sourceRowsByQuery={sourceRowsByQuery} showHeading={false}><RichNarrative id={id+':body'} value={s.text} sourcePreviews={previews(s.text)} label={'Edit '+s.title}/></ReportSection></div>;
 };
 const rankCols=[
  {field:'rank',label:'#'}, {field:'ticker',label:'Equity'},
  {field:'price',label:'Oct 16 close',renderCell:(v,r)=>money(v,r.currency)},
  {field:'probabilities',label:'Bear/base/bull %'},
  {field:'bear',label:'Bear price',renderCell:(v,r)=>money(v,r.currency)},
  {field:'base',label:'Base price',renderCell:(v,r)=>money(v,r.currency)},
  {field:'bull',label:'Bull price',renderCell:(v,r)=>money(v,r.currency)},
  {field:'expectedReturn',label:'Expected return',renderCell:v=>pct(v)},
  {field:'weight',label:'Portfolio %',renderCell:v=>`${v}%`}
 ];
 const valuationCols=[{field:'ticker',label:'Equity'},{field:'basis',label:'Earnings basis'},
  {field:'bearEPS',label:'Bear EPS',renderCell:(v,r)=>money(v,r.currency)},
  {field:'bearPE',label:'Bear P/E',renderCell:v=>`${v}×`},
  {field:'baseEPS',label:'Base EPS',renderCell:(v,r)=>money(v,r.currency)},
  {field:'basePE',label:'Base P/E',renderCell:v=>`${v}×`},
  {field:'bullEPS',label:'Bull EPS',renderCell:(v,r)=>money(v,r.currency)},
  {field:'bullPE',label:'Bull P/E',renderCell:v=>`${v}×`},
  {field:'entryToBaseEPS',label:'Entry/base EPS',renderCell:v=>`${v.toFixed(1)}×`},
  {field:'buyCeiling',label:'25% return ceiling',renderCell:(v,r)=>money(v,r.currency)}];
 return <article className="report-content eq-report" aria-label="AI public-equity investment report">
  <header className="report-hero"><h1 data-data-app-title contentEditable={canEdit&&mode==='edit'} suppressContentEditableWarning onBlur={canEdit&&mode==='edit'?e=>setAppTitle(e.currentTarget.textContent.trim()||appTitle):undefined}>{appTitle}</h1><RichNarrative id="report-intro" value="October 16, 2026 reference prices · December 31, 2027 horizon · US demand, global public equities · $100k growth portfolio" className="report-deck"/></header>
  {section('executive')}
  <nav className="eq-toc" aria-label="Report contents">{[['ranking','25-stock ranking'],['macro','K-shaped economy'],['infra','Physical bottlenecks'],['data-thesis','Data and agents'],['companies','Company analyses'],['valuation','Valuation assumptions'],['portfolio','Portfolio and risks'],['methods','Methodology']].map(([id,label])=><a key={id} href={'#'+id}>{label}</a>)}</nav>
  {section('scope')}
  <div id="ranking" className="eq-section"><RichNarrative id="ranking-intro" value="## The 25-stock ranking\n\nOrdered by probability-weighted cumulative price return. Targets are analyst scenarios for end-2027; probabilities are judgments. Prices and targets use each instrument’s stated currency. SK hynix expected return includes modeled FX. Use the table arrows to see every row; the full source contains all 25 companies."/>
   {visible('return-chart')&&<EvidenceChart id="return-chart" title="Expected upside comes with substantial operating downside" queryId="rankings" rows={rows} sourceRows={rows} height={820} spec={returnSpec} description="Modeled returns from October 16, 2026. Operating bear returns are scenario endpoints, not worst-case losses. All 25 stocks are shown."/>}
   {visible('rankings')&&<DataComponent id="rankings" title="All 25 ranked equities and price scenarios" kind="table" queryId="rankings" sourceRows={rows} displayRows={rows}><DataTable rows={rows} columns={rankCols} searchable={false} compactNumbers={false} caption="Ranked end-2027 stock price scenarios; regular-session close October 16, 2026"/></DataComponent>}
  </div>
  {section('macro')}{section('capture')}{section('infra')}{section('data-thesis')}{section('consumers')}{section('timing')}
  <section id="companies" className="eq-section"><RichNarrative id="company-intro" value="## Company analyses\n\nEach analysis connects reported economics to an analyst valuation bridge, three competitive outcomes, 2026–27 proof points and a reason to change the thesis. EPS and P/E appear in a separate inspectable table for every company. Confidence describes the evidence and thesis qualitatively; it does not validate the scenario probabilities."/>
   <div className="eq-company-selector"><label htmlFor="company-select">Read a company</label><select id="company-select" value={selected} onChange={e=>setSelected(e.target.value)}><option value="all">All 25 analyses</option>{rows.map(r=><option key={r.ticker} value={r.ticker}>{r.rank}. {r.name} ({r.ticker})</option>)}</select>{selected!=='all'&&<button onClick={()=>setSelected('all')}>Show all 25</button>}</div>
   {rows.filter(r=>selected==='all'||r.ticker===selected).map(r=>{
    const q='company_'+r.ticker;
    const text=`## ${r.rank}. ${r.name} (${r.ticker})\n\n**Investment mechanism.** ${r.thesis}\n\n**Reported starting point.** ${r.evidence} [Earnings / filing](${r.source}).\n\n**Base earnings bridge — analyst assumptions.** ${r.bridge}\n\n**Bear.** ${r.bearStory}\n\n**Base.** ${r.baseStory}\n\n**Bull.** ${r.bullStory}\n\n**2026–27 catalysts and proof points**\n\n${r.catalysts.map(c=>'- '+c).join('\n')}\n\n**Change the thesis if:** ${r.failure}\n\n**Valuation and risk.** ${r.risk}\n\n**Evidence confidence:** ${r.confidence}. **Earnings definition:** ${r.basis}.`;
    const caseRows=[['Bear',r.bearEPS,r.bearPE,r.bearProbability,r.bear,r.bearFX],['Base',r.baseEPS,r.basePE,r.baseProbability,r.base,r.baseFX],['Bull',r.bullEPS,r.bullPE,r.bullProbability,r.bull,r.bullFX]].map(([scenario,eps,pe,probability,price,fx])=>({scenario,eps,pe,probability,price,fx}));
    return <div key={r.ticker} id={'analysis-'+r.ticker} className="eq-company">
     {visible('company-'+r.ticker)&&<ReportSection id={'company-'+r.ticker} title={r.name+' investment case'} queryId={q} sourceRows={[r]} showHeading={false}><RichNarrative id={'company-'+r.ticker+':body'} value={text} sourcePreviews={{[r.source]:{title:r.name+' earnings / filing',summary:r.evidence,source:new URL(r.source).hostname,date:r.date??undefined,approvedForReport:true}}}/></ReportSection>}
     {visible('case-'+r.ticker)&&<DataComponent id={'case-'+r.ticker} queryId={q} title={r.name+' — analyst valuation scenarios'} kind="table" displayRows={caseRows} sourceRows={[r]}>
      <div className="eq-company-facts" data-reviewed-rows><span>October 16 close <strong>{money(r.price,r.currency)}</strong></span><span>Expected return <strong>{pct(r.expectedReturn)}</strong></span><span>Target weight <strong>{r.weight}%</strong></span><span>Entry / base EPS <strong>{r.entryToBaseEPS.toFixed(1)}×</strong></span></div>
      <DataTable searchable={false} compactNumbers={false} rows={caseRows} columns={[{field:'scenario',label:'Case'},{field:'probability',label:'Probability',renderCell:v=>`${v}%`},{field:'eps',label:'CY2027 EPS',renderCell:v=>money(v,r.currency)},{field:'pe',label:'Year-end P/E',renderCell:v=>`${v}×`},{field:'price',label:'End-2027 price',renderCell:v=>money(v,r.currency)},...(r.currency==='KRW'?[{field:'fx',label:'FX return multiplier',renderCell:v=>`${v.toFixed(2)}×`}]:[])]} caption={r.name+' end-2027 modeled scenarios'}/>
      <p className="eq-small" data-reviewed-rows>Prices: {r.currency}. <a href={r.priceSource} target="_blank" rel="noreferrer">Reference-price history</a>. {r.currency==='KRW'?'Expected return applies the displayed currency multipliers; the price endpoints above are local KRW.':'Dividends and transaction costs are excluded.'}</p>
     </DataComponent>}
    </div>;
   })}
  </section>
  <div id="valuation" className="eq-section"><RichNarrative id="valuation-intro" value="## Valuation assumptions across all 25\n\nThe earnings definitions differ and are stated explicitly. The base-case P/E is an assumed multiple applied at end-2027 to calendar-2027 normalized earnings. The entry ceiling preserves a 25% modeled cumulative return; it is not a guarantee of value."/>
   {visible('valuation-matrix')&&<DataComponent id="valuation-matrix" title="EPS, multiples and entry discipline" kind="table" queryId="rankings" sourceRows={rows} displayRows={rows}><DataTable rows={rows} columns={valuationCols} searchable={false} compactNumbers={false} caption="All analyst valuation inputs and scenario-dependent entry ceilings"/></DataComponent>}
  </div>
  {section('screen')}{section('methods')}{section('portfolio')}
  {visible('portfolio-table')&&<DataComponent id="portfolio-table" title="$100k target portfolio" queryId="portfolio" kind="table" sourceRows={snapshot.queries.portfolio.rows} displayRows={snapshot.queries.portfolio.rows}><DataTable searchable={false} compactNumbers={false} rows={snapshot.queries.portfolio.rows} columns={[{field:'ticker',label:'Holding'},{field:'theme',label:'Primary mechanism'},{field:'weight',label:'Weight',renderCell:v=>`${v}%`},{field:'dollars',label:'Dollar budget',renderCell:v=>money(v)},{field:'expectedReturn',label:'Modeled return',renderCell:v=>pct(v)},{field:'contribution',label:'Portfolio contribution',renderCell:v=>`${(v*100).toFixed(2)} pp`}]} caption="$100,000 hypothetical portfolio allocations, including cash"/></DataComponent>}
  {visible('portfolio-stress')&&<DataComponent id="portfolio-stress" title="Portfolio outcomes and probability sensitivity" queryId="stress" kind="table" sourceRows={snapshot.queries.stress.rows} displayRows={snapshot.queries.stress.rows}><DataTable searchable={false} compactNumbers={false} rows={snapshot.queries.stress.rows} columns={[{field:'scenario',label:'Illustration'},{field:'terminalValue',label:'Terminal value',renderCell:v=>money(v)},{field:'priceReturn',label:'Price return',renderCell:v=>pct(v)}]} caption="Portfolio stress endpoints; no joint scenario probabilities are implied"/></DataComponent>}
  {section('monitor')}
  <RichNarrative id="closing-note" value="Research uses public filings, earnings releases and dated primary macro evidence. Price scenarios, allocation decisions and causal interpretations are analyst judgments. The reference date is fixed; verify a current quote and the latest filing before implementation. Source actions beside each section retain the underlying observations and assumptions."/>
 </article>;
}
