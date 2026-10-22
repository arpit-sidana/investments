import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const folder = path.join(root, 'research-reports/ai-equities-2027-2026-10-22');
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));
const model = read('ai-equities-model.json');
const snapshot = read('ai-equities-snapshot.json');
const sections = read('research-reports/ai-equities-2027-2026-10-22/narrative.json');
const money = (v, c='USD') => new Intl.NumberFormat('en-US', {style:'currency', currency:c, maximumFractionDigits:c==='KRW'?0:2}).format(v);
const pct = v => `${v>=0?'+':''}${(v*100).toFixed(1)}%`;
const cell = v => String(v).replaceAll('|','\\|').replaceAll('\n',' ');
const table = (head, rows) => [head, head.map(()=>'---'), ...rows].map(row=>'| '+row.map(cell).join(' | ')+' |').join('\n');
const section = id => {
  const value = sections.find(s=>s.id===id);
  assert(value, `Missing narrative ${id}`);
  return `<a id="${id}"></a>\n\n${value.text}`;
};

assert.equal(model.length,25);
assert.equal(new Set(model.map(r=>r.ticker)).size,25);
assert.equal(snapshot.queries.portfolio.rows.reduce((sum,r)=>sum+r.weight,0),100);
for (const r of model) {
  assert.equal(r.bearProbability+r.baseProbability+r.bullProbability,100);
  let ratio=0;
  for (const scenario of ['bear','base','bull']) {
    assert(Math.abs(r[scenario]-r[scenario+'EPS']*r[scenario+'PE'])<1e-7, `${r.ticker} ${scenario} target`);
    ratio+=r[scenario+'Probability']/100*r[scenario]/r.price*r[scenario+'FX'];
  }
  assert(Math.abs(ratio-1-r.expectedReturn)<1e-10, `${r.ticker} EV`);
}

