import { useMemo, useState } from 'react'
import { ArrowRight, Check, Download, Sparkles } from 'lucide-react'
import { api } from './api'
import { LinkRow, money, NodeDetail, StatusPill, ViewHeader } from './components'
import { hypothesisReach, iconFor, modelCase, TYPE_ORDER, type Graph } from './graph'
import { Icon } from './icons'
import { download } from './util'
import type { DesignPack, GraphNode, LensId, ModeId, PackDetail } from './types'

function Tile({ node, pack, onPick }: { node: GraphNode; pack: PackDetail; onPick: (id: string) => void }) {
  return (
    <button type="button" className="reason-node" onClick={() => onPick(node.id)}>
      <span className="link-ico"><Icon name={iconFor(node, pack)} size={16} /></span>
      <span>
        <small>{node.type}</small>
        <b>{node.title}</b>
        <em>{node.evidenceStatus || 'unverified'}</em>
      </span>
    </button>
  )
}

export function SignalsView({
  pack,
  graph,
  lens,
  onPick,
  onNavigate,
}: {
  pack: PackDetail
  graph: Graph
  lens: LensId
  onPick: (id: string) => void
  onNavigate: (mode: ModeId) => void
}) {
  const hypotheses = graph.nodes.filter((node) => node.type === 'hypothesis')
  const [index, setIndex] = useState(0)
  const hypothesis = hypotheses[Math.min(index, hypotheses.length - 1)]
  if (!hypothesis) return <p className="quiet">This pack has no value hypotheses yet.</p>
  const reach = hypothesisReach(graph, hypothesis.id)
  const delivery = [...reach.capabilities, ...reach.partners.slice(0, 1), ...reach.offers.slice(0, 1)]
  const stages: { title: string; note: string; nodes: GraphNode[] }[] = [
    { title: '01 · Executive intent', note: 'Board objective', nodes: reach.boards },
    { title: '02 · Accountability', note: 'Functions and personas', nodes: [...reach.functions, ...reach.personas.slice(0, 2)] },
    { title: '03 · Observed or suspected signals', note: 'No causal claim', nodes: reach.signals },
    { title: '04 · Testable hypothesis', note: 'Needs experiment', nodes: [hypothesis] },
    { title: '05 · Outcome measures', note: 'Baseline required', nodes: reach.metrics },
    { title: '06 · Delivery & commercial', note: 'After validation', nodes: delivery },
  ]
  return (
    <section className="section">
      <ViewHeader
        overline={`Cross-silo reasoning canvas · ${pack.design.industry}`}
        title="Connect the business decision to what the signals might mean."
        text="Choose a hypothesis. The evidence chain is built from graph relationships, not from a fixed product slide."
        pill="Hypothesis ≠ proof"
        tone="warn"
      />
      <div className="case-row">
        {hypotheses.map((node, number) => (
          <button key={node.id} type="button" className={`econ-case ${number === index ? 'active' : ''}`} onClick={() => setIndex(number)}>
            <small>Value thread {number + 1}</small>
            <b>{node.title}</b>
          </button>
        ))}
      </div>
      <div className="reason-title">
        <span className="reason-emblem"><Icon name="network" size={26} /></span>
        <div>
          <small>Selected business hypothesis</small>
          <h3>{hypothesis.title}</h3>
          <p>{hypothesis.summary}</p>
        </div>
        <button type="button" className="ui-btn ghost-light" onClick={() => onNavigate('reasoning')}>
          Watch an agent reason on live signals <ArrowRight size={15} />
        </button>
      </div>
      <div className="reason-chain">
        {stages.map((stage) => (
          <div key={stage.title} className="reason-stage">
            <div className="reason-stage-header">
              <span>{stage.title}</span>
              <small>{stage.note}</small>
            </div>
            {stage.nodes.length ? stage.nodes.slice(0, 4).map((node) => <Tile key={node.id} node={node} pack={pack} onPick={onPick} />) : <div className="reason-empty">Evidence or owner required</div>}
          </div>
        ))}
      </div>
      <div className="reason-foot">
        <div className="insight-panel">
          <h3><Icon name="database" size={16} /> What must we establish?</h3>
          {reach.sources.map((node) => (
            <div key={node.id} className="linked-evidence">
              <b>{node.title}</b>
              <span>Data custodian · permitted use · quality · time boundary</span>
            </div>
          ))}
          {reach.sources.length === 0 && <p>No data sources linked. Collect customer evidence first.</p>}
          <p className="footnote">Status: {hypothesis.evidenceStatus}. Financial numbers, where present, are synthetic.</p>
        </div>
        <div className="insight-panel">
          <h3><Icon name="shield" size={16} /> What could invalidate the idea?</h3>
          {reach.risks.map((node) => (
            <div key={node.id} className="linked-evidence">
              <b>{node.title}</b>
              <span>{node.summary}</span>
            </div>
          ))}
          <p className="footnote">Compare against a control group or before/after baseline. Check alternative explanations and double counting.</p>
        </div>
        <div className="insight-panel">
          <h3><Icon name="handshake" size={16} /> {lens === 'cisco' ? 'Which capabilities apply?' : 'What might a partner monetise?'}</h3>
          {(lens === 'cisco' ? reach.capabilities : reach.offers).map((node) => (
            <div key={node.id} className="linked-evidence">
              <b>{node.title}</b>
              <span>{node.summary}</span>
            </div>
          ))}
          <p className="footnote">Partner fees and Cisco opportunity are kept apart from customer value.</p>
        </div>
      </div>
    </section>
  )
}

