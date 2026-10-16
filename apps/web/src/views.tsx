import { useEffect, useMemo, useState } from 'react'
import {
  Background,
  Handle,
  Position,
  ReactFlow,
  type Node,
  type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { api } from './api'
import { Building, Chain, Drawer, money, nodeById, StatusPill } from './components'
import { Icon } from './icons'
import type {
  DiscoveryDocument,
  DiscoveryInput,
  DiscoveryLayerId,
  DiscoveryStageAgent,
  LensId,
  PackDetail,
  PublicRun,
  TraceEvent,
} from './types'

type AgentData = { title: string; hosting: string; status: string }

function AgentNode({ data }: NodeProps<Node<AgentData>>) {
  return (
    <div className={`agent-node ${data.status}`}>
      <Handle type="target" position={Position.Left} />
      <strong>{data.title}</strong>
      <em>{data.hosting}</em>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}

type ConceptData = { title: string; layer: string; evidence: string; confidence: string; selected: boolean }

function ConceptNode({ data }: NodeProps<Node<ConceptData>>) {
  return (
    <div className={`concept-node layer-${data.layer}${data.selected ? ' on' : ''}`}>
      <Handle type="target" position={Position.Top} />
      <span className="concept-tag">{data.evidence.replace(/_/g, ' ')}</span>
      <strong>{data.title}</strong>
      <em>{data.confidence} confidence</em>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

const nodeTypes = { agent: AgentNode, concept: ConceptNode }

export function StoryView({
  pack,
  lens,
  index,
  setIndex,
  notes,
  setNotes,
}: {
  pack: PackDetail
  lens: LensId
  index: number
  setIndex: (value: number) => void
  notes: boolean
  setNotes: (value: boolean) => void
}) {
  const scenes = pack.design.story
  const scene = scenes[index]
  const lensCopy = pack.design.lenses[lens]
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === 'ArrowRight') setIndex(Math.min(scenes.length - 1, index + 1))
      if (event.key === 'ArrowLeft') setIndex(Math.max(0, index - 1))
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [index, scenes.length, setIndex])
  const focusLabel = scene.focusNodeIds
    .map((id) => nodeById(pack.design.nodes, id)?.type)
    .filter(Boolean)[0]
  return (
    <section className="section">
      <ol className="steps" aria-label="Story steps">
        {scenes.map((item, step) => (
          <li key={item.id}>
            <button
              type="button"
              className={step === index ? 'step active' : step < index ? 'step done' : 'step'}
              aria-current={step === index ? 'step' : undefined}
              onClick={() => setIndex(step)}
            >
              <b>{step + 1}</b>
              {item.title}
            </button>
          </li>
        ))}
      </ol>
      <div className="scene-grid">
        <Building
          src={pack.imageUrl}
          hotspots={pack.design.scene.hotspots}
          nodes={pack.design.nodes}
          active={scene.focusNodeIds}
          eyebrow={focusLabel ? `${scene.title} · ${focusLabel} focus` : scene.title}
          badge={scene.headline}
        />
        <article className="card story-copy">
          <span className="overline">{scene.eyebrow}</span>
          <h2>{scene.headline}</h2>
          <p className="lead">{scene.explanation}</p>
          <div className="rule" />
          <ol className="point-list">
            {scene.keyPoints.map((point, number) => (
              <li key={point} className="point-item">
                <span className="num">{number + 1}</span>
                {point}
              </li>
            ))}
          </ol>
          <div className="lens-callout">
            <Icon name={lensCopy?.icon} />
            <div>
              <span className="smlabel">{lensCopy?.label} perspective</span>
              <p>{scene.lensTalkingPoints[lens]}</p>
            </div>
          </div>
        </article>
      </div>
      <footer className="footer-bar">
        <p>
          <strong>{scene.title}</strong>
          <span>{scene.transition}</span>
        </p>
        <div className="row-actions">
          <button type="button" className="ui-btn" onClick={() => setNotes(true)}>
            Presenter notes
          </button>
          <button type="button" className="ui-btn" onClick={() => setIndex(Math.max(0, index - 1))} disabled={index === 0}>
            Back
          </button>
          <button
            type="button"
            className="ui-btn primary"
            onClick={() => setIndex(Math.min(scenes.length - 1, index + 1))}
            disabled={index === scenes.length - 1}
          >
            Continue
          </button>
        </div>
      </footer>
      <Drawer open={notes} title="Presenter notes" onClose={() => setNotes(false)}>
        <p>{scene.presenterNotes}</p>
        <p className="quiet">{scene.transition}</p>
        <p>
          <strong>{lensCopy?.label}. </strong>
          {scene.lensTalkingPoints[lens]}
        </p>
      </Drawer>
    </section>
  )
}

export function TwinView({ pack, lens, onPick }: { pack: PackDetail; lens: LensId; onPick?: (id: string) => void }) {
  const [trackId, setTrackId] = useState(pack.design.tracks[0]?.id || '')
  const [selected, setSelected] = useState(pack.design.tracks[0]?.nodeIds[0] || '')
  useEffect(() => {
    const track = pack.design.tracks[0]
    setTrackId(track?.id || '')
    setSelected(track?.nodeIds[0] || '')
  }, [pack])
  const track = pack.design.tracks.find((item) => item.id === trackId) || pack.design.tracks[0]
  const node = nodeById(pack.design.nodes, selected)
  const related = pack.design.edges.filter((edge) => edge.from === selected || edge.to === selected)
  const lensNodes = pack.design.nodes.filter((item) =>
    lens === 'customer' ? ['board', 'metric', 'hypothesis'].includes(item.type) : lens === 'partner' ? item.type === 'offer' || item.type === 'partner' : item.type === 'capability',
  )
  return (
    <section className="stage column-stage">
      <div className="visual-stack">
        <Building
          src={pack.imageUrl}
          hotspots={pack.design.scene.hotspots}
          nodes={pack.design.nodes}
          active={track?.nodeIds || []}
          onPick={(id) => {
            setSelected(id)
            onPick?.(id)
          }}
        />
        <div className="track-bar">
          {pack.design.tracks.map((item) => (
            <button key={item.id} type="button" className={item.id === track?.id ? 'chip on' : 'chip'} onClick={() => { setTrackId(item.id); setSelected(item.nodeIds[0] || '') }}>
              {item.label}
            </button>
          ))}
        </div>
        {track && (
          <Chain
            ids={track.nodeIds}
            nodes={pack.design.nodes}
            edges={pack.design.edges}
            selected={selected}
            onSelect={setSelected}
          />
        )}
      </div>
      <aside className="panel">
        {node ? (
          <>
            <p className="kicker">{node.type} · {node.evidenceStatus}</p>
            <h2>{node.title}</h2>
            <p>{node.summary}</p>
            {node.financialModel && (
              <div className="callout">
                <StatusPill tone="warn">Illustrative model inputs</StatusPill>
                <p>These figures are pack assumptions. They are not a measured customer result.</p>
                <ul>
                  {node.financialModel.annualPoolGBP != null && <li>Addressable pool {money(node.financialModel.annualPoolGBP)}</li>}
                  {node.financialModel.opportunityPct != null && <li>Opportunity assumption {node.financialModel.opportunityPct}%</li>}
                  {node.financialModel.serviceAnnualGBP != null && <li>Partner service hypothesis {money(node.financialModel.serviceAnnualGBP)}</li>}
                </ul>
              </div>
            )}
            <h3>Relationships</h3>
            <ul className="rel-list">
              {related.map((edge) => (
                <li key={`${edge.from}-${edge.relation}-${edge.to}`}>
                  <button type="button" onClick={() => setSelected(edge.from === selected ? edge.to : edge.from)}>
                    <span>{edge.relation}</span>
                    {nodeById(pack.design.nodes, edge.from === selected ? edge.to : edge.from)?.title}
                  </button>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p>Select a node on the chain.</p>
        )}
        <h3>{pack.design.lenses[lens]?.label}</h3>
        <ul className="quiet-list">
          {lensNodes.slice(0, 4).map((item) => (
            <li key={item.id}>{item.title}</li>
          ))}
        </ul>
      </aside>
    </section>
  )
}

const FLOW = ['sense', 'context', 'value', 'plan', 'guard', 'human', 'act', 'verify']

export function LiveView({
  pack,
  run,
  busy,
  error,
  orchestrator,
  setOrchestrator,
  transport,
  setTransport,
  onRun,
  onPause,
  onStep,
  onDecide,
}: {
  pack: PackDetail
  run: PublicRun | null
  busy: boolean
  error: string
  orchestrator: string
  setOrchestrator: (value: string) => void
  transport: string
  setTransport: (value: string) => void
  onRun: () => void
  onPause: () => void
  onStep: () => void
  onDecide: (decision: 'approved' | 'rejected', actor: string, rationale: string) => void
}) {
  const [replay, setReplay] = useState(false)
  const [cursor, setCursor] = useState(0)
  const [actor, setActor] = useState('Facilities reviewer')
  const [rationale, setRationale] = useState('')
  const [notes, setNotes] = useState(false)
  const events = run?.events || []
  useEffect(() => {
    setReplay(false)
    setCursor(Math.max(0, events.length - 1))
  }, [run?.run.id, events.length])
  const shown = replay ? events[Math.min(cursor, events.length - 1)] : events[events.length - 1]
  const active = shown?.graphRefs || pack.intent.valueIntent.primaryRefIds
  const done = new Set(events.filter((event) => event.stage === 'complete' || event.stage === 'decision').map((event) => event.agent))
  const workflow = pack.scenario.workflow.find((step) => step.agent === shown?.agent)
  return (
    <section className="section">
      <ol className="steps" aria-live="polite" aria-label="Agent hand-offs">
        {FLOW.map((id, number) => {
          const agent = pack.network.find((item) => item.id === id)
          const current = shown?.agent === id
          return (
            <li key={id}>
              <span className={current ? 'step active' : done.has(id) ? 'step done' : 'step'}>
                <b>{number + 1}</b>
                {agent?.title || id}
              </span>
            </li>
          )
        })}
      </ol>
      <div className="stage">
      <div className="visual-stack">
        <Building
          src={pack.imageUrl}
          hotspots={pack.design.scene.hotspots}
          nodes={pack.design.nodes}
          active={active}
          eyebrow={replay ? 'Recorded trace replay' : run ? `Live audit stream · ${run.run.state}` : 'Ready · synthetic signals'}
          badge={shown ? `${shown.type} · ${shown.evidenceStatus}` : pack.intent.presentation.title}
        />
        <p className="trace-line">trace {run?.run.traceId || 'not started'}</p>
      </div>
      <aside className="panel">
        <div className="control-row">
          <label>
            Orchestrator
            <select value={orchestrator} onChange={(event) => setOrchestrator(event.target.value)} disabled={Boolean(run)}>
              <option value="deterministic">Deterministic</option>
              <option value="langgraph">LangGraph</option>
            </select>
          </label>
          <label>
            Context transport
            <select value={transport} onChange={(event) => setTransport(event.target.value)} disabled={Boolean(run)}>
              <option value="local">In-process</option>
              <option value="a2a">A2A service</option>
            </select>
          </label>
        </div>
        <div className="row-actions">
          <button type="button" className="primary" onClick={onRun} disabled={busy || Boolean(run)}>
            Run
          </button>
          <button type="button" onClick={onPause} disabled={!run || run.run.orchestrator === 'langgraph'}>
            Pause
          </button>
          <button type="button" onClick={onStep} disabled={busy || run?.run.orchestrator === 'langgraph' || run?.run.state === 'AWAITING_APPROVAL'}>
            Step
          </button>
          <button type="button" onClick={() => setReplay((value) => !value)} disabled={events.length === 0}>
            {replay ? 'Follow live' : 'Replay'}
          </button>
          <button type="button" onClick={() => setNotes(true)}>
            Notes
          </button>
        </div>
        {replay && events.length > 0 && (
          <label className="scrub">
            Event {cursor + 1} / {events.length}
            <input
              type="range"
              min={0}
              max={events.length - 1}
              value={Math.min(cursor, events.length - 1)}
              onChange={(event) => setCursor(Number(event.target.value))}
            />
          </label>
        )}
        <p className="kicker">{run?.run.state || 'READY'} · {pack.scenario.status}</p>
        <h2>{shown?.message || pack.intent.presentation.title}</h2>
        <p>{workflow?.description || 'Start a run to watch signal, context, value, plan, policy, approval, simulated action and verification.'}</p>
        {shown && <EventBody event={shown} />}
        {error && <p className="error">{error}</p>}
        {run?.run.state === 'AWAITING_APPROVAL' && !replay && (
          <form
            className="approval"
            onSubmit={(event) => {
              event.preventDefault()
              onDecide('approved', actor, rationale)
            }}
          >
            <h3>Human approval</h3>
            <p>This approves a simulated local ticket only. It expires with the intent and plan hashes shown.</p>
            <label>
              Approver
              <input value={actor} onChange={(event) => setActor(event.target.value)} required minLength={2} />
            </label>
            <div className="row-actions">
              <button type="submit" className="primary">Approve simulated ticket</button>
              <button
                type="button"
                onClick={() => onDecide('rejected', actor, rationale || 'Rejected in review')}
              >
                Reject
              </button>
            </div>
            <label>
              Rationale
              <textarea value={rationale} onChange={(event) => setRationale(event.target.value)} rows={2} />
            </label>
            <p className="mono">Intent {run.run.intentHash.slice(0, 16)} · Plan {run.run.planHash?.slice(0, 16)}</p>
          </form>
        )}
        {run?.run.state === 'APPROVED' && (
          <p className="quiet">Approval is recorded. Step once to draft the simulated ticket, then again to record the unverified outcome.</p>
        )}
        {run?.run.state === 'COMPLETE_NOT_MEASURED' && <StatusPill tone="warn">NOT MEASURED</StatusPill>}
        {run?.run.ticket && (
          <div className="callout">
            <strong>{run.run.ticket.ticketType}</strong>
            <p>{run.run.ticket.summary}</p>
            <p className="quiet">External system written: no. Status {run.run.ticket.status}.</p>
          </div>
        )}
      </aside>
      </div>
      <Drawer open={notes} title="Run notes" onClose={() => setNotes(false)}>
        <p>{workflow?.detail || pack.scenario.subtitle}</p>
        <p className="quiet">Synthetic observations. Correlation here is not causation, and a drafted ticket is not a saving.</p>
      </Drawer>
    </section>
  )
}

function EventBody({ event }: { event: TraceEvent }) {
  const readings = Array.isArray(event.details.readings) ? (event.details.readings as { source: string; name: string; value: string }[]) : []
  const options = Array.isArray(event.details.options) ? (event.details.options as string[]) : []
  return (
    <div className="event-body">
      <p className="mono">
        {event.type} · {event.evidenceStatus} · {event.actor}
      </p>
      {readings.length > 0 && (
        <ul>
          {readings.map((reading) => (
            <li key={reading.name}>
              {reading.source}: {reading.name} = {reading.value}
            </li>
          ))}
        </ul>
      )}
      {options.length > 0 && (
        <ul>
          {options.map((option) => (
            <li key={option}>{option}</li>
          ))}
        </ul>
      )}
      {event.details.assertion ? <p>{String(event.details.assertion)}</p> : null}
      <p className="quiet">Graph refs {event.graphRefs.join(', ') || 'none'}</p>
    </div>
  )
}

export function NetworkView({ pack, run }: { pack: PackDetail; run: PublicRun | null }) {
  const events = run?.events || []
  const last = events[events.length - 1]
  const [selected, setSelected] = useState(last?.agent || 'context')
  useEffect(() => {
    if (last?.agent) setSelected(last.agent)
  }, [last?.eventId, last?.agent])
  const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const nodes = useMemo<Node<AgentData>[]>(() => {
    const ordered = FLOW.map((id) => pack.network.find((agent) => agent.id === id)).filter((agent) => agent != null)
    return ordered.map((agent, index) => {
      const done = events.some((event) => event.agent === agent.id && (event.stage === 'complete' || event.stage === 'decision'))
      const status = last?.agent === agent.id ? 'current' : done ? 'done' : 'idle'
      return {
        id: agent.id,
        type: 'agent',
        position: { x: (index % 4) * 240, y: Math.floor(index / 4) * 180 },
        data: { title: agent.title, hosting: agent.hosting, status },
      }
    })
  }, [pack.network, events, last?.agent])
  const edges = FLOW.slice(0, -1).map((id, index) => ({
    id: `${id}-${FLOW[index + 1]}`,
    source: id,
    target: FLOW[index + 1],
    type: 'smoothstep',
    animated: !reduced && last?.agent === FLOW[index + 1],
  }))
  const agent = pack.network.find((item) => item.id === selected)
  const event = [...events].reverse().find((item) => item.agent === selected)
  const previous = event ? events[events.indexOf(event) - 1] : undefined
  const gap = event && previous ? Date.parse(event.timestamp) - Date.parse(previous.timestamp) : null
  return (
    <section className="stage">
      <div className="flow-wrap">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          onNodeClick={(_, node) => setSelected(node.id)}
          proOptions={{ hideAttribution: false }}
        >
          <Background />
        </ReactFlow>
      </div>
      <aside className="panel">
        {agent && (
          <>
            <p className="kicker">{agent.placement}</p>
            <h2>{agent.title}</h2>
            <p>{agent.purpose}</p>
            <p><strong>Authority. </strong>{agent.authority}</p>
            <p><strong>Hosting. </strong>{agent.hosting}</p>
            <p className="quiet">
              {gap == null ? 'No elapsed time yet. Latency is taken from audit timestamps, not estimated.' : `Time since previous audit event: ${Math.max(0, gap)} ms.`}
            </p>
            {event && (
              <>
                <h3>Latest hand-off</h3>
                <p>{event.message}</p>
                <p className="mono">trace {event.traceId}</p>
                <p className="quiet">Input evidence stays on the event. Output status {event.evidenceStatus}.</p>
              </>
            )}
          </>
        )}
      </aside>
    </section>
  )
}

export function EvidenceView({ pack, lens, run }: { pack: PackDetail; lens: LensId; run: PublicRun | null }) {
  const verify = run?.events.find((event) => event.agent === 'verify')
  const plan = run?.events.find((event) => event.agent === 'plan')
  const commercial = pack.intent.commercial
  return (
    <section className="stage">
      <div className="evidence-spine">
        <article>
          <p className="kicker">Signals · simulated</p>
          <h2>Observed, not proven</h2>
          <ul>
            {pack.scenario.signalSnapshot.map((signal) => (
              <li key={signal.name}>
                <strong>{signal.name}</strong> {signal.value}
                <small>{signal.source} · {signal.quality}</small>
              </li>
            ))}
          </ul>
        </article>
        <article>
          <p className="kicker">Hypothesis · unvalidated</p>
          <h2>{pack.intent.valueIntent.objective}</h2>
          <p>{commercial.customer.hypothesis}</p>
          <p className="quiet">Confounders: {pack.intent.evidence.confounders.join('; ')}.</p>
        </article>
        <article>
          <p className="kicker">Plan · proposed</p>
          <ul>
            {(Array.isArray(plan?.details.options) ? (plan?.details.options as string[]) : []).map((option) => (
              <li key={option}>{option}</li>
            ))}
            {!plan && <li>No plan has been recorded for this run.</li>}
          </ul>
        </article>
        <article>
          <p className="kicker">Action · simulated</p>
          <p>{run?.run.ticket ? run.run.ticket.summary : 'No simulated ticket yet.'}</p>
        </article>
        <article className="measure">
          <p className="kicker">Verification</p>
          <h2>NOT MEASURED</h2>
          <p>{verify ? String(verify.details.assertion || verify.message) : pack.intent.evidence.verification}</p>
          <p className="quiet">Missing before a claim: {(pack.design.validation?.missingData || []).join(', ') || 'customer baseline and a signed measurement plan'}.</p>
        </article>
      </div>
      <aside className="panel">
        <p className="kicker">{pack.design.lenses[lens]?.label}</p>
        {lens === 'customer' && (
          <>
            <h2>{pack.intent.valueIntent.metric}</h2>
            <p>Baseline: {pack.intent.valueIntent.baselineText}</p>
            <p>Target: {pack.intent.valueIntent.targetText}</p>
            <StatusPill tone="warn">{commercial.customer.status}</StatusPill>
          </>
        )}
        {lens === 'partner' && (
          <>
            <h2>Partner role</h2>
            <p>{commercial.partner.role}</p>
            <ul>
              {pack.design.nodes.filter((node) => node.type === 'offer').map((node) => (
                <li key={node.id}>{node.title}</li>
              ))}
            </ul>
          </>
        )}
        {lens === 'cisco' && (
          <>
            <h2>Capability position</h2>
            <p>{commercial.cisco.capabilityPositioning}</p>
            <ul>
              {pack.design.nodes.filter((node) => node.type === 'capability').map((node) => (
                <li key={node.id}>{node.title}</li>
              ))}
            </ul>
            <p className="quiet">No Cisco booking figure is stated.</p>
          </>
        )}
        <p className="quiet">{commercial.separation}</p>
        <h3>Audit</h3>
        <ul className="audit">
          {(run?.events || []).map((event) => (
            <li key={event.eventId}>
              <span>{event.timestamp.slice(11, 19)}</span> {event.agent} · {event.evidenceStatus}
            </li>
          ))}
          {!run && <li>Run the live workflow to append an audit record.</li>}
        </ul>
      </aside>
    </section>
  )
}

export function StudioView({ pack }: { pack: PackDetail }) {
  const [text, setText] = useState('')
  const [result, setResult] = useState<string>('')
  async function check() {
    try {
      const document = JSON.parse(text) as unknown
      const response = await api.validate(document)
      setResult(response.ok ? `Valid ${response.kind || 'document'}.` : response.errors.join('\n'))
    } catch (error) {
      setResult(error instanceof Error ? error.message : 'Could not validate')
    }
  }
  function download() {
    const blob = new Blob([JSON.stringify(pack.intent, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${pack.design.packId}-value-intent.json`
    link.click()
    URL.revokeObjectURL(url)
  }
  return (
    <section className="stage">
      <div className="panel studio-main">
        <p className="kicker">Lineage · {pack.intent.schemaVersion}</p>
        <h2>{pack.design.name}</h2>
        <p>{pack.design.provenance?.disclaimer || 'Synthetic pack. Not a customer-verified baseline.'}</p>
        <ul className="quiet-list">
          <li>{pack.lineage.design}</li>
          <li>{pack.lineage.scenario}</li>
          <li>{pack.lineage.legacyManifest}</li>
          {pack.lineage.modules.map((module) => (
            <li key={module}>{module}</li>
          ))}
        </ul>
        <h3>Import check</h3>
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          rows={8}
          placeholder="Paste a design pack or a cvs.intent/v1 document"
          aria-label="Pack JSON"
        />
        <div className="row-actions">
          <button type="button" onClick={check}>Validate</button>
          <button type="button" className="primary" onClick={download}>Export intent</button>
        </div>
        {result && <pre>{result}</pre>}
      </div>
      <aside className="panel">
        <p className="kicker">{pack.validation.ok ? 'Schema and graph links accepted' : 'Validation failed'}</p>
        <h2>Intent preview</h2>
        <p className="mono">{pack.intent.intentHash}</p>
        <p>Outcome state {pack.intent.runtime.outcomeState}. Legacy manifest outcome {pack.legacy.outcomeState}.</p>
        <h3>Denied</h3>
        <ul>
          {pack.intent.governance.deniedActions.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
        <p className="quiet">External systems enabled: {String(pack.intent.governance.externalSystemsEnabled)}. Physical control in the scenario: {String(pack.scenario.controls.allowPhysicalControl)}.</p>
      </aside>
    </section>
  )
}

const ACCOUNT_STAGES = [
  ['discovery', 'Discovery'],
  ['early_pursuit', 'Early pursuit'],
  ['active_opportunity', 'Active opportunity'],
  ['renewal', 'Renewal'],
  ['expansion', 'Expansion'],
  ['transformation', 'Transformation'],
]

const EVIDENCE_TONE: Record<string, string> = {
  validated: 'ok',
  public_signal: 'info',
  user_provided: 'info',
  industry_pattern: 'warn',
  inferred: 'warn',
  assumption: 'warn',
  unknown: 'bad',
}

const LAYER_ICON: Record<DiscoveryLayerId, string> = {
  industry_context: 'compass',
  industry_value_stream: 'waypoints',
  customer_value_stream: 'building',
  function: 'users',
  persona: 'handshake',
}

function label(value: string) {
  return value.replace(/_/g, ' ')
}

export function DiscoveryView({
  pack,
  lens,
  run,
  document: doc,
  stages,
  busy,
  error,
  form,
  setForm,
  onRun,
  onStep,
  onReset,
}: {
  pack: PackDetail
  lens: LensId
  run: PublicRun | null
  document: DiscoveryDocument | null
  stages: DiscoveryStageAgent[]
  busy: boolean
  error: string
  form: DiscoveryInput
  setForm: (value: DiscoveryInput) => void
  onRun: () => void
  onStep: () => void
  onReset: () => void
}) {
  const [section, setSection] = useState<'graph' | 'evidence' | 'validate' | 'pack'>('graph')
  const [selected, setSelected] = useState('')
  const [layerFilter, setLayerFilter] = useState<DiscoveryLayerId | 'all'>('all')
  const [evidenceFilter, setEvidenceFilter] = useState('all')
  const [signal, setSignal] = useState('')
  const events = run?.events || []
  const done = new Set(events.filter((event) => event.stage === 'complete').map((event) => event.agent))
  const current = events[events.length - 1]?.agent
  const graph = doc?.knowledge_graph
  const nodeIndex = useMemo(
    () => new Map((graph?.nodes || []).map((node) => [node.id, node])),
    [graph],
  )

  useEffect(() => {
    if (graph && !nodeIndex.has(selected)) {
      const first = graph.nodes.find((node) => node.layer === 'customer_value_stream') || graph.nodes[0]
      setSelected(first?.id || '')
    }
  }, [graph, nodeIndex, selected])

  const visible = useMemo(() => {
    if (!graph) return []
    if (layerFilter === 'all') return graph.nodes
    const keep = new Set(graph.nodes.filter((node) => node.layer === layerFilter).map((node) => node.id))
    for (const edge of graph.edges) {
      if (keep.has(edge.from)) keep.add(edge.to)
      else if (keep.has(edge.to)) keep.add(edge.from)
    }
    return graph.nodes.filter((node) => keep.has(node.id))
  }, [graph, layerFilter])

  const flowNodes = useMemo<Node<ConceptData>[]>(() => {
    if (!graph) return []
    const perLayer = new Map<string, number>()
    return visible.map((node) => {
      const order = graph.layers.find((layer) => layer.id === node.layer)?.order ?? 1
      const column = perLayer.get(node.layer) ?? 0
      perLayer.set(node.layer, column + 1)
      return {
        id: node.id,
        type: 'concept',
        position: { x: column * 250, y: (order - 1) * 190 },
        data: {
          title: node.title,
          layer: node.layer,
          evidence: node.evidence_type,
          confidence: node.confidence,
          selected: node.id === selected,
        },
      }
    })
  }, [graph, visible, selected])

  const flowEdges = useMemo(() => {
    const ids = new Set(visible.map((node) => node.id))
    return (graph?.edges || [])
      .filter((edge) => ids.has(edge.from) && ids.has(edge.to))
      .map((edge) => ({
        id: `${edge.from}-${edge.to}`,
        source: edge.from,
        target: edge.to,
        type: 'smoothstep',
        label: edge.relation,
      }))
  }, [graph, visible])

  const node = nodeIndex.get(selected)

  function download() {
    if (!doc) return
    const blob = new Blob([JSON.stringify(doc, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = window.document.createElement('a')
    link.href = url
    link.download = `${doc.meta.pack_id}-discovery-pack.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <section className="section">
      <ol className="steps" aria-label="Discovery stages" aria-live="polite">
        {stages.map((stage, index) => (
          <li key={stage.id}>
            <span className={current === stage.id ? 'step active' : done.has(stage.id) ? 'step done' : 'step'} title={stage.purpose}>
              <b>{index + 1}</b>
              {stage.title}
            </span>
          </li>
        ))}
      </ol>

      {!doc && run && (
        <div className="card story-copy">
          <span className="overline">Researching</span>
          <h2>Reading the local corpus for {form.customerName || 'this customer'}</h2>
          <p className="lead">
            {events[events.length - 1]?.message || 'Starting the first stage.'}
          </p>
          <p className="trace-line">trace {run.run.traceId}</p>
          {error && <p className="error">{error}</p>}
        </div>
      )}

      {!doc && !run && (
        <div className="stage">
          <form
            className="card story-copy"
            onSubmit={(event) => {
              event.preventDefault()
              onRun()
            }}
          >
            <span className="overline">Step 01 · Runtime input</span>
            <h2>Research a customer and build the first-view knowledge graph</h2>
            <p className="lead">
              The agent reads a local, labelled research corpus: industry body and analyst material, the customer's own
              end-of-year reporting, and the design pack already in this repository. It makes no external call. Where
              evidence is missing it writes a validation question instead of an answer.
            </p>
            <div className="rule" />
            <div className="field-grid">
              <label>
                Customer name
                <input
                  value={form.customerName}
                  onChange={(event) => setForm({ ...form, customerName: event.target.value })}
                  placeholder="Northwind Group"
                  maxLength={120}
                />
              </label>
              <label>
                Geography
                <input
                  value={form.geography}
                  onChange={(event) => setForm({ ...form, geography: event.target.value })}
                  placeholder="UK and Ireland"
                  maxLength={120}
                />
              </label>
              <label>
                Business model
                <input
                  value={form.businessModel}
                  onChange={(event) => setForm({ ...form, businessModel: event.target.value })}
                  placeholder="Multi-site enterprise"
                  maxLength={160}
                />
              </label>
              <label>
                Account stage
                <select value={form.accountStage} onChange={(event) => setForm({ ...form, accountStage: event.target.value })}>
                  {ACCOUNT_STAGES.map(([value, text]) => (
                    <option key={value} value={value}>
                      {text}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label className="field-wide">
              Add something you were told (recorded as a user-provided signal, never promoted to evidence)
              <input
                value={signal}
                onChange={(event) => setSignal(event.target.value)}
                placeholder="The estate lead said the board asked for a cost review"
                maxLength={400}
              />
            </label>
            <div className="row-actions">
              <button
                type="button"
                onClick={() => {
                  if (!signal.trim()) return
                  setForm({
                    ...form,
                    signals: [...form.signals, { signal: signal.trim(), sensitivity: 'confidential', confidence: 'medium' }],
                  })
                  setSignal('')
                }}
              >
                Add signal
              </button>
              <button type="submit" className="primary" disabled={busy}>
                Run discovery
              </button>
            </div>
            {form.signals.length > 0 && (
              <ul className="quiet-list">
                {form.signals.map((item) => (
                  <li key={item.signal}>
                    {item.signal} <span className="pill tone-info">user provided · {item.sensitivity}</span>
                  </li>
                ))}
              </ul>
            )}
            {error && <p className="error">{error}</p>}
          </form>
          <aside className="panel">
            <p className="kicker">How the agent works</p>
            <h2>Eight stages, one audit trail</h2>
            <ol className="point-list">
              {stages.map((stage, index) => (
                <li className="point-item" key={stage.id}>
                  <span className="num">{index + 1}</span>
                  <span>
                    <strong>{stage.title}</strong>
                    <br />
                    <span className="quiet">{stage.purpose}</span>
                  </span>
                </li>
              ))}
            </ol>
            <div className="callout">
              <strong>No external research calls.</strong>
              <p className="quiet">
                Sources are local placeholders so the pipeline can be tested. Replace them with real references before
                anything leaves the studio.
              </p>
            </div>
          </aside>
        </div>
      )}

      {doc && (
        <>
          <div className="subnav">
            <div className="subnav-tabs" role="tablist" aria-label="Discovery sections">
              {([
                ['graph', 'Knowledge graph'],
                ['evidence', 'Evidence register'],
                ['validate', 'Validation backlog'],
                ['pack', 'Pack JSON'],
              ] as const).map(([id, text]) => (
                <button
                  key={id}
                  type="button"
                  role="tab"
                  aria-selected={section === id}
                  className={section === id ? 'active' : ''}
                  onClick={() => setSection(id)}
                >
                  {text}
                </button>
              ))}
            </div>
            <div className="row-actions">
              <span className="pill">{doc.customer.name} · {label(doc.customer.account_stage)}</span>
              <button type="button" onClick={onStep} disabled={busy || run?.run.state === 'DISCOVERY_COMPLETE'}>
                Step
              </button>
              <button type="button" onClick={onReset}>New research</button>
            </div>
          </div>

          {section === 'graph' && (
            <>
              <ol className="outline" aria-label="Pack concept outline">
                <li>
                  <button
                    type="button"
                    className={layerFilter === 'all' ? 'outline-card on' : 'outline-card'}
                    onClick={() => setLayerFilter('all')}
                  >
                    <span className="outline-order">All</span>
                    <strong>Whole graph</strong>
                    <em>{graph?.nodes.length} concepts · {graph?.edges.length} links</em>
                  </button>
                </li>
                {graph?.layers.map((layer) => (
                  <li key={layer.id}>
                    <button
                      type="button"
                      className={layerFilter === layer.id ? 'outline-card on' : 'outline-card'}
                      onClick={() => setLayerFilter(layer.id)}
                      title={layer.description}
                    >
                      <span className="outline-order">{layer.order}</span>
                      <strong>
                        <Icon name={LAYER_ICON[layer.id]} size={14} /> {layer.label}
                      </strong>
                      <em>{graph.counts[layer.id]} concepts</em>
                    </button>
                  </li>
                ))}
              </ol>
              <div className="stage">
                <div className="flow-wrap tall">
                  <ReactFlow
                    nodes={flowNodes}
                    edges={flowEdges}
                    nodeTypes={nodeTypes}
                    fitView
                    minZoom={0.2}
                    onNodeClick={(_, clicked) => setSelected(clicked.id)}
                    proOptions={{ hideAttribution: false }}
                  >
                    <Background />
                  </ReactFlow>
                </div>
                <aside className="panel">
                  <LensNote doc={doc} lens={lens} pack={pack} />
                  <div className="rule" />
                  {node ? (
                    <>
                      <p className="kicker">{label(node.layer)} · {label(node.evidence_type)}</p>
                      <h2>{node.title}</h2>
                      <p>{node.summary}</p>
                      <div className="badge-row">
                        <StatusPill tone={EVIDENCE_TONE[node.evidence_type] || 'neutral'}>
                          {label(node.evidence_type)}
                        </StatusPill>
                        <StatusPill tone="neutral">{node.confidence} confidence</StatusPill>
                        <StatusPill tone={node.validation_status === 'validated' ? 'ok' : 'warn'}>
                          {label(node.validation_status)}
                        </StatusPill>
                      </div>
                      <NodeDetail detail={node.detail} />
                      {node.validation_questions.length > 0 && (
                        <>
                          <h3>Ask before using this</h3>
                          <ul>
                            {node.validation_questions.map((question) => (
                              <li key={question}>{question}</li>
                            ))}
                          </ul>
                        </>
                      )}
                      <h3>Sources</h3>
                      <ul className="quiet-list">
                        {node.source_refs.map((ref) => (
                          <li key={ref}>
                            {doc.source_notes.find((item) => item.id === ref)?.name || ref}
                          </li>
                        ))}
                        {node.source_refs.length === 0 && <li>No source. This concept is an assumption.</li>}
                      </ul>
                      {node.design_pack_refs.length > 0 && (
                        <p className="quiet">Design pack nodes: {node.design_pack_refs.join(', ')}</p>
                      )}
                    </>
                  ) : (
                    <p>Select a concept in the graph.</p>
                  )}
                </aside>
              </div>
            </>
          )}

          {section === 'evidence' && (
            <div className="stage">
              <div className="panel">
                <p className="kicker">Evidence register · {doc.evidence_register.length} claims</p>
                <h2>Every claim, and what it rests on</h2>
                <div className="track-bar">
                  {['all', ...Object.keys(doc.company_insights.evidence_coverage.counts)].map((key) => (
                    <button
                      key={key}
                      type="button"
                      className={evidenceFilter === key ? 'chip on' : 'chip'}
                      onClick={() => setEvidenceFilter(key)}
                    >
                      {label(key)}
                      {key !== 'all' && ` · ${doc.company_insights.evidence_coverage.counts[key]}`}
                    </button>
                  ))}
                </div>
                <table className="grid-table">
                  <thead>
                    <tr>
                      <th>Claim</th>
                      <th>Class</th>
                      <th>Confidence</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {doc.evidence_register
                      .filter((row) => evidenceFilter === 'all' || row.evidence_type === evidenceFilter)
                      .map((row) => (
                        <tr key={row.id}>
                          <td>
                            {row.claim}
                            {row.validation_question && <span className="quiet"> Ask: {row.validation_question}</span>}
                          </td>
                          <td>
                            <StatusPill tone={EVIDENCE_TONE[row.evidence_type] || 'neutral'}>
                              {label(row.evidence_type)}
                            </StatusPill>
                          </td>
                          <td>{row.confidence}</td>
                          <td className="quiet">{label(row.validation_status)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
              <aside className="panel">
                <p className="kicker">Sources cited</p>
                <h2>Provenance</h2>
                <ul className="quiet-list">
                  {doc.source_notes.map((item) => (
                    <li key={item.id}>
                      <strong>{item.name}</strong>
                      <br />
                      <span className="quiet">
                        {label(item.source_class)} · {item.reference_type} · {item.confidence} confidence
                      </span>
                      <br />
                      <span className="mono">{item.reference}</span>
                    </li>
                  ))}
                </ul>
                <div className="callout">
                  <strong>Content status: synthetic.</strong>
                  <p className="quiet">
                    Placeholder sources exist so the pipeline can be tested. {doc.company_insights.evidence_coverage.total}{' '}
                    statements were classified; {Math.round(doc.company_insights.evidence_coverage.validatedShare * 100)}%
                    rest on material already agreed in this repository.
                  </p>
                </div>
              </aside>
            </div>
          )}

          {section === 'validate' && (
            <div className="stage">
              <div className="evidence-spine">
                <article>
                  <p className="kicker">Validation gates · {doc.validation_gates.length}</p>
                  <h2>Answer these before any claim</h2>
                  <ul className="quiet-list">
                    {doc.validation_gates.map((gate) => (
                      <li key={gate.id}>
                        {gate.question}
                        <br />
                        <span className="quiet">
                          Owner to confirm: {gate.owner_to_confirm} · blocks {gate.blocks.join(', ') || 'nothing yet'}
                        </span>
                      </li>
                    ))}
                  </ul>
                </article>
                <article>
                  <p className="kicker">Sequenced roadmap</p>
                  <ol className="point-list">
                    {doc.roadmap.map((item) => (
                      <li className="point-item" key={item.step}>
                        <span className="num">{item.step}</span>
                        <span>
                          {item.action}
                          <br />
                          <span className="quiet">Evidence needed: {item.evidence_needed}</span>
                        </span>
                      </li>
                    ))}
                  </ol>
                </article>
                <article className="measure">
                  <p className="kicker">Outcome state</p>
                  <h2>NOT MEASURED</h2>
                  <p>
                    {doc.outcomes.length} board objectives were carried across from the design pack with no baseline and
                    no target. Maturity stage: {doc.current_state.maturity_stage}.
                  </p>
                  <p className="quiet">Missing before a claim: {doc.current_state.missing_data.join(', ') || 'to confirm'}.</p>
                </article>
              </div>
              <aside className="panel">
                <p className="kicker">AI use cases · responsible AI</p>
                <h2>Each one carries a risk and a next step</h2>
                {doc.ai_value_twin.map((item) => (
                  <div className="callout" key={item.id}>
                    <strong>{item.name}</strong>
                    <div className="badge-row">
                      <StatusPill tone={item.rai_risk === 'high' ? 'bad' : item.rai_risk === 'medium' ? 'warn' : 'ok'}>
                        RAI risk {item.rai_risk}
                      </StatusPill>
                      <StatusPill tone="neutral">impact {item.impact}</StatusPill>
                      <StatusPill tone="neutral">complexity {item.complexity}</StatusPill>
                    </div>
                    <p className="quiet">{item.rai_notes}</p>
                    <p className="quiet">Human step: {item.human_in_the_loop}</p>
                    <p className="quiet">Next: {item.next_validation_action}</p>
                  </div>
                ))}
              </aside>
            </div>
          )}

          {section === 'pack' && (
            <div className="stage">
              <div className="panel studio-main">
                <p className="kicker">{doc.schemaVersion} · template {doc.meta.template_version}</p>
                <h2>Generated discovery pack</h2>
                <p className="mono">{doc.discoveryHash}</p>
                <p className="quiet">{doc.meta.disclaimer}</p>
                <div className="row-actions">
                  <button type="button" className="primary" onClick={download}>
                    Export discovery pack
                  </button>
                </div>
                <pre>{JSON.stringify(doc, null, 2).slice(0, 12000)}</pre>
                <p className="quiet">Preview truncated. Export the file for the full document.</p>
              </div>
              <aside className="panel">
                <p className="kicker">Pack concepts in order</p>
                <h2>What was built</h2>
                <ol className="point-list">
                  {doc.knowledge_graph.layers.map((layer) => (
                    <li className="point-item" key={layer.id}>
                      <span className="num">{layer.order}</span>
                      <span>
                        <strong>{layer.label}</strong> · {doc.knowledge_graph.counts[layer.id]}
                        <br />
                        <span className="quiet">{layer.description}</span>
                      </span>
                    </li>
                  ))}
                </ol>
                <h3>Also in the pack</h3>
                <ul className="quiet-list">
                  <li>{doc.value_twin_nodes.length} value twin nodes on the template contract</li>
                  <li>{doc.evidence_register.length} classified claims</li>
                  <li>{doc.portfolio_mapping.length} capability needs before any portfolio mapping</li>
                  <li>{doc.partner_landscape.length} partner roles, all inferred</li>
                  <li>{doc.role_insights.length} role views</li>
                  <li>{doc.validation_gates.length} validation gates</li>
                </ul>
                <p className="quiet">Paste the exported file into Pack Studio to re-validate it against the contract.</p>
              </aside>
            </div>
          )}
        </>
      )}
      {error && doc && <p className="error">{error}</p>}
    </section>
  )
}

function NodeDetail({ detail }: { detail: Record<string, unknown> }) {
  const rows = Object.entries(detail).filter(([, value]) => Array.isArray(value) && value.length > 0)
  if (rows.length === 0) return null
  return (
    <>
      {rows.map(([key, value]) => (
        <div key={key}>
          <h3>{label(key)}</h3>
          <ul>
            {(value as unknown[]).map((item) => (
              <li key={String(item)}>{String(item)}</li>
            ))}
          </ul>
        </div>
      ))}
    </>
  )
}

function LensNote({ doc, lens, pack }: { doc: DiscoveryDocument; lens: LensId; pack: PackDetail }) {
  if (lens === 'partner') {
    return (
      <>
        <p className="kicker">Partner lens</p>
        <ul className="quiet-list">
          {doc.partner_landscape.map((item) => (
            <li key={item.id}>
              <strong>{item.name}</strong> · {label(item.evidence_type)}
              <br />
              <span className="quiet">{item.validation_question}</span>
            </li>
          ))}
        </ul>
        <p className="quiet">{doc.partner_landscape[0]?.p360_guidance}</p>
      </>
    )
  }
  if (lens === 'cisco') {
    return (
      <>
        <p className="kicker">Capability lens</p>
        <ul className="quiet-list">
          {doc.portfolio_mapping.slice(0, 6).map((item) => (
            <li key={`${item.capability_need}-${item.gap}`}>
              {item.capability_need}
              <br />
              <span className="quiet">
                {item.portfolio_domain ? `Possible domain: ${item.portfolio_domain}` : 'No portfolio match claimed'} ·{' '}
                {item.priority} priority
              </span>
            </li>
          ))}
        </ul>
        <p className="quiet">Capability needs come before products. No booking figure is stated.</p>
      </>
    )
  }
  return (
    <>
      <p className="kicker">Customer lens</p>
      <ul className="quiet-list">
        {doc.outcomes.map((item) => (
          <li key={item.id}>
            <strong>{item.outcome}</strong>
            <br />
            <span className="quiet">
              {item.kpi} · {item.status}
            </span>
          </li>
        ))}
      </ul>
      <p className="quiet">
        Objectives are carried from {pack.design.name}. No baseline or target is claimed by the research agent.
      </p>
    </>
  )
}
