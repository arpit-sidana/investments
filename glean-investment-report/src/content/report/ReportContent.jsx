import React from "react";

import {
  DataComponent, DataTable, EvidenceChart, MetricCard, ReportSection, RichNarrative, useDataApp,
} from "../../data-app-public.jsx";

const pct = (value) => `${(Number(value) * 100).toFixed(1)}%`;
const pctWhole = (value) => `${Number(value).toFixed(1)}%`;
const dollars = (value) => `$${Number(value).toFixed(2)}`;
const billions = (value) => `$${Number(value).toFixed(2)}B`;
const millions = (value) => `$${Number(value).toFixed(0)}M`;
const multiple = (value) => `${Number(value).toFixed(2)}x`;

const arrSpec = {
  type: "line", x: "date", y: "arrMillions", yLabel: "ARR ($M)", valueDecimals: 0,
  annotations: [
    { id: "arr-100", kind: "point", at: "2025-02-05", field: "arrMillions", label: "$100M ARR" },
    { id: "arr-300", kind: "point", at: "2026-05-28", field: "arrMillions", label: "$300M ARR" },
  ],
};
const priceSpec = { type: "horizontalBar", x: "venue", y: "price", xLabel: "Price per share ($)", valueDecimals: 2 };
const capSpec = { type: "horizontalBar", x: "cohort", y: "estimatedPct", xLabel: "Estimated ownership (%)", valueDecimals: 1 };
const scenarioSpec = { type: "bar", x: "case", y: "impliedSharePrice", yLabel: "Implied share price ($)", valueDecimals: 0 };
const exitSpec = { type: "horizontalBar", x: "outcome", y: "probabilityPct", xLabel: "Subjective probability (%)", valueDecimals: 0 };

function Narrative({ id, queryId, queryIds, rows, rowsByQuery, title, value, className = "report-analysis" }) {
  return <ReportSection id={id} title={title} queryId={queryId ?? queryIds?.[0]} queryIds={queryIds}
    sourceRows={rows} sourceRowsByQuery={rowsByQuery} showHeading={false}>
    <RichNarrative id={`${id}:body`} className={className} label={`Edit ${title}`} value={`## ${title}\n\n${value}`} />
  </ReportSection>;
}

function EvidenceTable({ id, title, queryId, rows, columns, description }) {
  return <DataComponent id={id} title={title} queryId={queryId} kind="table"
    displayRows={rows} sourceRows={rows} description={description}>
    <DataTable rows={rows} columns={columns} searchable={false} caption={title} />
  </DataComponent>;
}

