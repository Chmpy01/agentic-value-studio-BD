import { useEffect, useMemo, useState } from 'react'
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from '@xyflow/react'
import { ArrowRight, ChevronRight } from 'lucide-react'
import { LinkRow, NodeDetail, Segmented, ViewHeader } from './components'
import { functionsForBoard, hypothesisReach, iconFor, neighbours, personasForFunction, TYPE_ORDER, type Graph } from './graph'
import { Icon } from './icons'
import type { GraphNode, LensId, PackDetail } from './types'

type GraphMode = 'paths' | 'graph' | 'people'

export function ValueGraphView({
  pack,
  graph,
  lens,
  selected,
  onSelect,
}: {
  pack: PackDetail
  graph: Graph
  lens: LensId
  selected: string
  onSelect: (id: string) => void
}) {
  const [mode, setMode] = useState<GraphMode>('paths')
  return (
    <section className="section">
      <ViewHeader
        overline="Connected knowledge graph"
        title="The traceable chain from customer outcome to partner offer."
        text="Choose a graph path, explore the whole graph, or drill from a board objective to the people who act on it. Click any node to see provenance and neighbours."
        pill={`${graph.edges.length} typed relationships`}
      />
      <Segmented
        label="Graph view"
        value={mode}
        onChange={setMode}
        options={[
          { id: 'paths', label: 'Value paths', icon: 'waypoints' },
          { id: 'graph', label: 'Knowledge graph', icon: 'network' },
          { id: 'people', label: 'Board → function → persona', icon: 'users' },
        ]}
      />
      {mode === 'paths' && <PathsView pack={pack} graph={graph} selected={selected} onSelect={onSelect} />}
      {mode === 'graph' && <KnowledgeGraph pack={pack} graph={graph} lens={lens} selected={selected} onSelect={onSelect} />}
      {mode === 'people' && <AccountabilityView graph={graph} lens={lens} onSelect={onSelect} />}
    </section>
  )
}

function pathColumns(graph: Graph, nodeIds: string[]) {
  const hypotheses = nodeIds.filter((id) => graph.byId.get(id)?.type === 'hypothesis')
  const columns: { nodes: GraphNode[]; overlay: boolean }[] = []
  for (const id of nodeIds) {
    const node = graph.byId.get(id)
    if (!node) continue
    columns.push({ nodes: [node], overlay: false })
    if (node.type === 'function') {
      const personas = personasForFunction(graph, id).filter(
        (persona) => !hypotheses.length || persona.persona?.hypothesisIds.some((h) => hypotheses.includes(h)),
      )
      if (personas.length) columns.push({ nodes: personas.slice(0, 2), overlay: true })
    }
  }
  return columns
}