export function ExplorerView({ pack, graph, selected, onSelect }: { pack: PackDetail; graph: Graph; selected: string; onSelect: (id: string) => void }) {
  const [type, setType] = useState('all')
  const [search, setSearch] = useState('')
  const types = ['all', ...TYPE_ORDER.filter((kind) => graph.nodes.some((node) => node.type === kind))]
  const term = search.trim().toLowerCase()
  const nodes = graph.nodes.filter(
    (node) => (type === 'all' || node.type === type) && (!term || `${node.title} ${node.summary} ${node.type}`.toLowerCase().includes(term)),
  )
  const shown = graph.byId.has(selected) ? selected : nodes[0]?.id || ''
  return (
    <section className="section">
      <ViewHeader
        overline="Dynamic entity explorer"
        title="Follow the evidence, not the product catalogue."
        text="Open any connected entity to navigate its business, technology and commercial context."
        pill={`${nodes.length} matching entities`}
      />
      <div className="vbody">
        <aside className="panel">
          <h3>Choose a value layer</h3>
          <div className="filter-list">
            {types.map((kind) => (
              <button key={kind} type="button" className={`chip ${type === kind ? 'on' : ''}`} onClick={() => setType(kind)}>
                {kind === 'all' ? 'All entities' : kind}
              </button>
            ))}
          </div>
          <p className="quiet">The layers come from each pack's entity types plus overlay personas.</p>
          <span className="detail-sub">Enterprise value streams</span>
          <div className="connected">
            {graph.nodes.filter((node) => node.type === 'stream').map((node) => (
              <LinkRow key={node.id} node={node} note={node.summary} onPick={onSelect} />
            ))}
          </div>
        </aside>
        <div className="panel">
          <input className="search" placeholder="Search objectives, personas, signals, partners…" value={search} onChange={(event) => setSearch(event.target.value)} aria-label="Search graph entities" />
          <div className="node-cards">
            {nodes.slice(0, 48).map((node) => (
              <button key={node.id} type="button" className={`node-card ${shown === node.id ? 'active' : ''}`} onClick={() => onSelect(node.id)}>
                <span className="chip-head">
                  <Icon name={iconFor(node, pack)} size={16} />
                  <span className="node-type">{node.type}</span>
                </span>
                <b>{node.title}</b>
                <small>{node.summary}</small>
              </button>
            ))}
          </div>
        </div>
        <aside className="panel">
          <NodeDetail graph={graph} id={shown} onPick={onSelect} />
        </aside>
      </div>
    </section>
  )
}

const EVIDENCE_STATES = ['all', 'observed', 'validated', 'hypothesis', 'unverified', 'illustrative']

