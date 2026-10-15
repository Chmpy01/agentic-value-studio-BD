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
import type { LensId, PackDetail, PublicRun, TraceEvent } from './types'

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

const nodeTypes = { agent: AgentNode }

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
  return (
    <section className="stage story-stage">
      <article className="story-card">
        <div>
          <p className="eyebrow">{scene.eyebrow}</p>
          <h1>{scene.headline}</h1>
          <p className="lede">{scene.explanation}</p>
          <ul className="points">
            {scene.keyPoints.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </div>
        <footer className="story-foot">
          <div className="dots" aria-label="Story progress">
            {scenes.map((item, dot) => (
              <button
                key={item.id}
                type="button"
                className={dot === index ? 'on' : ''}
                aria-label={item.title}
                aria-current={dot === index}
                onClick={() => setIndex(dot)}
              />
            ))}
          </div>
          <div className="row-actions">
            <button type="button" onClick={() => setIndex(Math.max(0, index - 1))} disabled={index === 0}>
              Back
            </button>
            <button type="button" className="primary" onClick={() => setIndex(Math.min(scenes.length - 1, index + 1))} disabled={index === scenes.length - 1}>
              Next
            </button>
            <button type="button" onClick={() => setNotes(true)}>
              Presenter notes
            </button>
          </div>
        </footer>
      </article>
      <aside className="panel">
        <p className="kicker">{lensCopy?.label}</p>
        <h2>{scene.title}</h2>
        <p className="quiet">{lensCopy?.description}</p>
        <div className="focus-list">
          {scene.focusNodeIds.map((id) => {
            const node = nodeById(pack.design.nodes, id)
            if (!node) return null
            return (
              <div key={id} className="focus-item">
                <Icon name={node.icon} />
                <div>
                  <small>{node.type}</small>
                  <strong>{node.title}</strong>
                </div>
              </div>
            )
          })}
        </div>
      </aside>
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
    <section className="stage">
      <div className="visual-stack">
        <Building src={pack.imageUrl} hotspots={pack.design.scene.hotspots} nodes={pack.design.nodes} active={active} />
        <ol className="stepper" aria-live="polite">
          {FLOW.map((id) => {
            const agent = pack.network.find((item) => item.id === id)
            const current = shown?.agent === id
            return (
              <li key={id} className={current ? 'current' : done.has(id) ? 'done' : ''}>
                <span>{agent?.title || id}</span>
              </li>
            )
          })}
        </ol>
        <p className="trace-line">
          {replay ? 'Recorded trace replay' : 'Live audit stream'} · trace {run?.run.traceId || 'not started'}
        </p>
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
