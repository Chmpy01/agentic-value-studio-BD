import { Star } from 'lucide-react'
import { LinkRow, money, StatusPill, ViewHeader } from './components'
import { compoundCase, hypothesisReach, sharedEnablers, unique, type Graph } from './graph'
import { Icon } from './icons'
import type { GraphNode, LensId, PackDetail } from './types'

const HUES = ['#3d8bff', '#16b39a', '#f0a24a']
const VENN = {
  2: { circles: [[235, 185], [365, 185]], r: 135, labels: [[150, 185], [450, 185]], core: [300, 185] },
  3: { circles: [[245, 150], [355, 150], [300, 245]], r: 118, labels: [[175, 118], [425, 118], [300, 312]], core: [300, 182] },
} as const

function pct(value: number, total: number) {
  return `${(value / total) * 100}%`
}

function Venn({ members, shared, outcome }: { members: GraphNode[]; shared: number; outcome: string }) {
  const layout = VENN[members.length === 3 ? 3 : 2]
  return (
    <div className="venn">
      <svg viewBox="0 0 600 370" role="img" aria-label={`${members.map((m) => m.title).join(', ')} combine into ${outcome}`}>
        <defs>
          {members.map((member, index) => (
            <radialGradient key={member.id} id={`venn-${index}`} cx="50%" cy="45%" r="60%">
              <stop offset="0%" stopColor={HUES[index]} stopOpacity="0.55" />
              <stop offset="100%" stopColor={HUES[index]} stopOpacity="0.18" />
            </radialGradient>
          ))}
          <filter id="venn-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="10" />
          </filter>
        </defs>
        {members.map((member, index) => {
          const [cx, cy] = layout.circles[index]
          return (
            <g key={member.id} className="venn-circle" style={{ animationDelay: `${index * 120}ms` }}>
              <circle cx={cx} cy={cy} r={layout.r} fill={`url(#venn-${index})`} stroke={HUES[index]} strokeOpacity="0.85" strokeWidth="1.5" style={{ mixBlendMode: 'screen' }} />
            </g>
          )
        })}
        <circle cx={layout.core[0]} cy={layout.core[1]} r="34" fill="#ffd36e" opacity="0.35" filter="url(#venn-glow)" className="venn-core" />
      </svg>
      {members.map((member, index) => {
        const [x, y] = layout.labels[index]
        return (
          <div key={member.id} className="venn-label" style={{ left: pct(x, 600), top: pct(y, 370) }}>
            <span className="venn-dot" style={{ background: HUES[index] }} />
            <b>{member.title}</b>
          </div>
        )
      })}
      <div className="venn-core-label" style={{ left: pct(layout.core[0], 600), top: pct(layout.core[1], 370) }}>
        <Star size={18} />
        <span>{shared} shared</span>
      </div>
    </div>
  )
}