export function EvidenceRiskView({ pack, graph, onPick }: { pack: PackDetail; graph: Graph; onPick: (id: string) => void }) {
  const [filter, setFilter] = useState('all')
  const rows =
    pack.design.evidenceRegister ||
    graph.nodes
      .filter((node) => ['board', 'signal', 'source', 'hypothesis'].includes(node.type))
      .map((node) => ({ id: `ev-${node.id}`, nodeId: node.id, status: node.evidenceStatus || 'unverified', dataOwner: 'To confirm', validationAction: 'Confirm evidence' }))
  const counts = rows.reduce<Record<string, number>>((acc, row) => ({ ...acc, [row.status]: (acc[row.status] || 0) + 1 }), {})
  const filtered = rows.filter((row) => filter === 'all' || row.status === filter)
  const risks = graph.nodes.filter((node) => node.type === 'risk')
  return (
    <section className="section">
      <ViewHeader
        overline="Trust, evidence & assurance"
        title="Separate signals, assumptions and validated value."
        text="Every high-impact assertion needs an owner, permission, baseline and verification method before it becomes a customer claim."
        pill={`${pack.design.status} pack`}
        tone="warn"
      />
      <div className="summary-stats three">
        <div className="stat"><small>Evidence-linked entities</small><b>{rows.length}</b><span>From the pack evidence register</span></div>
        <div className="stat"><small>Observed / validated</small><b>{(counts.observed || 0) + (counts.validated || 0)}</b><span>No synthetic claims promoted</span></div>
        <div className="stat"><small>To qualify</small><b>{(counts.hypothesis || 0) + (counts.unverified || 0) + (counts.illustrative || 0)}</b><span>Customer validation required</span></div>
      </div>
      <div className="track-bar">
        {EVIDENCE_STATES.map((state) => (
          <button key={state} type="button" className={`chip ${filter === state ? 'on' : ''}`} onClick={() => setFilter(state)}>
            {state === 'all' ? 'All evidence' : state} <span className="count">{state === 'all' ? rows.length : counts[state] || 0}</span>
          </button>
        ))}
      </div>
      <div className="evidence-grid">
        <div className="evidence-list">
          {filtered.map((row) => {
            const node = graph.byId.get(row.nodeId)
            return (
              <button key={row.id} type="button" className="evidence-card" onClick={() => onPick(row.nodeId)}>
                <span className="evidence-icon"><Icon name={iconFor(node, pack)} size={17} /></span>
                <span>
                  <b>{node?.title || row.nodeId}</b>
                  <small>{node?.type || 'record'} · {row.status} · owner {row.dataOwner}</small>
                  <em>{row.validationAction}</em>
                </span>
                <ArrowRight size={15} />
              </button>
            )
          })}
          {filtered.length === 0 && <div className="insight-panel">No entities in this evidence state.</div>}
        </div>
        <aside className="evidence-side">
          <div className="insight-panel">
            <h3>Evidence acceptance gates</h3>
            {['Decision owner and intended outcome', 'Data provenance and permission', 'Measurable baseline and boundaries', 'Alternative explanations and counterfactual', 'Risk, accessibility and security sign-off', 'Benefits realisation and review owner'].map((gate) => (
              <div key={gate} className="gate"><Check size={14} /> {gate}</div>
            ))}
          </div>
          <div className="insight-panel">
            <h3>Assurance controls</h3>
            {risks.map((node) => (
              <button key={node.id} type="button" className="linked-evidence as-button" onClick={() => onPick(node.id)}>
                <b>{node.title}</b>
                <span>{node.summary}</span>
              </button>
            ))}
          </div>
          <div className="insight-panel">
            <h3>Missing customer evidence</h3>
            {(pack.design.validation?.missingData || []).map((item) => (
              <div key={item} className="linked-evidence">{item}</div>
            ))}
            <p className="footnote">A graph relationship does not demonstrate an integration, causal effect, contractual commitment or achieved ROI.</p>
          </div>
        </aside>
      </div>
    </section>
  )
}

