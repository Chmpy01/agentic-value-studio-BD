import type { ReactNode } from 'react'
import type { GraphNode } from './types'
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

export function Chain({
  ids,
  nodes,
  edges,
  selected,
  onSelect,
}: {
  ids: string[]
  nodes: GraphNode[]
  edges: { from: string; to: string; relation: string }[]
  selected: string
  onSelect: (id: string) => void
}) {
  return (
    <ol className="chain">
      {ids.map((id, index) => {
        const node = nodeById(nodes, id)
        if (!node) return null
        const previous = ids[index - 1]
        const edge = edges.find((item) => item.from === previous && item.to === id)
        return (
          <li key={id}>
            {index > 0 && <span className="relation">{edge?.relation || 'linked'}</span>}
            <button type="button" className={selected === id ? 'chain-node on' : 'chain-node'} onClick={() => onSelect(id)}>
              <Icon name={node.icon} size={16} />
              <small>{node.type}</small>
              <strong>{node.title}</strong>
            </button>
          </li>
        )
      })}
    </ol>
  )
}
