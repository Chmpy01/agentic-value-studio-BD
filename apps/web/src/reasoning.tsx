import { useEffect, useMemo, useState } from 'react'
import { Background, Handle, Position, ReactFlow, type Edge, type Node, type NodeProps } from '@xyflow/react'
import { ArrowRight, Play, Star } from 'lucide-react'
import { api } from './api'
import { LinkRow, Segmented, StatusPill, ViewHeader } from './components'
import type { Graph } from './graph'
import { Icon } from './icons'
import type { Assessment, LensId, ModeId, PackDetail, ReasoningEvent, ReasoningRun, ReasoningScenario, Recommendation, Topology } from './types'

const TERMINAL = new Set(['COMPLETE', 'BLOCKED', 'ERROR'])

const LAYOUT: Record<string, { x: number; y: number; icon: string; label: string; role: string }> = {
  __start__: { x: 0, y: 150, icon: 'play', label: 'Start', role: 'trace opened' },
  ingest: { x: 120, y: 150, icon: 'database', label: 'Ingest', role: 'validate readings' },
  detect: { x: 330, y: 150, icon: 'activity', label: 'Detect', role: 'threshold breaches' },
  evaluate: { x: 560, y: 0, icon: 'spark', label: 'Evaluate', role: 'parallel · one per hypothesis' },
  monitor: { x: 560, y: 175, icon: 'radio', label: 'Monitor', role: 'no breach' },
  request_evidence: { x: 560, y: 300, icon: 'shield', label: 'Request evidence', role: 'rejected data only' },
  synthesise: { x: 790, y: 0, icon: 'merge', label: 'Synthesise', role: 'rank · find combined outcome' },
  policy_gate: { x: 1010, y: 150, icon: 'shield', label: 'Policy gate', role: 'deterministic allowlist' },
  narrate: { x: 1230, y: 150, icon: 'workflow', label: 'Narrate', role: 'template, not a model' },
  __end__: { x: 1440, y: 150, icon: 'badge', label: 'End', role: 'NOT MEASURED' },
}

type StepData = { id: string; state: string; parallel: Assessment[] }