const output = [
  '# AI equities through end-2027: who keeps the profit',
  '**Research date: October 22, 2026 · Reference entry: October 16, 2026 regular-session close · Horizon: December 31, 2027 · Hypothetical portfolio: $100,000**',
  'Complete Markdown reading edition. This preserves the existing research and model; conversion to Markdown is not a new market-data refresh. All scenarios and probabilities are analyst assumptions. [Back to report index](../../README.md).',
  section('executive'),
  '## Contents\n\n- [Scope and evidence boundaries](#scope)\n- [25-stock ranking](#ranking)\n- [K-shaped economy and human behavior](#macro)\n- [Where AI value becomes profit](#capture)\n- [Memory, optics, compute and power](#infra)\n- [Data licensing and agent workflows](#data-thesis)\n- [Consumer and luxury opportunities](#consumers)\n- [End-2026, mid-2027 and end-2027 milestones](#timing)\n- [All 25 company analyses and scenarios](#companies)\n- [Entry discipline](#valuation)\n- [Other candidates and exclusions](#screen)\n- [Valuation methodology](#methods)\n- [Portfolio allocations and stress cases](#portfolio)\n- [Monitoring and exit rules](#monitor)\n- [Source appendix](#sources)',
  section('scope'),
  '<a id="ranking"></a>\n\n## The 25-stock ranking',
  'Ordered by probability-weighted cumulative price return from the fixed entry to end-2027. The rank is a judgmental comparison within this researched set. Reference prices use the instrument currency; expected returns are in USD, including the SK hynix FX assumptions. Detailed probabilities, bear/base/bull targets and valuation inputs appear in each company analysis below.',
  table(['Rank / equity','Oct 16 close','Expected return','Portfolio weight'],model.map(r=>[`${r.rank}. [${r.ticker}](#analysis-${r.ticker.toLowerCase()})`,money(r.price,r.currency),pct(r.expectedReturn),`${r.weight}%`])),
  ...['macro','capture','infra','data-thesis','consumers','timing'].map(section),
  '<a id="companies"></a>\n\n## Company analyses',
  'Each case connects reported economics to an analyst earnings bridge, competitive outcomes, 2026–27 proof points and a reason to change the thesis. Confidence describes the evidence and thesis qualitatively; it does not validate scenario probabilities.',
];
for(const r of model) {
  output.push(
    `<a id="analysis-${r.ticker.toLowerCase()}"></a>\n\n### ${r.rank}. ${r.name} (${r.ticker})`,
    `**Oct 16 close:** ${money(r.price,r.currency)} (${r.currency}) · **Modeled expected return:** ${pct(r.expectedReturn)} · **Portfolio weight:** ${r.weight}% · **Entry/base EPS:** ${r.entryToBaseEPS.toFixed(1)}×. [Historical-price source](${r.priceSource}).`,
    `**Investment mechanism.** ${r.thesis}`,
    `**Reported starting point.** ${r.evidence} [Earnings / filing](${r.source})${r.date?` (dated ${r.date})`:''}.`,
    `**Base earnings bridge — analyst assumptions.** ${r.bridge}`,
    table(['Case / probability','CY2027 EPS','End-2027 P/E','End-2027 price'],['bear','base','bull'].map(s=>[`${s[0].toUpperCase()+s.slice(1)} / ${r[s+'Probability']}%`,money(r[s+'EPS'],r.currency),`${r[s+'PE']}×`,money(r[s],r.currency)])),
    ...(r.currency==='KRW'?[`**USD translation multipliers:** bear ${r.bearFX.toFixed(2)}×, base ${r.baseFX.toFixed(2)}×, bull ${r.bullFX.toFixed(2)}×. Displayed price endpoints are local KRW.`]:[]),
    `**Bear.** ${r.bearStory}\n\n**Base.** ${r.baseStory}\n\n**Bull.** ${r.bullStory}`,
    `**2026–27 catalysts and proof points**\n\n${r.catalysts.map(c=>'- '+c).join('\n')}`,
    `**Change the thesis if:** ${r.failure}`,
    `**Valuation and risk.** ${r.risk}`,
    `**Evidence confidence:** ${r.confidence}. **Earnings definition:** ${r.basis}.`,
    '[Back to ranking](#ranking)',
  );
}
output.push(
  '<a id="valuation"></a>\n\n## Entry discipline across all 25',
  'The scenario EPS, multiples and targets are given beside each company above. Entry/base EPS uses calendar-2027 modeled normalized earnings, not consensus forward earnings. The entry ceiling preserves a 25% modeled cumulative expected return under unchanged assumptions; it is not a guarantee of value.',
  table(['Equity','Entry/base EPS','25% return entry ceiling'],model.map(r=>[r.ticker,`${r.entryToBaseEPS.toFixed(1)}×`,money(r.buyCeiling,r.currency)])),
  section('screen'), section('methods'), section('portfolio'),
  '### $100k target portfolio',
  table(['Holding / theme','Weight','Dollar budget','Expected contribution'],snapshot.queries.portfolio.rows.map(r=>[`${r.ticker} / ${r.theme}`,`${r.weight}%`,money(r.dollars),`${(r.contribution*100).toFixed(2)} pp`])),
  '### Portfolio outcomes and probability sensitivity',
  'These are illustrative portfolio endpoints; no joint scenario probabilities are implied. Price returns exclude dividends, taxes, fees and cash interest.',
  table(['Illustration','Terminal value','Price return'],snapshot.queries.stress.rows.map(r=>[r.scenario,money(r.terminalValue),pct(r.priceReturn)])),
  section('monitor'),
  '<a id="sources"></a>\n\n## Source appendix',
  fs.readFileSync(path.join(root,'ai-equities-source-index.md'),'utf8').replace(/^# Controlling research sources\n\n/,''),
  '## Reproducible supporting files\n\n- [Company and scenario model](../../ai-equities-model.json)\n- [Research snapshot, including portfolio and stress inputs](../../ai-equities-snapshot.json)\n- [Narrative source](narrative.json)\n- [Markdown renderer](../../scripts/render-ai-equities-markdown.mjs)\n\nRun `node scripts/render-ai-equities-markdown.mjs` from the repository to regenerate this edition. This reads saved inputs and does not fetch quotes, execute trades, start a server, or deploy a site.',
);
const text=output.join('\n\n')+'\n';
for(const s of sections)assert(text.includes(s.text),`Narrative omitted: ${s.id}`);
for(const r of model)for(const field of ['thesis','evidence','bridge','bearStory','baseStory','bullStory','failure','risk'])assert(text.includes(r[field]),`Omitted ${r.ticker} ${field}`);
fs.writeFileSync(path.join(folder,'REPORT.md'),text);
console.log(`Wrote complete Markdown: ${model.length} companies, ${model.length*3} scenarios, ${sections.length} narrative sections; ${text.length.toLocaleString()} characters.`);
