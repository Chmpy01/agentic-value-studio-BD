import type { ReactNode } from 'react'
import type { GraphNode } from './types'
import { iconFor, neighbours, type Graph } from './graph'
import { Icon } from './icons'

export function Building({
  src,
  hotspots,
  nodes,
  active,
  onPick,
  eyebrow,
  badge,
}: {
  src: string
  hotspots: { nodeId: string; x: number; y: number }[]
  nodes: GraphNode[]
  active: string[]
  onPick?: (id: string) => void
  eyebrow?: string
  badge?: string
}) {
  return (
    <div className="canvas">
      <img className="canvas-image" src={src} alt="" />
      {eyebrow && <span className="canvas-eyebrow">{eyebrow}</span>}
      {hotspots.map((spot) => {
        const node = nodes.find((item) => item.id === spot.nodeId)
        const on = active.includes(spot.nodeId)
        return (
          <button
            key={spot.nodeId}
            type="button"
            className={on ? 'hotspot on' : 'hotspot'}
            style={{ left: `${spot.x}%`, top: `${spot.y}%` }}
            aria-label={node?.title || spot.nodeId}
            title={node?.title}
            onClick={() => onPick?.(spot.nodeId)}
          >
            <Icon name={node?.icon} size={17} />
          </button>
        )
      })}
      {badge && <span className="canvas-badge">{badge}</span>}
      <span className="canvas-watermark">Concept visual · no customer telemetry</span>
    </div>
  )
}

export function Drawer({
  open,
  title,
  onClose,
  children,
}: {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
}) {
  if (!open) return null
  return (
    <aside className="drawer" role="dialog" aria-label={title}>
      <header>
        <strong>{title}</strong>
        <button type="button" onClick={onClose}>
          Close
        </button>
      </header>
      <div>{children}</div>
    </aside>
  )
}

export function StatusPill({ children, tone = 'neutral' }: { children: ReactNode; tone?: string }) {
  return <span className={`pill tone-${tone}`}>{children}</span>
}

export function money(value?: number, currency = 'GBP') {
  if (value == null) return null
  return new Intl.NumberFormat('en-GB', { style: 'currency', currency, maximumFractionDigits: 0 }).format(value)
}

export function nodeById(nodes: GraphNode[], id: string) {
  return nodes.find((node) => node.id === id)
}

export function ViewHeader({ overline, title, text, pill, tone }: { overline: string; title: string; text?: string; pill?: ReactNode; tone?: string }) {
  return (
    <div className="view-header">
      <div>
        <span className="overline">{overline}</span>
        <h2>{title}</h2>
        {text && <p>{text}</p>}
      </div>
      {pill && <StatusPill tone={tone}>{pill}</StatusPill>}
    </div>
  )
}

export function Segmented<T extends string>({
  value,
  options,
  onChange,
  label,
}: {
  value: T
  options: { id: T; label: string; icon?: string }[]
  onChange: (value: T) => void
  label: string
}) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((option) => (
        <button key={option.id} type="button" className={value === option.id ? 'active' : ''} aria-pressed={value === option.id} onClick={() => onChange(option.id)}>
          {option.icon && <Icon name={option.icon} size={15} />}
          {option.label}
        </button>
      ))}
    </div>
  )
}

export function LinkRow({ node, note, onPick }: { node: GraphNode; note?: string; onPick?: (id: string) => void }) {
  return (
    <button type="button" className="link-row" onClick={() => onPick?.(node.id)}>
      <span className="link-ico"><Icon name={iconFor(node)} size={16} /></span>
      <span>
        <b>{node.title}</b>
        <small>{note ?? node.type}</small>
      </span>
    </button>
  )
}

function Tags({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null
  return (
    <div className="tag-block">
      <span className="detail-sub">{title}</span>
      <div className="tags">
        {items.map((item) => (
          <span key={item} className="tag">{item}</span>
        ))}
      </div>
    </div>
  )
}

export function NodeDetail({ graph, id, onPick, limit = 12 }: { graph: Graph; id: string; onPick: (id: string) => void; limit?: number }) {
  const node = graph.byId.get(id)
  if (!node) return <p className="quiet">Select a node to see its provenance and neighbours.</p>
  const related = neighbours(graph, id)
  const persona = node.persona
  return (
    <div className="node-detail">
      <div className="big-icon"><Icon name={iconFor(node)} size={22} /></div>
      <span className="overline">{node.type} · {node.evidenceStatus || 'unverified'}</span>
      <h3 className="detail-title">{node.title}</h3>
      <p className="detail-summary">{node.summary}</p>
      {persona?.quote && <blockquote className="persona-quote">“{persona.quote}”</blockquote>}
      {persona && (
        <>
          <Tags title="Goals" items={persona.goals} />
          <Tags title="Pain points" items={persona.pains} />
          <Tags title="Decisions they own" items={persona.decisions} />
          <Tags title="KPIs they watch" items={persona.kpis} />
        </>
      )}
      {node.financialModel && (
        <div className="fact">
          Illustrative model inputs: addressable pool {money(node.financialModel.annualPoolGBP)}, opportunity {node.financialModel.opportunityPct}%.
          Not a measured customer result.
        </div>
      )}
      <div className="fact">
        Confidence: {node.confidence || 'not graded'} · Relationship count: {related.length}. A graph link does not establish cause and effect.
        {persona && ' Personas are overlay archetypes, not named people.'}
      </div>
      <span className="detail-sub">Connected reasoning</span>
      <div className="connected">
        {related.slice(0, limit).map(({ edge, other }) => (
          <LinkRow key={`${edge.from}-${edge.relation}-${edge.to}`} node={other} note={`${edge.relation} · ${other.type}`} onPick={onPick} />
        ))}
        {related.length === 0 && <p className="quiet">No connected nodes.</p>}
      </div>
    </div>
  )
}