function StepNode({ data }: NodeProps<Node<StepData>>) {
  const meta = LAYOUT[data.id] || { icon: 'layers', label: data.id, role: '' }
  const terminal = data.id === '__start__' || data.id === '__end__'
  return (
    <div className={`lg-node ${data.state} ${terminal ? 'terminal' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <span className="lg-ico"><Icon name={meta.icon} size={terminal ? 14 : 17} /></span>
      {!terminal && (
        <span className="lg-text">
          <strong>{meta.label}</strong>
          <small>{meta.role}</small>
        </span>
      )}
      {data.parallel.length > 0 && (
        <span className="lg-fan">
          {data.parallel.map((item) => (
            <span key={item.hypothesisId} className={`fan ${item.band}`}>
              {item.title} <b>{item.score.toFixed(2)}</b>
            </span>
          ))}
        </span>
      )}
      <Handle type="source" position={Position.Right} />
    </div>
  )
}

const stepTypes = { step: StepNode }

function readingState(readingId: string, events: ReasoningEvent[]) {
  if (events.some((e) => e.type === 'reading.rejected' && e.details.readingId === readingId)) return 'rejected'
  const evaluated = events.find((e) => e.type === 'signals.evaluated')
  if (!evaluated) return events.some((e) => e.type === 'signals.ingested') ? 'accepted' : 'pending'
  const triggered = (evaluated.details.triggered as { readingId: string }[]) || []
  return triggered.some((item) => item.readingId === readingId) ? 'breach' : 'normal'
}

export function ReasoningView({
  pack,
  graph,
  lens,
  onPick,
  onNavigate,
  onCompound,
}: {
  pack: PackDetail
  graph: Graph
  lens: LensId
  onPick: (id: string) => void
  onNavigate: (mode: ModeId) => void
  onCompound: (synergyId: string) => void
}) {
  const [topology, setTopology] = useState<Topology | null>(null)
  const [scenarios, setScenarios] = useState<ReasoningScenario[]>([])
  const [scenarioId, setScenarioId] = useState('')
  const [run, setRun] = useState<ReasoningRun | null>(null)
  const [tab, setTab] = useState<'findings' | 'trace'>('findings')
  const [error, setError] = useState('')
  const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  useEffect(() => {
    api.reasoningTopology().then(setTopology).catch((reason: Error) => setError(reason.message))
    api.reasoningScenarios(pack.design.packId)
      .then((list) => {
        setScenarios(list)
        setScenarioId(list.find((item) => item.id !== 'steady')?.id || list[0]?.id || '')
      })
      .catch((reason: Error) => setError(reason.message))
  }, [pack.design.packId])

  const runId = run?.id
  const running = Boolean(run && !TERMINAL.has(run.state))
  useEffect(() => {
    if (!runId || !running) return
    const timer = window.setInterval(() => {
      api.reasoning(runId).then(setRun).catch(() => undefined)
    }, 300)
    return () => window.clearInterval(timer)
  }, [runId, running])

  async function start() {
    setError('')
    setTab('findings')
    try {
      setRun(await api.startReasoning({ pack: pack.design.packId, scenario: scenarioId }))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not start reasoning')
    }
  }

  const events = useMemo(() => run?.events ?? [], [run])
  const scenario = scenarios.find((item) => item.id === scenarioId)
  const assessments = events.filter((e) => e.type === 'hypothesis.assessed').map((e) => e.details as unknown as Assessment)
  const visited = useMemo(() => new Set(events.map((e) => e.node)), [events])
  const last = events[events.length - 1]?.node
  const done = Boolean(run && TERMINAL.has(run.state))

  const nodes = useMemo<Node<StepData>[]>(() => {
    if (!topology) return []
    return topology.nodes.map(({ id }) => {
      let state = 'idle'
      if (run) {
        const seen = id === '__start__' ? events.length > 0 : id === '__end__' ? done && run.state === 'COMPLETE' : visited.has(id)
        if (seen) state = !done && id === last ? 'current' : 'done'
        else if (done) state = 'skipped'
      }
      const position = LAYOUT[id] || { x: 0, y: 0 }
      return { id, type: 'step', position: { x: position.x, y: position.y }, data: { id, state, parallel: id === 'evaluate' ? assessments : [] }, draggable: false }
    })
  }, [topology, run, events, visited, last, done, assessments])

  const edges = useMemo<Edge[]>(() => {
    if (!topology) return []
    const seen = (id: string) => (id === '__start__' ? events.length > 0 : id === '__end__' ? done && run?.state === 'COMPLETE' : visited.has(id))
    return topology.edges.map((edge) => {
      const walked = Boolean(run) && seen(edge.source) && seen(edge.target)
      const live = walked && !done && edge.target === last
      return {
        id: `${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        type: 'smoothstep',
        animated: (live || (walked && !done)) && !reduced,
        className: `lg-edge ${edge.conditional ? 'conditional' : ''} ${walked ? 'walked' : run && done ? 'unused' : ''}`,
        label: edge.conditional ? 'route' : undefined,
        labelBgPadding: [5, 2] as [number, number],
        labelBgBorderRadius: 5,
      }
    })
  }, [topology, run, events, visited, done, last, reduced])

  const recommendation = run?.result?.recommendation
  const compound = run?.result?.compound
  const ranking = run?.result?.ranking ?? assessments
  const narrative = events.find((e) => e.type === 'narrative.generated')
  const personas = [...new Map(ranking.flatMap((item) => item.personas).map((p) => [p.id, p])).values()]
  const start0 = events[0] ? Date.parse(events[0].timestamp) : 0

  return (
    <section className="section">
      <ViewHeader
        overline="LangGraph · signal-driven reasoning"
        title="Signals choose the route. Policy decides what may happen next."
        text="A real LangGraph StateGraph runs on the API. Breached signals fan out into parallel hypothesis checks; every path ends at a deterministic policy gate. The view replays the recorded trace."
        pill="Synthetic signals · no LLM · no actuation"
        tone="warn"
      />
      <div className="reason-controls">
        <div className="case-row tight">
          {scenarios.map((item) => (
            <button key={item.id} type="button" className={`econ-case ${item.id === scenarioId ? 'active' : ''}`} onClick={() => { setScenarioId(item.id); setRun(null) }} disabled={running}>
              <small>Signal situation</small>
              <b>{item.label}</b>
            </button>
          ))}
        </div>
        <button type="button" className="ui-btn primary run-btn" onClick={() => void start()} disabled={!scenarioId || running}>
          <Play size={15} /> {running ? 'Reasoning…' : run ? 'Run again' : 'Run reasoning graph'}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      <div className="graph-layout">
        <div className="lg-canvas">
          <div className="hero-top">
            <span className="canvas-eyebrow static">{topology?.engine || 'LangGraph'} · {run ? run.state : 'ready'}</span>
            <span className="hero-note mono-light">{run ? `trace ${run.traceId.slice(0, 8)}` : scenario?.description}</span>
          </div>
          <div className="lg-flow">
            <ReactFlow nodes={nodes} edges={edges} nodeTypes={stepTypes} fitView fitViewOptions={{ padding: 0.12 }} nodesDraggable={false} zoomOnScroll={false} panOnDrag={false} proOptions={{ hideAttribution: true }}>
              <Background gap={26} color="#21436b" />
            </ReactFlow>
          </div>
          <div className="readings">
            {scenario?.readings.map((reading) => {
              const state = readingState(reading.id, events)
              const signal = graph.byId.get(reading.signalId)
              return (
                <button key={reading.id} type="button" className={`reading ${state}`} onClick={() => onPick(reading.signalId)} title={signal?.title}>
                  <small>{signal?.title} · {graph.byId.get(reading.sourceId)?.title}</small>
                  <b>{reading.value ?? '—'}<span>{reading.unit}</span></b>
                  <em>{reading.metric}</em>
                  <span className="reading-foot">
                    {reading.threshold.op === 'gt' ? '>' : '<'} {reading.threshold.value} · {reading.quality} · {reading.ageMinutes} min
                    <i>{state}</i>
                  </span>
                </button>
              )
            })}
          </div>
        </div>
        <aside className="panel reason-panel">
          <Segmented label="Reasoning detail" value={tab} onChange={setTab} options={[{ id: 'findings', label: 'Findings' }, { id: 'trace', label: `Trace · ${events.length}` }]} />
          {tab === 'trace' ? (
            <ol className="trace">
              {events.map((event) => (
                <li key={event.eventId} className={`trace-item s-${event.evidenceStatus.toLowerCase()}`}>
                  <span className="t">+{Date.parse(event.timestamp) - start0} ms</span>
                  <span className="n">{event.node}</span>
                  <p>{event.message}</p>
                  <em>{event.type} · {event.evidenceStatus}</em>
                </li>
              ))}
              {events.length === 0 && <li className="quiet">Run the graph to record a trace. Each row is a SQLite event written by a graph node.</li>}
            </ol>
          ) : !run ? (
            <div className="reason-intro">
              <h3 className="detail-title">How the graph decides</h3>
              <ol className="point-list">
                {['Ingest rejects stale, malformed or low-quality readings.', 'Detect compares accepted readings with thresholds.', 'A conditional edge routes to monitor, request evidence, or a parallel fan-out.', 'Each hypothesis linked to a breached signal is scored in its own task.', 'Synthesise ranks them and looks for a combined outcome.', 'The policy gate allows only monitor, request evidence or a proposal for a governed run.'].map((item, index) => (
                  <li key={item} className="point-item"><span className="num">{index + 1}</span>{item}</li>
                ))}
              </ol>
              <p className="fact">LangChain model calls are off. The narrator sits behind a provider interface and uses a deterministic template, so every run is reproducible.</p>
            </div>
          ) : (
            <Findings
              graph={graph}
              lens={lens}
              running={running}
              ranking={ranking}
              recommendation={recommendation}
              compound={compound ?? null}
              personas={personas}
              narrative={narrative}
              onPick={onPick}
              onNavigate={onNavigate}
              onCompound={onCompound}
            />
          )}
        </aside>
      </div>
    </section>
  )
}