export function EconomicsView({ graph, lens }: { graph: Graph; lens: LensId }) {
  const cases = graph.nodes.filter((node) => node.type === 'hypothesis' && node.financialModel)
  const [index, setIndex] = useState(0)
  const [pct, setPct] = useState<number | null>(null)
  const [capture, setCapture] = useState<number | null>(null)
  const node = cases[Math.min(index, cases.length - 1)]
  const numbers = node ? modelCase(node, pct ?? undefined, capture ?? undefined) : null
  if (!node || !numbers) return <p className="quiet">No hypothesis in this pack carries a financial model.</p>
  const bars = [
    { label: 'Cost pool', value: numbers.pool, tone: '' },
    { label: 'Gross', value: numbers.gross, tone: '' },
    { label: 'Net / year', value: numbers.net, tone: 'green' },
    { label: 'Implement', value: numbers.investment, tone: 'orange' },
  ]
  const max = Math.max(...bars.map((bar) => Math.abs(bar.value)), 1)
  const reach = hypothesisReach(graph, node.id)
  return (
    <section className="section">
      <ViewHeader
        overline="Illustrative value economics"
        title="Qualify the financial hypothesis before buying technology."
        text="Editable synthetic assumptions. The result is a discussion aid, not a customer forecast."
        pill="Unvalidated · modelled"
        tone="warn"
      />
      <div className="case-row">
        {cases.map((item, number) => (
          <button key={item.id} type="button" className={`econ-case ${number === index ? 'active' : ''}`} onClick={() => { setIndex(number); setPct(null); setCapture(null) }}>
            <small>Hypothesis {number + 1}</small>
            <b>{item.title}</b>
          </button>
        ))}
      </div>
      <div className="summary-stats">
        <div className="stat"><small>Gross annual value</small><b>{money(numbers.gross)}</b><span>Before assurance and services</span></div>
        <div className="stat"><small>Net annual value</small><b>{money(numbers.net)}</b><span>After managed service charge</span></div>
        <div className="stat"><small>Year-one net</small><b>{money(numbers.firstYear)}</b><span>After investment</span></div>
        <div className="stat"><small>Simple payback</small><b>{Number.isFinite(numbers.payback) && numbers.payback >= 0 ? `${numbers.payback.toFixed(1)} mo` : 'N/A'}</b><span>Not risk-adjusted</span></div>
      </div>
      <div className="econ-grid">
        <div className="panel">
          <h3 className="detail-title">{node.title}</h3>
          <p className="quiet">{node.summary}</p>
          <label className="slider-row">
            <span className="slider-head"><span>Improvement opportunity</span><output>{numbers.pct}%</output></span>
            <input type="range" min={0} max={30} step={0.2} value={numbers.pct} onChange={(event) => setPct(Number(event.target.value))} />
          </label>
          <label className="slider-row">
            <span className="slider-head"><span>Realisation / capture factor</span><output>{Math.round(numbers.capture * 100)}%</output></span>
            <input type="range" min={0} max={100} step={5} value={Math.round(numbers.capture * 100)} onChange={(event) => setCapture(Number(event.target.value) / 100)} />
          </label>
          <div className="econ-chart">
            {bars.map((bar) => (
              <div key={bar.label} className="bar-wrap">
                <b>{money(bar.value)}</b>
                <div className={`bar ${bar.tone}`} style={{ height: `${Math.max(5, (130 * Math.abs(bar.value)) / max)}px` }} />
                <small>{bar.label}</small>
              </div>
            ))}
          </div>
        </div>
        <div className="panel">
          {lens === 'customer' && (
            <>
              <h3>Evidence needed to proceed</h3>
              <ol className="point-list">
                {['Customer-owned baseline and measurement boundary', 'Benefits ownership, normalisation and control group', 'Risk limits, implementation and service costs', 'Sponsor approval and post-change verification'].map((item, number) => (
                  <li key={item} className="point-item"><span className="num">{number + 1}</span>{item}</li>
                ))}
              </ol>
            </>
          )}
          {lens === 'partner' && (
            <>
              <h3>Partner revenue view</h3>
              <p>Managed service hypothesis {money(numbers.service)} / year and implementation {money(numbers.investment)}. This is partner revenue, not customer benefit.</p>
              <div className="connected">{reach.offers.map((item) => <LinkRow key={item.id} node={item} note={item.summary} />)}</div>
            </>
          )}
          {lens === 'cisco' && (
            <>
              <h3>Capability dependencies</h3>
              <div className="connected">{reach.capabilities.map((item) => <LinkRow key={item.id} node={item} note={item.summary} />)}</div>
              <p className="quiet">No Cisco booking figure is stated or counted as customer value.</p>
            </>
          )}
          <div className="formula">
            <b>Transparent calculation</b>
            <br />Gross = addressable pool × opportunity % × capture factor.
            <br />Net / year = gross − annual service.
            <br />Year 1 = net / year − implementation.
            <br />Simple payback = investment ÷ monthly net benefit.
            <br /><br />Pool {money(numbers.pool)} · Integration {money(numbers.investment)} · Service {money(numbers.service)} / year
          </div>
          <p className="fact">Double counting across hypotheses is not removed here. See Compound Value for combined outcomes with overlap deducted.</p>
        </div>
      </div>
    </section>
  )
}

interface Discovery {
  customer: string
  sector: string
  scope: string
  objectives: string
  notes: string
}