function PathsView({ pack, graph, selected, onSelect }: { pack: PackDetail; graph: Graph; selected: string; onSelect: (id: string) => void }) {
  const [trackId, setTrackId] = useState(pack.design.tracks[0]?.id)
  const track = pack.design.tracks.find((item) => item.id === trackId) || pack.design.tracks[0]
  const columns = useMemo(() => pathColumns(graph, track?.nodeIds || []), [graph, track])
  const inPath = columns.some((column) => column.nodes.some((node) => node.id === selected))
  const shown = inPath ? selected : columns[0]?.nodes[0]?.id || ''
  return (
    <>
      <div className="track-bar">
        {pack.design.tracks.map((item) => (
          <button key={item.id} type="button" className={item.id === track?.id ? 'chip on' : 'chip'} onClick={() => { setTrackId(item.id); onSelect(item.nodeIds[0]) }}>
            {item.label}
          </button>
        ))}
      </div>
      <div className="graph-layout">
        <div className="graph-canvas">
          <div className="graphpath">
            {columns.map((column, index) => {
              const previous = columns[index - 1]?.nodes[0]
              const edge = previous && graph.edges.find((item) => item.from === previous.id && column.nodes.some((node) => node.id === item.to))
              return (
                <div key={column.nodes.map((node) => node.id).join('-')} className="gstep">
                  {index > 0 && (
                    <span className="gconn" title={edge?.relation || 'linked in this path'}>
                      <ArrowRight size={18} />
                      <small>{edge?.relation || ''}</small>
                    </span>
                  )}
                  <div className={column.nodes.length > 1 ? 'gstack' : ''}>
                    {column.nodes.map((node) => (
                      <button
                        key={node.id}
                        type="button"
                        className={`gnode ${column.overlay ? 'overlay' : ''} ${shown === node.id ? 'active' : ''} ${column.nodes.length > 1 ? 'compact' : ''}`}
                        onClick={() => onSelect(node.id)}
                      >
                        <Icon name={iconFor(node, pack)} size={column.nodes.length > 1 ? 15 : 19} />
                        <small>{node.type}</small>
                        <b>{node.title}</b>
                      </button>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
          <p className="canvas-caption">
            Typed connections describe why a capability or partner is relevant. Dashed cards are overlay personas. Hypotheses require evidence before any causal or value claims.
          </p>
        </div>
        <aside className="panel">
          <NodeDetail graph={graph} id={shown} onPick={onSelect} />
        </aside>
      </div>
    </>
  )
}

type KgData = { node: GraphNode; icon: string; state: 'idle' | 'active' | 'near' | 'dim' }
type LabelData = { label: string; count: number }

function KgNode({ data }: NodeProps<Node<KgData>>) {
  return (
    <div className={`kg-node t-${data.node.type} ${data.state}`}>
      <Handle type="target" position={Position.Left} />
      <span className="kg-ico"><Icon name={data.icon} size={14} /></span>
      <span>
        <small>{data.node.type}</small>
        <strong>{data.node.title}</strong>
      </span>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}

function LabelNode({ data }: NodeProps<Node<LabelData>>) {
  return (
    <div className="kg-label">
      {data.label}
      <span>{data.count}</span>
    </div>
  )
}

const kgTypes = { kg: KgNode, label: LabelNode }
const COL_W = 215
const ROW_H = 74

const LENS_TYPES: Record<LensId, string[]> = {
  customer: ['board', 'function', 'persona', 'hypothesis', 'metric'],
  partner: ['hypothesis', 'partner', 'offer', 'capability'],
  cisco: ['signal', 'source', 'capability', 'hypothesis'],
}

function KnowledgeGraph(props: { pack: PackDetail; graph: Graph; lens: LensId; selected: string; onSelect: (id: string) => void }) {
  return (
    <ReactFlowProvider>
      <KnowledgeGraphInner {...props} />
    </ReactFlowProvider>
  )
}

function KnowledgeGraphInner({ pack, graph, lens, selected, onSelect }: { pack: PackDetail; graph: Graph; lens: LensId; selected: string; onSelect: (id: string) => void }) {
  const [streams, setStreams] = useState(false)
  const [lensFocus, setLensFocus] = useState(false)
  const flow = useReactFlow()
  const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const { types, visible, tallest } = useMemo(() => {
    const kinds: string[] = TYPE_ORDER.filter((type) => (streams || type !== 'stream') && graph.nodes.some((node) => node.type === type))
    const shown = graph.nodes.filter((node) => kinds.includes(node.type))
    return { types: kinds, visible: shown, tallest: Math.max(...kinds.map((type) => shown.filter((node) => node.type === type).length)) }
  }, [graph, streams])
  const near = useMemo(() => new Set([selected, ...neighbours(graph, selected).map((item) => item.other.id)]), [graph, selected])
  const hasSelection = graph.byId.has(selected) && types.includes(graph.byId.get(selected)!.type)

  const nodes = useMemo<Node[]>(() => {
    const result: Node[] = []
    types.forEach((type, column) => {
      const members = visible.filter((node) => node.type === type)
      const offset = ((tallest - members.length) * ROW_H) / 2
      result.push({
        id: `label-${type}`,
        type: 'label',
        position: { x: column * COL_W, y: -70 },
        data: { label: type, count: members.length },
        selectable: false,
        draggable: false,
      })
      members.forEach((node, row) => {
        let state: KgData['state'] = 'idle'
        if (hasSelection) state = node.id === selected ? 'active' : near.has(node.id) ? 'near' : 'dim'
        else if (lensFocus && !LENS_TYPES[lens].includes(node.type)) state = 'dim'
        result.push({
          id: node.id,
          type: 'kg',
          position: { x: column * COL_W, y: offset + row * ROW_H },
          data: { node, icon: iconFor(node, pack), state },
        })
      })
    })
    return result
  }, [types, visible, tallest, hasSelection, selected, near, lensFocus, lens, pack])

  const edges = useMemo<Edge[]>(() => {
    const ids = new Set(visible.map((node) => node.id))
    return graph.edges
      .filter((edge) => ids.has(edge.from) && ids.has(edge.to))
      .map((edge) => {
        const lit = hasSelection && (edge.from === selected || edge.to === selected)
        return {
          id: `${edge.from}-${edge.relation}-${edge.to}`,
          source: edge.from,
          target: edge.to,
          label: lit ? edge.relation : undefined,
          animated: lit && !reduced,
          className: lit ? 'kg-edge lit' : hasSelection ? 'kg-edge faded' : 'kg-edge',
          labelBgPadding: [6, 3] as [number, number],
          labelBgBorderRadius: 6,
        }
      })
  }, [graph.edges, visible, hasSelection, selected, reduced])

  useEffect(() => {
    if (!hasSelection) return
    const ids = [...near].filter((id) => visible.some((node) => node.id === id)).map((id) => ({ id }))
    const timer = window.setTimeout(() => flow.fitView({ nodes: ids, duration: reduced ? 0 : 600, padding: 0.35, maxZoom: 1.15 }), 30)
    return () => window.clearTimeout(timer)
  }, [selected, hasSelection, flow, near, visible, reduced])

  return (
    <div className="graph-layout">
      <div className="kg-wrap">
        <div className="kg-toolbar">
          <button type="button" className="chip" onClick={() => { onSelect(''); flow.fitView({ duration: reduced ? 0 : 500, padding: 0.08 }) }}>
            Show whole graph
          </button>
          <button type="button" className={streams ? 'chip on' : 'chip'} aria-pressed={streams} onClick={() => setStreams((value) => !value)}>
            Value streams
          </button>
          <button type="button" className={lensFocus ? 'chip on' : 'chip'} aria-pressed={lensFocus} onClick={() => { setLensFocus((value) => !value); onSelect('') }}>
            Highlight {pack.design.lenses[lens]?.label || lens} lens
          </button>
        </div>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={kgTypes}
          fitView
          fitViewOptions={{ padding: 0.08 }}
          minZoom={0.2}
          nodesDraggable={false}
          onNodeClick={(_, node) => {
            if (node.type === 'kg') onSelect(node.id)
          }}
          onPaneClick={() => onSelect('')}
        >
          <Background gap={22} />
          <Controls showInteractive={false} />
          <MiniMap pannable zoomable className="kg-minimap" />
        </ReactFlow>
      </div>
      <aside className="panel">
        {hasSelection ? (
          <NodeDetail graph={graph} id={selected} onPick={onSelect} />
        ) : (
          <>
            <span className="overline">Navigable graph</span>
            <h3 className="detail-title">{graph.nodes.length} nodes · {graph.edges.length} links</h3>
            <p className="detail-summary">Columns run from board intent to commercial offer. Click a node to focus its neighbourhood, then follow a link on the right to walk the graph.</p>
            <span className="detail-sub">Start from a board objective</span>
            <div className="connected">
              {graph.nodes.filter((node) => node.type === 'board').map((node) => (
                <LinkRow key={node.id} node={node} note={node.summary} onPick={onSelect} />
              ))}
            </div>
            <p className="fact">Persona nodes and their edges come from the project overlay. Design graph IDs are unchanged.</p>
          </>
        )}
      </aside>
    </div>
  )
}

function AccountabilityView({ graph, lens, onSelect }: { graph: Graph; lens: LensId; onSelect: (id: string) => void }) {
  const boards = graph.nodes.filter((node) => node.type === 'board')
  const [boardId, setBoardId] = useState(boards[0]?.id || '')
  const functions = functionsForBoard(graph, boardId)
  const [functionId, setFunctionId] = useState(functions[0]?.node.id || '')
  const activeFunction = functions.some((item) => item.node.id === functionId) ? functionId : functions[0]?.node.id || ''
  const personas = personasForFunction(graph, activeFunction)
  const [personaId, setPersonaId] = useState('')
  const activePersona = personas.find((item) => item.id === personaId) || personas[0]
  const board = graph.byId.get(boardId)
  const fn = graph.byId.get(activeFunction)

  function chooseBoard(id: string) {
    setBoardId(id)
    const first = functionsForBoard(graph, id)[0]?.node.id || ''
    setFunctionId(first)
    setPersonaId('')
  }

  return (
    <div className="people">
      <nav className="crumbs" aria-label="Accountability path">
        <span>{board?.title}</span>
        <ChevronRight size={14} />
        <span>{fn?.title || 'No function linked'}</span>
        <ChevronRight size={14} />
        <span className="here">{activePersona?.title || 'No persona yet'}</span>
      </nav>
      <div className="people-grid">
        <div className="people-col">
          <span className="col-head"><Icon name="target" size={14} /> Board objective</span>
          {boards.map((item) => (
            <button key={item.id} type="button" className={`pcard ${item.id === boardId ? 'active' : ''}`} onClick={() => chooseBoard(item.id)}>
              <b>{item.title}</b>
              <small>{item.summary}</small>
              <em>{functionsForBoard(graph, item.id).length} accountable functions</em>
            </button>
          ))}
        </div>
        <div className="people-col">
          <span className="col-head"><Icon name="users" size={14} /> Accountable function</span>
          {functions.map(({ node, relation }) => (
            <button key={node.id} type="button" className={`pcard ${node.id === activeFunction ? 'active' : ''}`} onClick={() => { setFunctionId(node.id); setPersonaId('') }}>
              <span className="rel-badge">{relation}</span>
              <b>{node.title}</b>
              <small>{outgoingSignals(graph, node.id)}</small>
              <em>{personasForFunction(graph, node.id).length} personas</em>
            </button>
          ))}
          {functions.length === 0 && <p className="quiet">No function is linked to this objective in the pack.</p>}
        </div>
        <div className="people-col">
          <span className="col-head"><Icon name="user" size={14} /> Persona</span>
          {personas.map((node) => (
            <button key={node.id} type="button" className={`pcard persona ${node.id === activePersona?.id ? 'active' : ''}`} onClick={() => setPersonaId(node.id)}>
              <span className="avatar">{initials(node.title)}</span>
              <span>
                <b>{node.title}</b>
                <small>{node.summary}</small>
              </span>
            </button>
          ))}
          {personas.length === 0 && <p className="quiet">No persona has been captured for this function yet.</p>}
        </div>
        <aside className="panel persona-panel">
          {activePersona?.persona ? (
            <PersonaCard graph={graph} node={activePersona} lens={lens} onSelect={onSelect} />
          ) : (
            <p className="quiet">Choose a function with personas to see goals, decisions and the signals they act on.</p>
          )}
        </aside>
      </div>
    </div>
  )
}

function outgoingSignals(graph: Graph, functionId: string) {
  const signals = graph.edges.filter((edge) => edge.from === functionId && edge.relation === 'informed-by').map((edge) => graph.byId.get(edge.to)?.title)
  const controls = graph.edges.filter((edge) => edge.from === functionId && edge.relation === 'owns-control').map((edge) => graph.byId.get(edge.to)?.summary)
  if (signals.length) return `Informed by ${signals.join(', ')}`
  if (controls.length) return `Owns control: ${controls.join(', ')}`
  return 'Sponsor or governance role'
}

function initials(title: string) {
  return title.split(/[\s/&]+/).filter(Boolean).slice(0, 2).map((word) => word[0]).join('').toUpperCase()
}

function PersonaCard({ graph, node, lens, onSelect }: { graph: Graph; node: GraphNode; lens: LensId; onSelect: (id: string) => void }) {
  const persona = node.persona!
  const signals = persona.signalIds.map((id) => graph.byId.get(id)).filter((item): item is GraphNode => Boolean(item))
  const hypotheses = persona.hypothesisIds.map((id) => graph.byId.get(id)).filter((item): item is GraphNode => Boolean(item))
  const lensLine: Record<LensId, string> = {
    customer: 'Customer lens: what this person must believe before the outcome is funded.',
    partner: 'Partner lens: who you design discovery, integration and managed service around.',
    cisco: 'Cisco + ecosystem lens: which signals and platforms this person depends on.',
  }
  return (
    <div className="persona-card">
      <div className="persona-head">
        <span className="avatar lg">{initials(persona.title)}</span>
        <div>
          <span className="overline">Persona · {persona.evidenceStatus}</span>
          <h3 className="detail-title">{persona.title}</h3>
          <p className="detail-summary">{persona.archetype}</p>
        </div>
      </div>
      {persona.quote && <blockquote className="persona-quote">“{persona.quote}”</blockquote>}
      <div className="persona-grid">
        <div><span className="detail-sub">Goals</span><ul>{persona.goals.map((item) => <li key={item}>{item}</li>)}</ul></div>
        <div><span className="detail-sub">Pain points</span><ul>{persona.pains.map((item) => <li key={item}>{item}</li>)}</ul></div>
        <div><span className="detail-sub">Decisions</span><ul>{persona.decisions.map((item) => <li key={item}>{item}</li>)}</ul></div>
        <div><span className="detail-sub">KPIs</span><div className="tags">{persona.kpis.map((item) => <span key={item} className="tag">{item}</span>)}</div></div>
      </div>
      <span className="detail-sub">Acts on signals</span>
      <div className="connected">
        {signals.map((item) => <LinkRow key={item.id} node={item} note="watches · signal" onPick={onSelect} />)}
      </div>
      <span className="detail-sub">Influences value hypotheses</span>
      <div className="connected">
        {hypotheses.map((item) => {
          const reach = hypothesisReach(graph, item.id)
          return <LinkRow key={item.id} node={item} note={`measured by ${reach.metrics.map((m) => m.title).join(', ') || 'metric to define'}`} onPick={onSelect} />
        })}
      </div>
      <p className="fact">{lensLine[lens]} Archetype only; validate with real stakeholders before use.</p>
    </div>
  )
}