export function ReportContent() {
  const { reviewedRows, visible, canEdit, mode, appTitle, setAppTitle } = useDataApp();
  const arr = reviewedRows("arr_milestones");
  const marks = reviewedRows("market_marks");
  const rounds = reviewedRows("funding_rounds");
  const cap = reviewedRows("cap_table_estimate");
  const scenarios = reviewedRows("valuation_scenarios");
  const sensitivity = reviewedRows("entry_sensitivity");
  const platforms = reviewedRows("platforms");
  const exits = reviewedRows("exit_probabilities");
  const social = reviewedRows("social_signals");

  const forge = marks.find((row) => row.venue === "Forge Price") ?? {};
  const npm = marks.find((row) => row.venue.includes("Nasdaq")) ?? {};
  const base = scenarios.find((row) => row.case === "Base") ?? {};
  const expectedMultiple = scenarios.reduce((sum, row) => sum + row.probability * row.returnMultipleAt3810, 0);
  const expectedIrr = Math.pow(expectedMultiple, 1 / 3) - 1;

  const scenarioRows = scenarios.map((row) => ({
    Case: row.case, Probability: pct(row.probability), "ARR CAGR": pct(row.arrCagr),
    "Year-3 ARR": millions(row.year3ArrMillions), "Exit multiple": `${row.exitArrMultiple.toFixed(0)}x`,
    "Net equity": billions(row.netEquityBillions), "Share price": dollars(row.impliedSharePrice),
    "3-year IRR": pct(row.irrAt3810),
  }));
  const fundingRows = rounds.map((row) => ({
    Round: row.round, Date: row.date, Raised: millions(row.amountMillions),
    "Price/share": dollars(row.price), "Post-money": `$${row.postMoneyMillions.toLocaleString()}M`,
    "New money": pctWhole(row.newMoneyPct),
  }));
  const sensitivityRows = sensitivity.map((row) => ({
    Entry: dollars(row.entryPrice), Reference: row.reference,
    Bear: pct(row.bearIrr), Base: pct(row.baseIrr), Bull: pct(row.bullIrr),
  }));

  return <article className="report-content glean-report" aria-label="Glean private-market investment report">
    <header className="report-hero glean-hero">
      <div className="report-kicker">PRIVATE-MARKET UNDERWRITING · 16 SEP 2026</div>
      <h1 data-data-app-title contentEditable={canEdit && mode === "edit"} suppressContentEditableWarning
        onBlur={canEdit && mode === "edit" ? (event) => setAppTitle(event.currentTarget.textContent.trim() || appTitle) : undefined}
        onKeyDown={canEdit && mode === "edit" ? (event) => {
          if (event.key === "Enter") { event.preventDefault(); event.currentTarget.blur(); }
        } : undefined}>{appTitle}</h1>
      <RichNarrative id="report:description" className="report-deck" label="Edit report introduction"
        value="A source-backed underwriting memo for a small, illiquid satellite position—covering product moat, growth, secondary pricing, modeled ownership, exit paths, venue choice, and the price discipline required for asymmetric returns." />
    </header>

    {visible("investment-summary") && <ReportSection id="investment-summary" title="Investment conclusion" queryId="arr_milestones"
      queryIds={["arr_milestones", "market_marks", "valuation_scenarios"]}
      sourceRowsByQuery={{ arr_milestones: arr, market_marks: marks, valuation_scenarios: scenarios }}
      showHeading={false} className="report-summary glean-summary">
      <RichNarrative id="investment-summary:body" className="report-summary-lead" label="Edit investment conclusion"
        value={`## Conditional buy, not a chase\n\n**Conviction:** 7/10 on the company, 6/10 near the ${dollars(forge.price)} Forge mark, and 4/10 above $50. Glean has crossed from promising application to scaled enterprise-AI platform: company-reported ARR rose from $100M to $300M in 15 months. The market, however, is fragmented: Forge implies ${billions(forge.impliedValuationBillions)} while Nasdaq Private Market implies ${billions(npm.impliedValuationBillions)}.\n\nAt ${dollars(forge.price)} plus a modeled 5% entry fee, the probability-weighted three-year outcome is ${multiple(expectedMultiple)} and roughly **${pct(expectedIrr)} annualized**. That is attractive for a satellite position, but not enough to ignore transfer restrictions, preferred/common differences, information asymmetry, future dilution, or the possibility of no liquidity by 2029.\n\n**Decision rule:** pursue direct or clean SPV exposure at **$38–$42**, tolerate up to **$45** only with current financials and clean terms, and pass above $45 absent a fresh ARR/retention step-up.`} />
    </ReportSection>}

    <div className="report-facts report-facts-four" aria-label="Key investment metrics">
      <MetricCard id="metric-arr" title="Latest reported ARR" queryId="arr_milestones" sourceRows={arr}
        value="$300M" comparison="3× in 15 months" description="Company-reported, unaudited ARR as of May 28, 2026."
        trendValues={arr.map((row) => row.arrMillions)} />
      <MetricCard id="metric-valuation" title="Forge implied value" queryId="market_marks" sourceRows={marks}
        value={billions(forge.impliedValuationBillions)} comparison={`${dollars(forge.price)} per share`}
        description="Provider estimate, not a confirmed executable quote." />
      <MetricCard id="metric-multiple" title="Current ARR multiple" queryId="market_marks" sourceRows={marks}
        value={`${forge.arrMultiple?.toFixed(1)}×`} comparison="vs. 24.9× on NPM"
        description="Implied equity value divided by $300M ARR." />
      <MetricCard id="metric-base-irr" title="Base-case 3-year IRR" queryId="valuation_scenarios" sourceRows={scenarios}
        value={pct(base.irrAt3810)} comparison={`${multiple(base.returnMultipleAt3810)} MOIC`}
        description="At $38.10 plus 5% fee; before taxes, carry, and exit costs." />
    </div>

    <section className="report-section">
      <Narrative id="business-quality" title="Why Glean matters" queryId="arr_milestones" rows={arr}
        value="Glean is building the permission-aware context layer for enterprise work: search, assistant, and agents across documents, SaaS systems, and internal knowledge. The economic promise is less about generic search and more about resolving identity, permissions, provenance, and company-specific context across fragmented systems. That layer can be durable because every connector, graph edge, permission check, and workflow increases deployment depth.\n\nThe strongest evidence is velocity and enterprise depth: $100M ARR in February 2025, $200M in December 2025, and $300M in May 2026; more than 27 billion documents indexed; more than 1,000 employees; Fortune 500 customer count nearly doubled year over year; and $1M-plus contracts nearly tripled in 2025. These are company disclosures—not audited financials—but they indicate genuine scale." />
      <EvidenceChart id="arr-growth" queryId="arr_milestones" title="Reported ARR reached $300M in 15 months"
        spec={arrSpec} rows={arr} sourceRows={arr} height={300}
        description="Company-reported ARR milestones; exact intra-period path is unknown." />
      <Narrative id="moat-risks" title="Moat versus the bear case" queryIds={["arr_milestones", "social_signals"]}
        rowsByQuery={{ arr_milestones: arr, social_signals: social }}
        value="**Bull case:** Glean owns the enterprise context and permission layer while remaining model-agnostic. Its 100-plus connectors, search relevance, knowledge graph, security posture, and expanding agent surface create implementation and workflow switching costs. The live X sample reinforced the category thesis: Glean announced a Salesforce AgentExchange MCP integration, while practitioners highlighted permissions, provenance, and evaluation as the hard part of useful agents.\n\n**Bear case:** Microsoft, Google, Salesforce, ServiceNow, Amazon, OpenAI, and Anthropic can bundle adjacent capabilities into existing seats and platforms. AI inference costs may suppress gross margin; services-heavy deployments may limit operating leverage; model improvements may commoditize retrieval; and security failures would be existential. Public disclosures omit net retention, gross margin, burn, customer concentration, and revenue quality—the numbers most likely to decide whether the current multiple is cheap or expensive." />
      <EvidenceTable id="social-evidence" title="Authenticated X evidence sample" queryId="social_signals" rows={social}
        columns={[
          { field: "date", label: "Date" }, { field: "source", label: "Source" },
          { field: "signal", label: "Signal" }, { field: "detail", label: "What it says" },
          { field: "confidence", label: "Confidence", presentation: "status" },
        ]} description="Bounded Latest-search sample from the user's authenticated Safari session; not a complete X scrape or a sentiment index." />
    </section>

    <section className="report-section">
      <Narrative id="technical-setup" title="Secondary-market setup: improving price, imperfect signal" queryId="market_marks" rows={marks}
        value={`The technical setup is constructive only because price has reset. Forge's ${dollars(forge.price)} mark is about 22% below the $49.02 Series F price and roughly 38% below Forge's approximate late-2025 peak near $61. That creates room for operating growth to catch up with valuation.\n\nThe warning is dispersion. Nasdaq Private Market's ${dollars(npm.price)} mark is 33% above Forge. Private-company marks can mix common and preferred shares, SPVs, stale indications, financing rounds, and different fully diluted share counts. They are price-discovery inputs—not a tape. A spread this wide makes security terms and actual order-book depth more important than the headline mark.`} />
      <EvidenceChart id="secondary-prices" queryId="market_marks" title="Private-market reference prices are widely dispersed"
        spec={priceSpec} rows={marks} sourceRows={marks} height={340}
        description="Primary financing prices and provider-derived estimates; none is necessarily executable." />
      <EvidenceTable id="funding-table" title="Priced funding history" queryId="funding_rounds" rows={fundingRows}
        columns={["Round", "Date", "Raised", "Price/share", "Post-money", "New money"].map((field) => ({ field, label: field }))}
        description="Public round data totals $774.5M raised. New-money ownership is amount divided by post-money value." />
    </section>

    <section className="report-section">
      <Narrative id="cap-table-note" title="Estimated cap table: useful shape, low precision" queryId="cap_table_estimate" rows={cap}
        value="A legal cap table is not public. The estimate below mechanically treats each priced round's amount divided by post-money valuation as new ownership, then dilutes earlier cohorts pro rata. It suggests roughly 42.5% remains with founders, employees, seed holders, and option pools combined; Series A through F cohorts account for the balance.\n\nDo not use these figures to infer an individual's ownership. Option-pool refreshes, tender offers, secondaries, SAFEs, debt, transfers, and share-class rights can materially change the result. For an actual purchase, request the current fully diluted share count, class, liquidation preference, conversion ratio, ROFR history, transfer restrictions, and latest charter." />
      <EvidenceChart id="cap-table" queryId="cap_table_estimate" title="Modeled ownership by financing cohort"
        spec={capSpec} rows={cap} sourceRows={cap} height={360}
        description="Sequential pro-rata dilution estimate, not Glean's legal cap table." />
    </section>

    <section className="report-section">
      <Narrative id="valuation-framework" title="Bull, base, bear and expected value" queryIds={["valuation_scenarios", "entry_sensitivity"]}
        rowsByQuery={{ valuation_scenarios: scenarios, entry_sensitivity: sensitivity }}
        value={`The model starts at $300M ARR and values Glean three years out on ARR, then deducts modeled dilution. Bear assumes 25% ARR CAGR and 8×; base 45% and 14×; bull 65% and 20×. Probabilities are 35% / 50% / 15%. At the Forge reference price, the probability-weighted outcome is ${multiple(expectedMultiple)} over three years.\n\nThe asymmetry is real but not spectacular: modeled downside is 0.68× while upside is 4.13×. The base case carries the result, so underwriting must focus on whether Glean can sustain at least mid-40s growth while preserving enterprise retention and gross margin. A lower entry price is the cleanest risk reducer because private-market terms are otherwise largely uncontrollable.`} />
      <EvidenceChart id="scenario-chart" queryId="valuation_scenarios" title="Three-year implied share price by scenario"
        spec={scenarioSpec} rows={scenarios} sourceRows={scenarios} height={300}
        description="Modeled diluted share price in September 2029; entry fee affects return, not exit price." />
      <EvidenceTable id="scenario-table" title="Scenario assumptions and outputs" queryId="valuation_scenarios" rows={scenarioRows}
        columns={Object.keys(scenarioRows[0] ?? {}).map((field) => ({ field, label: field }))}
        description="Illustrative probability-weighted model, not a forecast or guarantee." />
      <EvidenceTable id="entry-sensitivity" title="Entry price is the decisive variable" queryId="entry_sensitivity" rows={sensitivityRows}
        columns={Object.keys(sensitivityRows[0] ?? {}).map((field) => ({ field, label: field }))}
        description="Annualized three-year returns using the same scenario outcomes and a 5% entry fee." />
    </section>

    <section className="report-section">
      <Narrative id="exit-analysis" title="IPO is more likely than acquisition, but patience is required" queryId="exit_probabilities" rows={exits}
        value="Glean is financially large enough to be an IPO candidate, but scale alone does not create a timetable. Management previously emphasized the flexibility of remaining private, while also expressing a long-run desire to go public. No public S-1 was identified. The highest-probability window is 2028–2030, contingent on growth above roughly 35%, durable retention, and public-company-ready margins and controls.\n\nAcquisition is strategically plausible—ServiceNow's $2.85B Moveworks purchase validates the category—but Glean's likely $8B-plus clearing price narrows the buyer set. Salesforce, Amazon, or Oracle could value a neutral enterprise-context layer; Microsoft and Google face heavier product overlap. A long private hold remains a substantial outcome, so do not fund this position with capital needed inside five to seven years." />
      <EvidenceChart id="exit-probabilities" queryId="exit_probabilities" title="Subjective status by September 2029"
        spec={exitSpec} rows={exits} sourceRows={exits} height={300}
        description="Analyst judgment; mutually exclusive probabilities sum to 100%." />
    </section>

    <section className="report-section">
      <Narrative id="platform-choice" title="Best first platform: Hiive" queryId="platforms" rows={platforms}
        value="Hiive is the best first venue for this specific satellite position because Glean has traded there since July 2024, is included in the Hiive50 liquidity index, has a dedicated liquidity report, and the standard direct minimum is $25,000. Nasdaq Private Market / SecondMarket is the best institutional cross-check. Forge offers the richest public Glean price history, but its usual $100,000 direct minimum is poorly matched to a satellite allocation. EquityZen is the smaller-check fallback if an offering becomes available.\n\nUse venue ranking only after comparing the actual security. Prefer direct shares or a simple single-name SPV; avoid opaque multi-name funds, layered fees, carry without clear value, or common shares priced close to preferred without an explicit rights adjustment." />
      <EvidenceTable id="platform-table" title="Platform comparison" queryId="platforms" rows={platforms}
        columns={[
          { field: "platform", label: "Platform" }, { field: "gleanEvidence", label: "Glean liquidity evidence" },
          { field: "standardMinimum", label: "Typical minimum" }, { field: "structure", label: "Structure" },
          { field: "publishedFees", label: "Published fees" }, { field: "fit", label: "Best use" },
        ]} description="Minimums, fees, eligibility, and availability vary by deal and jurisdiction." />
      <div className="decision-grid">
        <Narrative id="position-framework" title="Satellite-position playbook" queryIds={["market_marks", "entry_sensitivity", "platforms"]}
          rowsByQuery={{ market_marks: marks, entry_sensitivity: sensitivity, platforms }}
          value="Size at 0.25%–0.75% of investable assets, with a hard cap of 1%, only if a total loss and five-to-seven-year lockup are tolerable. Stage in thirds: one at $38–$42 after diligence, one on a fresh operating update, and one only on better pricing or verified acceleration. Do not average up merely because an IPO rumor appears." />
        <Narrative id="kill-criteria" title="What would break the thesis" queryId="valuation_scenarios" rows={scenarios}
          value="Pause or exit the process if forward ARR growth falls below 35%, net retention is below 110%, gross margin is below 65%, customer concentration is material, platform bundling is displacing renewals, or the offered security lacks clean transfer and information rights. Reject a price above $45 unless new evidence materially raises the base case." />
      </div>
    </section>

    <RichNarrative id="report:disclosure" className="report-disclosure glean-disclosure" label="Edit disclosure"
      value="Research, not investment advice. Private securities are speculative, illiquid, hard to value, and can become worthless. Company ARR is unaudited; marketplace marks are not firm quotes. The cap table, scenario probabilities, exit timing, and position sizing are analyst estimates. The authenticated X review was a bounded sample, not an exhaustive scrape. Verify accreditation, offering documents, taxes, fees, share class, transfer restrictions, and issuer approval with qualified professionals before investing." />
  </article>;
}