const PLACEHOLDER: Record<string, string> = {
  function: 'Decision owner to confirm with customer',
  signal: 'Candidate operational signal — no observations collected',
  source: 'Potential source — confirm existence, rights and time window',
  hypothesis: 'Testable outcome hypothesis to be co-designed with customer',
  metric: 'Metric needs baseline, owner, units and assurance',
  capability: 'Capability candidate only after value case validation',
  partner: 'Delivery archetype and responsibilities to be confirmed',
  offer: 'Commercial construct to agree after scope and margin analysis',
  risk: 'Risk / constraint must be tested and signed off',
  stream: 'Reference value stream; mapping to customer requires validation',
}

function makeStarter(template: DesignPack, discovery: Discovery): DesignPack {
  const pack = JSON.parse(JSON.stringify(template)) as DesignPack & Record<string, unknown>
  const goals = discovery.objectives.split(/\r?\n/).map((line) => line.trim()).filter(Boolean).slice(0, 3)
  const account = discovery.customer.trim() || 'Unspecified customer'
  pack.packId = `draft-${discovery.sector}-${Date.now().toString(36)}`
  pack.name = `Discovery scaffold · ${account}`
  pack.customer = { name: account, sector: pack.industry, scope: discovery.scope || 'Scope to be confirmed' }
  pack.status = 'draft'
  pack.subtitle = 'Customer-led discovery · no validated evidence or financial claims'
  pack.provenance = { disclaimer: 'All hypotheses, measurements, vendor fit and partner offers remain unverified; no synthetic pack metrics retained.' }
  let board = 0
  for (const node of pack.nodes) {
    node.evidenceStatus = 'unverified'
    node.confidence = 'to-validate'
    if (node.type === 'board') {
      node.title = goals[board] || `Board priority ${board + 1} — to discover`
      node.summary = 'Customer statement; confirm KPI and accountable sponsor'
      board += 1
    } else {
      node.summary = PLACEHOLDER[node.type] || node.summary
    }
    if (node.type === 'hypothesis') {
      node.title = `Hypothesis ${node.id.slice(1)} — to co-design`
      node.financialModel = { annualPoolGBP: 0, opportunityPct: 0, captureFactor: 0, implementationGBP: 0, serviceAnnualGBP: 0, currency: 'GBP' }
    }
    if (node.type === 'signal') node.title = `Signal ${node.id.slice(1)} — to investigate`
    if (node.type === 'source') node.title = `Data source ${node.id.slice(1)} — not connected`
    if (node.type === 'metric') node.title = `KPI ${node.id.slice(1)} — baseline missing`
  }
  pack.validation = {
    stage: 'Discovery — draft only',
    missingData: ['Confirm objectives and decision owners', 'Collect permitted operational baseline', 'Identify signals and source owners', 'Co-design testable intervention', 'Quantify investment and service economics', 'Check privacy, security, accessibility and safety'],
  }
  pack.evidenceRegister = pack.nodes
    .filter((node) => ['board', 'source', 'signal', 'hypothesis'].includes(node.type))
    .map((node) => ({ id: `ev-${node.id}`, nodeId: node.id, status: 'unverified', dataOwner: 'Unknown', validationAction: 'Customer confirmation, sourcing and assurance required' }))
  return pack
}

function briefMarkdown(discovery: Discovery) {
  return `# Customer discovery · ${discovery.customer || 'Not named'}\n\n> DRAFT. Record only assertions supplied by the customer.\n\nIndustry: ${discovery.sector}\nScope: ${discovery.scope || 'Not yet confirmed'}\n\n## Customer-stated objectives\n${discovery.objectives || 'Not yet captured'}\n\n## Conversation notes\n${discovery.notes || 'Not yet captured'}\n\n## Next questions\n- Who owns each goal and its KPI?\n- Which personas act on the signals?\n- What is the baseline, boundary and time window?\n- Which data sources are available and permitted?\n- What evidence would falsify the proposed hypotheses?\n- What risk, privacy, security and accessibility controls apply?\n`
}

