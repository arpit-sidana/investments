import fs from 'node:fs';
import path from 'node:path';
const root='/Users/ArpitSidana/Documents/ChatGPT/Investments';
const project=path.join(root,'ai-equities-2027-report');
const input=JSON.parse(fs.readFileSync(path.join(root,'ai-equities-company-research.json'),'utf8'));
const m=input.map(x=>{
  if(x.ticker==='ETN')x.date='2026-07-31';
  if(x.ticker==='TOST')x.date=null;
  if(x.ticker==='ADBE')x.priceSource='https://www.quiverquant.com/stock/ADBE/historical-prices/';
  const targets=[x.bearEPS*x.bearPE,x.baseEPS*x.basePE,x.bullEPS*x.bullPE];
  const probs=[x.bearProbability,x.baseProbability,x.bullProbability];
  const fx=[x.bearFX,x.baseFX,x.bullFX];
  const ev=targets.reduce((s,v,i)=>s+v*probs[i]/100*fx[i],0);
  return {...x,bear:targets[0],base:targets[1],bull:targets[2],evPrice:ev,
    expectedReturn:ev/x.price-1,expectedGrowth:ev/x.price-1,downside:targets[0]*fx[0]/x.price-1,
    downsideGrowth:targets[0]*fx[0]/x.price-1,baseReturn:targets[1]/x.price-1,
    dollars:x.weight*1000,entryToBaseEPS:x.price/x.baseEPS,buyCeiling:ev/1.25,
    probabilities:probs.join('/'),classification:'Analyst modeled outcomes; observed reference price',
    approximateShares:x.weight?x.weight*1000/x.price:0};
}).sort((a,b)=>b.expectedReturn-a.expectedReturn).map((x,i)=>({...x,rank:i+1}));
const snapshot=JSON.parse(fs.readFileSync(path.join(project,'src/data.json'),'utf8'));
snapshot.generatedAt=new Date().toISOString();
snapshot.report={asOf:'2026-10-22'};
snapshot.buildStatus='updating';
snapshot.status='reviewed';
snapshot.filters=[];
snapshot.title='AI returns through 2027 will depend on who keeps the profit';
const links=m.flatMap(x=>[{label:x.name+' earnings / filing',href:x.source},{label:x.ticker+' October 16 historical price',href:x.priceSource}]);
const methodCode=`For each company: bear=bearEPS*bearPE; base=baseEPS*basePE; bull=bullEPS*bullPE. evPrice=(bear*bearProbability*bearFX+base*baseProbability*baseFX+bull*bullProbability*bullFX)/100. expectedReturn=evPrice/price-1. downside=bear*bearFX/price-1. dollars=weight*1000. buyCeiling=evPrice/1.25. Rank descending expectedReturn. Price is the regular-session close on 2026-10-16; no dividend adjustment is used. All target EPS, multiples, probabilities, FX assumptions and diluted-share bridges are analyst assumptions. No YTD returns enter the calculation.`;
const evidenceFlow=[{title:'Public research retrieval',detail:'Provider: web.run. Individual historical-price searches generally used search_query:[{q:"\\\"TICKER\\\" \\\"Oct 16, 2026\\\" historical"}], replacing TICKER with each identifier; SK hynix used 000660. Issuer earnings releases and SEC exhibits were retrieved through targeted issuer/period searches and, for key accounting checks, direct open requests. Every controlling URL is retained. Extracted facts and calculations are retained in the source inspectors; the source index lists controlling references without reproducing complete webpages. NVDA and TSM prices were found with the query site:finance.yahoo.com NVDA historical data Oct 16 2026 TSM MU AVGO. Retrieval date: 2026-10-22. US price time: regular-session close, America/New_York; Korean close: Asia/Seoul.'},
{title:'Observed versus modeled',detail:'Reference prices and stated historical financial metrics are observed source inputs. All 2027 earnings, terminal multiples, probabilities, FX moves, portfolio weights and expected returns are analyst scenarios; they are not reported company guidance.'},
{title:'Reproduce calculations',detail:methodCode}];
const metricDefinitions=[
{label:'Expected price return',definition:'Probability-weighted end-2027 price divided by October 16, 2026 regular-session close, minus one. No dividends, taxes, fees or cash interest. KRW scenario translation applies only to SK hynix.',formula:'(bear*bearProbability*bearFX+base*baseProbability*baseFX+bull*bullProbability*bullFX)/100/price-1',componentIds:['rankings','return-chart','portfolio-table','portfolio-stress'],dependencies:['price','bear','base','bull','bearProbability','baseProbability','bullProbability','bearFX','baseFX','bullFX']},
{label:'End-2027 price',definition:'Calendar-2027 normalized diluted EPS times an analyst-selected year-end 2027 P/E; instrument currency is stated per company.',componentIds:['rankings','valuation-matrix']},
{label:'Bear downside',definition:'Operating bear terminal price, adjusted for modeled currency movement, divided by reference price minus one. This is not a maximum-loss estimate.',componentIds:['return-chart','rankings']},
{label:'Entry ceiling',definition:'Expected terminal price divided by 1.25, preserving a 25% modeled cumulative price return. This is not intrinsic value or a guarantee.',formula:'evPrice/1.25',componentIds:['valuation-matrix']},
{label:'Portfolio allocation',definition:'Weight is percent of the full $100,000 target portfolio. Dollar budget equals weight times $1,000. The residual 8% is cash; displayed stress values assume full target allocation at reference prices.',componentIds:['portfolio-table','portfolio-stress']}
];
snapshot.queries.rankings={rows:m,source:{label:'Analyst scenario model using issuer earnings and October 16 closing prices',links,notes:'Subjective three-point distributions. Normalized earnings definitions differ by issuer. Read the company basis and scenario bridge; ranks are not calibrated forecasts. All queried companies shown; no return-based filtering.',evidenceFlow,metricDefinitions},methods:[{language:'text',code:methodCode}]};
for(const x of m){
 snapshot.queries['company_'+x.ticker]={rows:[x],source:{label:x.name+' — operating evidence and analyst valuation',links:[{label:'Controlling earnings / filing',href:x.source},{label:'Reference-price history',href:x.priceSource}],notes:`${x.date?'Release date: '+x.date+'. ':''}Price: 2026-10-16. Basis: ${x.basis}. ${x.evidence} Confidence label is qualitative; all 2027 outputs are modeled.`,evidenceFlow:[{title:'Primary operating evidence',detail:JSON.stringify({provider:'web.run',source:x.source,period:x.date??'Q2 2026',retrieved:'2026-10-22',extracted:x.evidence})},{title:'Observed reference price',detail:JSON.stringify({provider:'web.run',historicalPriceSource:x.priceSource,request:{search_query:[{q:["NVDA","TSM"].includes(x.ticker)?"site:finance.yahoo.com NVDA historical data Oct 16 2026 TSM MU AVGO":`"${x.ticker}" "Oct 16, 2026" historical`}]},date:'2026-10-16',currency:x.currency,field:'Close',value:x.price})},{title:'Analyst transformation',detail:methodCode}],metricDefinitions:[{label:'Valuation assumptions',definition:x.basis+'. '+x.bridge,componentIds:['company-'+x.ticker,'case-'+x.ticker]}]},methods:[{language:'text',code:methodCode}]};
}
const macro=snapshot.queries.macro;
macro.source.links=macro.source.links.map(l=>({label:l.label,href:l.href??l.url}));
macro.source.notes+=' These are separate non-comparable macro indicators, not a common cohort.';
const sections=JSON.parse(fs.readFileSync(path.join(project,'src/content/report/narrative.json'),'utf8'));
const narrativeLinks=[...new Set(sections.flatMap(s=>[...s.text.matchAll(/\]\((https:\/\/[^)]+)\)/g)].map(v=>v[1])))];
snapshot.queries.research={rows:sections.filter(s=>!['executive','portfolio','methods'].includes(s.id)).map(s=>({section:s.title,classification:'Source-backed qualitative analysis; inference identified in text',analysis:s.text})),source:{label:'Primary macro releases, issuer earnings and business-model evidence',links:narrativeLinks.map(href=>({href,label:new URL(href).hostname+new URL(href).pathname})),notes:'This is qualitative evidence, not a numeric score or causally identified model. Candidate map coverage is broader than the fully modeled universe. Private-company anecdotes are not verified revenue measurements.',evidenceFlow:[{title:'Read public evidence',detail:'Provider web.run; primary source links in this record and adjacent narrative. Queries covered September 2026 CPI, October consumer spending, September housing, Q2 household credit, AI workflow data licensing and issuer earnings. Results retrieved 2026-10-22.'},{title:'Interpretation',detail:'Separate observed reported results from behavioral hypotheses and forward-looking analyst judgments; do not infer household motivation from aggregate transaction growth.'}]}};
const allocated=m.filter(x=>x.weight>0);
const cashWeight=100-m.reduce((s,x)=>s+x.weight,0);
const cash=1000*cashWeight;
const values={expected:cash+m.reduce((s,x)=>s+x.dollars*(1+x.expectedReturn),0),bear:cash+m.reduce((s,x)=>s+x.dollars*x.bear*x.bearFX/x.price,0),base:cash+m.reduce((s,x)=>s+x.dollars*x.base/x.price,0),bull:cash+m.reduce((s,x)=>s+x.dollars*x.bull*x.bullFX/x.price,0)};
const shift10=m.reduce((s,x)=>s+x.dollars*.10*(x.bear*x.bearFX-x.bull*x.bullFX)/x.price,0);
snapshot.queries.portfolio={rows:[...allocated.map(x=>({ticker:x.ticker,name:x.name,theme:x.theme,weight:x.weight,dollars:x.dollars,referencePrice:x.price,expectedReturn:x.expectedReturn,contribution:x.weight/100*x.expectedReturn})),{ticker:'CASH',name:'Uninvested USD cash',theme:'Cash',weight:cashWeight,dollars:cash,referencePrice:1,expectedReturn:0,contribution:0}],source:{label:'Hypothetical $100,000 target allocation',links,notes:'Weights are analyst decisions, not a mean-variance optimizer. No leverage. Cash yield, tax, dividends and transaction costs omitted. Full allocation at reference prices differs from proposed staged execution.',evidenceFlow,metricDefinitions},methods:[{language:'text',code:'dollars=100000*weight/100; contribution=weight/100*expectedReturn; cash=100000-sum(stock dollars). Terminal portfolio values sum dollars*(scenario price/reference price), plus cash.'}]};
snapshot.queries.stress={rows:[{scenario:'Expected under company probabilities',terminalValue:values.expected,priceReturn:values.expected/100000-1},{scenario:'All-company operating bear endpoints',terminalValue:values.bear,priceReturn:values.bear/100000-1},{scenario:'All-company base endpoints',terminalValue:values.base,priceReturn:values.base/100000-1},{scenario:'All-company bull endpoints',terminalValue:values.bull,priceReturn:values.bull/100000-1},{scenario:'Expected: shift 10 points bull to bear',terminalValue:values.expected+shift10,priceReturn:(values.expected+shift10)/100000-1},{scenario:'60% decline in all equities',terminalValue:cash+(100000-cash)*.4,priceReturn:(cash+(100000-cash)*.4)/100000-1}],source:{label:'Deterministic scenario aggregation; no estimated joint probabilities',links:[],notes:'Synchronized endpoints are stress illustrations, not probabilistic portfolio forecasts. Company probabilities differ and no covariance model was estimated.',evidenceFlow:[{title:'Aggregate terminal values',detail:'Sum each target dollar holding times the respective scenario price/reference-price ratio, plus $8,000 cash. Use KRW translation multipliers for SK hynix; its weight is zero.'},{title:'Probability sensitivity',detail:'For each equity holding shift 0.10 probability from its bull endpoint to bear. Delta=value*(bear*bearFX-bull*bullFX)/price*0.10. Leave base unchanged.'}],metricDefinitions:[{label:'Terminal portfolio value',definition:'Deterministic weighted value of target allocations. Returns exclude income, taxes and costs.',componentIds:['portfolio-stress']}]}};
snapshot.modelSummary={capital:100000,cash,holdings:allocated.length,values,probabilityShift10:shift10,entry:'2026-10-16',horizon:'2027-12-31',days:441};
fs.writeFileSync(path.join(project,'src/data.json'),JSON.stringify(snapshot,null,2));
fs.writeFileSync(path.join(root,'ai-equities-model.json'),JSON.stringify(m,null,2));
const sourceIndexLinks=[...new Map([...links,...narrativeLinks.map(href=>({href,label:new URL(href).hostname+new URL(href).pathname}))].map(x=>[x.href,x])).values()];
const sourceIndex='# Controlling research sources\n\nPrepared October 22, 2026; regular-session entry prices October 16. Issuer filings/releases establish historical financial facts. Historical tables establish the reference close. Scenarios, probabilities and weights are analyst estimates. The report retains scope and transformations beside each source-backed component. Complete webpages are not reproduced.\n\n'+sourceIndexLinks.map(x=>'- ['+x.label+']('+x.href+')').join('\n');
fs.writeFileSync(path.join(root,'ai-equities-source-index.md'),sourceIndex);
fs.writeFileSync(path.join(root,'ai-equities-research-log.md'),sourceIndex);
console.log(JSON.stringify({companies:m.length,positions:allocated.length,cash,values,shift10,queries:Object.keys(snapshot.queries).length}));