function Findings({
  graph,
  lens,
  running,
  ranking,
  recommendation,
  compound,
  personas,
  narrative,
  onPick,
  onNavigate,
  onCompound,
}: {
  graph: Graph
  lens: LensId
  running: boolean
  ranking: Assessment[]
  recommendation?: Recommendation
  compound: { id: string; title: string; extendedOutcome: string; overlapPct: number } | null
  personas: { id: string; title: string }[]
  narrative?: ReasoningEvent
  onPick: (id: string) => void
  onNavigate: (mode: ModeId) => void
  onCompound: (id: string) => void
}) {
  const action = recommendation?.action
  return (
    <div className="findings">
      {recommendation ? (
        <div className={`rec rec-${action}`}>
          <small>Policy gate · {recommendation.policy.passed ? 'passed' : 'blocked'}</small>
          <h3>{action?.replace(/_/g, ' ')}</h3>
          <p>{recommendation.reason}</p>
          {recommendation.missingEvidence && recommendation.missingEvidence.length > 0 && (
            <ul>{recommendation.missingEvidence.map((item) => <li key={item}>{item}</li>)}</ul>
          )}
          <div className="rec-flags">
            <StatusPill>Executes action: no</StatusPill>
            {recommendation.requiresHumanApproval && <StatusPill>Human approval required</StatusPill>}
            <StatusPill tone="warn">{recommendation.valueStatus.replace('_', ' ')}</StatusPill>
          </div>
          {action === 'propose_live_workflow' && (
            <button type="button" className="ui-btn primary" onClick={() => onNavigate('live')}>
              Open governed Live Operations <ArrowRight size={15} />
            </button>
          )}
        </div>
      ) : (
        <p className="quiet">{running ? 'Graph is running. Findings appear as nodes finish.' : 'No recommendation recorded.'}</p>
      )}
      {ranking.length > 0 && (
        <>
          <span className="detail-sub">Hypotheses ranked by signal pattern (correlation, not cause)</span>
          <div className="ranking">
            {ranking.map((item) => (
              <button key={item.hypothesisId} type="button" className="rank-row" onClick={() => onPick(item.hypothesisId)}>
                <span className="rank-head"><b>{item.title}</b><em className={`band ${item.band}`}>{item.band}</em></span>
                <span className="rank-bar"><span style={{ width: `${Math.round(item.score * 100)}%` }} className={item.band} /></span>
                <small>
                  {item.contributions.map((c) => `${graph.byId.get(c.signalId)?.title} (${c.relation === 'supports-hypothesis' ? 'supports' : 'correlates'})`).join(' · ') || 'no contributing signal'}
                </small>
                {item.missingEvidence.length > 0 && <small className="warn-text">{item.missingEvidence[0]}</small>}
              </button>
            ))}
          </div>
        </>
      )}
      {compound && (
        <div className="compound-callout">
          <span className="extended-ico"><Star size={16} /></span>
          <div>
            <small>Combined outcome in play</small>
            <b>{compound.title}</b>
            <p>{compound.extendedOutcome}</p>
            <button type="button" className="ui-btn" onClick={() => onCompound(compound.id)}>See compound value <ArrowRight size={14} /></button>
          </div>
        </div>
      )}
      {personas.length > 0 && (
        <>
          <span className="detail-sub">{lens === 'customer' ? 'People to brief (read-only)' : 'Stakeholders in the loop'}</span>
          <div className="connected">
            {personas.map((p) => {
              const node = graph.byId.get(p.id)
              return node ? <LinkRow key={p.id} node={node} note={`persona · ${graph.byId.get(node.persona?.functionId || '')?.title || ''}`} onPick={onPick} /> : null
            })}
          </div>
        </>
      )}
      {narrative && (
        <div className="narrative">
          <small>Briefing · {String(narrative.details.narrativeSource)} · not a verified fact</small>
          <p>{String(narrative.details.narrative)}</p>
        </div>
      )}
    </div>
  )
}