export function CompoundView({
  pack,
  graph,
  lens,
  synergyId,
  setSynergyId,
  onPick,
}: {
  pack: PackDetail
  graph: Graph
  lens: LensId
  synergyId: string
  setSynergyId: (id: string) => void
  onPick: (id: string) => void
}) {
  const synergies = pack.overlay.synergies
  const synergy = synergies.find((item) => item.id === synergyId) || synergies[0]
  if (!synergy) return <p className="quiet">No combined outcomes are defined for this pack.</p>
  const model = compoundCase(graph, synergy)
  const shared = sharedEnablers(graph, synergy.hypothesisIds)
  const bridges = synergy.bridgeNodeIds
    .filter((id) => !shared.some((item) => item.node.id === id))
    .map((id) => graph.byId.get(id))
    .filter((node): node is GraphNode => Boolean(node))
  const reaches = synergy.hypothesisIds.map((id) => hypothesisReach(graph, id))
  const boards = graph.nodes.filter((node) => node.type === 'board')
  const reached = new Set(reaches.flatMap((reach) => reach.boards.map((board) => board.id)))
  const bestAlone = Math.max(...reaches.map((reach) => reach.boards.length))
  const offers = unique(reaches.flatMap((reach) => reach.offers))
  const partners = unique(reaches.flatMap((reach) => reach.partners))
  const capabilities = unique(reaches.flatMap((reach) => reach.capabilities))
  const coordination = graph.edges.filter((edge) => edge.relation === 'coordinates-with' && partners.some((p) => p.id === edge.from) && partners.some((p) => p.id === edge.to))
  const stack = [
    ...model.cases.map((item, index) => ({ label: item.node.title, value: item.numbers?.gross ?? 0, kind: 'add', hue: HUES[index] })),
    { label: 'Overlap removed', value: -model.overlap, kind: 'minus', hue: '#e0645c' },
    { label: 'Combined gross', value: model.combinedGross, kind: 'total', hue: '#1669e8' },
  ]
  const max = Math.max(model.standaloneGross, 1)
  let running = 0
  return (
    <section className="section">
      <ViewHeader
        overline="Combined outcomes · extended value"
        title="Outcomes compound when they share signals, platforms and owners."
        text="Pick a combination. Shared enablers come from the graph; the extended outcome and overlap factors are authored assumptions to test."
        pill="Modelled · not measured"
        tone="warn"
      />
      <div className="case-row">
        {synergies.map((item) => (
          <button key={item.id} type="button" className={`econ-case ${item.id === synergy.id ? 'active' : ''}`} onClick={() => setSynergyId(item.id)}>
            <small>{item.hypothesisIds.length} outcomes combined</small>
            <b>{item.title}</b>
          </button>
        ))}
      </div>
      <div className="graph-layout">
        <div className="compound-hero">
          <div className="hero-top">
            <span className="canvas-eyebrow static">Value convergence · {synergy.evidenceStatus}</span>
            <span className="hero-note">Graph-derived overlap · authored extended outcome</span>
          </div>
          <Venn members={model.members} shared={shared.length + bridges.length} outcome={synergy.extendedOutcome} />
          <div className="extended">
            <span className="extended-ico"><Star size={18} /></span>
            <div>
              <small>Extended outcome · only reachable together</small>
              <p>{synergy.extendedOutcome}</p>
            </div>
          </div>
          <div className="enablers">
            {shared.map(({ node, count }) => (
              <button key={node.id} type="button" className="enabler" onClick={() => onPick(node.id)} title={`Shared by ${count} outcomes`}>
                <Icon name={node.type === 'persona' ? 'user' : node.icon} size={13} /> {node.title}
                <em>{node.type}</em>
              </button>
            ))}
            {bridges.map((node) => (
              <button key={node.id} type="button" className="enabler authored" onClick={() => onPick(node.id)} title="Authored bridge: validate">
                <Icon name={node.icon} size={13} /> {node.title}
                <em>authored bridge</em>
              </button>
            ))}
          </div>
          <div className="board-reach">
            <span>Board objectives advanced</span>
            {boards.map((board) => (
              <button key={board.id} type="button" className={`reach ${reached.has(board.id) ? 'on' : ''}`} onClick={() => onPick(board.id)}>
                <Icon name="target" size={13} /> {board.title}
              </button>
            ))}
            <b>Best single outcome reaches {bestAlone} of {boards.length}; combined reaches {reached.size}.</b>
          </div>
        </div>
        <aside className="panel compound-panel">
          <span className="overline">{pack.design.lenses[lens]?.label} lens</span>
          <h3 className="detail-title">{synergy.title}</h3>
          <p className="detail-summary">{synergy.mechanism}</p>
          {lens === 'customer' && (
            <>
              <span className="detail-sub">Value stack (annual, modelled)</span>
              <div className="waterfall">
                {stack.map((step) => {
                  const start = step.kind === 'total' ? 0 : step.kind === 'minus' ? running + step.value : running
                  const width = Math.abs(step.value)
                  if (step.kind === 'add') running += step.value
                  if (step.kind === 'minus') running += step.value
                  return (
                    <div key={step.label} className={`wf-row ${step.kind}`}>
                      <span className="wf-label">{step.label}</span>
                      <span className="wf-track">
                        <span className="wf-bar" style={{ left: pct(start, max), width: pct(width, max), background: step.hue }} />
                      </span>
                      <span className="wf-value">{money(step.value)}</span>
                    </div>
                  )
                })}
                <div className="wf-row extended-row">
                  <span className="wf-label">Extended outcome</span>
                  <span className="wf-track"><span className="wf-bar hatched" style={{ left: '0%', width: '100%' }} /></span>
                  <span className="wf-value">Not quantified</span>
                </div>
              </div>
              <div className="mini-stats">
                <div><small>Implementation</small><b>{money(model.combinedImplementation)}</b><span>{money(model.sharedSaving)} shared ({synergy.sharedImplementationPct}%)</span></div>
                <div><small>Net / year</small><b>{money(model.combinedNet)}</b><span>after {money(model.service)} service</span></div>
                <div><small>Payback</small><b>{Number.isFinite(model.payback) && model.payback >= 0 ? `${model.payback.toFixed(1)} mo` : 'N/A'}</b><span>not risk-adjusted</span></div>
              </div>
              <p className="fact">Overlap of {synergy.overlapPct}% is deducted so the same benefit is not claimed twice. The extended outcome needs an interaction test before any value is attached.</p>
            </>
          )}
          {lens === 'partner' && (
            <>
              <span className="detail-sub">One combined offer instead of {synergy.hypothesisIds.length}</span>
              <div className="connected">{offers.map((node) => <LinkRow key={node.id} node={node} note={node.summary} onPick={onPick} />)}</div>
              <span className="detail-sub">Delivery partners</span>
              <div className="connected">{partners.map((node) => <LinkRow key={node.id} node={node} note={node.summary} onPick={onPick} />)}</div>
              {coordination.length > 0 && <p className="fact">Graph shows {coordination.map((edge) => `${graph.byId.get(edge.from)?.title} coordinates with ${graph.byId.get(edge.to)?.title}`).join('; ')}.</p>}
              <p className="fact">Modelled service revenue {money(model.service)} / year is partner revenue, kept apart from customer value.</p>
            </>
          )}
          {lens === 'cisco' && (
            <>
              <span className="detail-sub">Capabilities across the combination</span>
              <div className="connected">{capabilities.map((node) => <LinkRow key={node.id} node={node} note={node.summary} onPick={onPick} />)}</div>
              <span className="detail-sub">Shared data foundation</span>
              <div className="connected">
                {[...shared.map((item) => item.node), ...bridges].filter((node) => node.type === 'source').map((node) => <LinkRow key={node.id} node={node} note="reused across outcomes" onPick={onPick} />)}
              </div>
              <p className="fact">Capabilities are positioned only after the combined hypothesis is validated. No booking figure is stated.</p>
            </>
          )}
          <span className="detail-sub">Evidence needed before claiming the combination</span>
          <ol className="point-list">
            {synergy.evidenceNeeded.map((item, index) => (
              <li key={item} className="point-item"><span className="num">{index + 1}</span>{item}</li>
            ))}
          </ol>
          <StatusPill tone="warn">NOT MEASURED</StatusPill>
        </aside>
      </div>
    </section>
  )
}