export function NewCustomerView({ pack }: { pack: PackDetail }) {
  const [form, setForm] = useState<Discovery>({ customer: '', sector: pack.design.packId, scope: '', objectives: '', notes: '' })
  const [draft, setDraft] = useState<DesignPack | null>(null)
  const [check, setCheck] = useState<{ ok: boolean; errors: string[] } | null>(null)
  const sameSector = form.sector === pack.design.packId
  const preview = useMemo(() => draft?.nodes.filter((node) => node.type === 'board') || [], [draft])
  async function generate() {
    const built = makeStarter(pack.design, form)
    setDraft(built)
    try {
      setCheck(await api.validate(built))
    } catch (error) {
      setCheck({ ok: false, errors: [error instanceof Error ? error.message : 'Validation failed'] })
    }
  }
  const field = (key: keyof Discovery) => ({ value: form[key], onChange: (event: { target: { value: string } }) => setForm({ ...form, [key]: event.target.value }) })
  return (
    <section className="section">
      <ViewHeader
        overline="Start from the first customer conversation"
        title="Create a draft Value Twin before you have a technical digital twin."
        text="Enter only what the customer actually said. The studio creates a connected discovery scaffold and leaves unverified fields empty."
        pill="Local · no AI API"
      />
      <div className="discovery-shell">
        <form className="panel discovery-form" onSubmit={(event) => { event.preventDefault(); void generate() }}>
          <h3>01 / Customer discovery intake</h3>
          <label>Customer or illustrative account<input className="search" maxLength={100} placeholder="Customer / project name" {...field('customer')} /></label>
          <label>
            Industry template
            <select className="search" {...field('sector')}>
              <option value="office">Intelligent workplace / buildings</option>
              <option value="retail">Retail estate</option>
              <option value="manufacturing">Manufacturing / industrial</option>
            </select>
          </label>
          {!sameSector && <p className="fact">Switch the loaded knowledge pack to this industry to use its graph as the template. The current pack is used until then.</p>}
          <label>Organisation / scope<input className="search" maxLength={220} placeholder="e.g. UK office portfolio, 12 buildings" {...field('scope')} /></label>
          <label>Board or executive objectives (one per line)<textarea className="search" rows={4} placeholder={'Reduce cost while improving employee experience\nReduce operational carbon'} {...field('objectives')} /></label>
          <label>What was actually said? What remains unknown?<textarea className="search" rows={4} {...field('notes')} /></label>
          <div className="row-actions">
            <button type="submit" className="ui-btn primary"><Sparkles size={15} /> Generate draft connected pack</button>
            <button type="button" className="ui-btn" onClick={() => download(briefMarkdown(form), 'customer-discovery-draft.md', 'text/markdown')}><Download size={15} /> Export discovery brief</button>
          </div>
          <p className="footnote">The draft keeps the graph shape but clears titles, evidence and financial values. It is never loaded as a runtime pack.</p>
        </form>
        <aside className="discovery-help">
          {draft ? (
            <div className="insight-panel">
              <span className="overline">Draft generated · {draft.status}</span>
              <h3>{draft.name}</h3>
              <StatusPill tone={check?.ok ? 'ok' : 'warn'}>{check ? (check.ok ? 'Schema and links valid' : `${check.errors.length} validation issue(s)`) : 'Validating…'}</StatusPill>
              {check && !check.ok && <pre className="errors">{check.errors.join('\n')}</pre>}
              <span className="detail-sub">Board objectives captured</span>
              {preview.map((node) => <div key={node.id} className="linked-evidence"><b>{node.title}</b><span>{node.summary}</span></div>)}
              <p className="quiet">{draft.nodes.length} nodes · {draft.edges.length} links · every node unverified.</p>
              <button type="button" className="ui-btn" onClick={() => download(JSON.stringify(draft, null, 2), `${draft.packId}.json`, 'application/json')}><Download size={15} /> Download draft pack JSON</button>
            </div>
          ) : (
            <div className="insight-panel">
              <span className="overline">What gets generated</span>
              <h3>An accountable graph scaffold</h3>
              {['Customer objectives and decision owners', 'Signal and source questions', 'Unvalidated value hypotheses', 'Metrics, risk controls and capability placeholders', 'Presenter scenes and relationship tracks'].map((item, number) => (
                <div key={item} className="onboard-step"><b>{number + 1}</b><span>{item}</span></div>
              ))}
            </div>
          )}
          <div className="insight-panel">
            <h3>What happens next?</h3>
            <p>Download the draft, run the design-time playbooks with customer-approved research, add personas to the overlay, then validate it in Pack Studio.</p>
            <p className="footnote">The studio is a deterministic renderer. No model reads customer records in the browser.</p>
          </div>
        </aside>
      </div>
    </section>
  )
}
