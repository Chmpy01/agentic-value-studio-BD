import type { GraphEdge, GraphNode, PackDetail, Synergy } from './types'

export interface Graph {
  nodes: GraphNode[]
  edges: GraphEdge[]
  byId: Map<string, GraphNode>
}

export const TYPE_ORDER = [
  'board',
  'function',
  'persona',
  'source',
  'signal',
  'hypothesis',
  'metric',
  'risk',
  'capability',
  'partner',
  'offer',
  'stream',
] as const

const DEFAULT_ICONS: Record<string, string> = {
  board: 'target',
  function: 'users',
  persona: 'user',
  signal: 'activity',
  source: 'database',
  hypothesis: 'spark',
  metric: 'chart',
  capability: 'network',
  partner: 'handshake',
  offer: 'briefcase',
  risk: 'shield',
  stream: 'layers',
}

export function iconFor(node: GraphNode | undefined, pack?: PackDetail) {
  if (!node) return 'layers'
  return pack?.design.ui?.iconMap?.[node.type] || DEFAULT_ICONS[node.type] || node.icon
}

/** Design graph plus overlay personas. Design IDs and edges are kept exactly as supplied. */
export function buildGraph(pack: PackDetail): Graph {
  const personas: GraphNode[] = pack.overlay.personas.map((persona) => ({
    id: persona.id,
    type: 'persona',
    title: persona.title,
    summary: persona.archetype,
    icon: 'user',
    evidenceStatus: persona.evidenceStatus,
    confidence: 'archetype',
    persona,
  }))
  const personaEdges: GraphEdge[] = pack.overlay.personas.flatMap((persona) => [
    { from: persona.functionId, to: persona.id, relation: 'represented-by', rationale: 'Overlay persona archetype within this function.' },
    ...persona.signalIds.map((id) => ({ from: persona.id, to: id, relation: 'watches', rationale: 'Persona acts on this signal.' })),
    ...persona.hypothesisIds.map((id) => ({ from: persona.id, to: id, relation: 'influences', rationale: 'Persona decides or is affected.' })),
  ])
  const nodes = [...pack.design.nodes, ...personas]
  return { nodes, edges: [...pack.design.edges, ...personaEdges], byId: new Map(nodes.map((node) => [node.id, node])) }
}

export function outgoing(graph: Graph, id: string, relations?: string[]) {
  return graph.edges
    .filter((edge) => edge.from === id && (!relations || relations.includes(edge.relation)))
    .map((edge) => graph.byId.get(edge.to))
    .filter((node): node is GraphNode => Boolean(node))
}

export function incoming(graph: Graph, id: string, relations?: string[]) {
  return graph.edges
    .filter((edge) => edge.to === id && (!relations || relations.includes(edge.relation)))
    .map((edge) => graph.byId.get(edge.from))
    .filter((node): node is GraphNode => Boolean(node))
}

export function neighbours(graph: Graph, id: string) {
  return graph.edges
    .filter((edge) => edge.from === id || edge.to === id)
    .map((edge) => ({ edge, other: graph.byId.get(edge.from === id ? edge.to : edge.from), outbound: edge.from === id }))
    .filter((item): item is { edge: GraphEdge; other: GraphNode; outbound: boolean } => Boolean(item.other))
}

export function unique<T extends { id: string }>(items: T[]) {
  return [...new Map(items.map((item) => [item.id, item])).values()]
}

export const BOARD_RELATIONS = ['owned-by', 'sponsored-by', 'governed-by']

export function functionsForBoard(graph: Graph, boardId: string) {
  return graph.edges
    .filter((edge) => edge.from === boardId && BOARD_RELATIONS.includes(edge.relation))
    .map((edge) => ({ relation: edge.relation, node: graph.byId.get(edge.to) }))
    .filter((item): item is { relation: string; node: GraphNode } => item.node?.type === 'function')
}

export function personasForFunction(graph: Graph, functionId: string) {
  return outgoing(graph, functionId, ['represented-by'])
}

/** Every node a hypothesis draws on, used to find what combined hypotheses share. */
export function hypothesisReach(graph: Graph, hypothesisId: string) {
  const direct = incoming(graph, hypothesisId, ['supports-hypothesis'])
  const signals = unique([...direct, ...incoming(graph, hypothesisId, ['correlates-with']).filter((node) => node.type === 'signal')])
  const sources = unique(signals.flatMap((signal) => incoming(graph, signal.id, ['produces'])))
  const capabilities = outgoing(graph, hypothesisId, ['requires-capability'])
  const deliveryPartners = capabilities.flatMap((capability) => outgoing(graph, capability.id, ['delivered-with']))
  const partners = unique([
    ...deliveryPartners,
    ...deliveryPartners.flatMap((partner) => [
      ...outgoing(graph, partner.id, ['coordinates-with']),
      ...incoming(graph, partner.id, ['coordinates-with']),
    ]),
  ])
  const offers = unique(partners.flatMap((partner) => outgoing(graph, partner.id, ['monetises-through'])))
  const functions = unique(direct.flatMap((signal) => incoming(graph, signal.id, ['informed-by'])))
  const boards = unique(functions.flatMap((fn) => incoming(graph, fn.id, BOARD_RELATIONS)))
  const personas = incoming(graph, hypothesisId, ['influences'])
  const metrics = outgoing(graph, hypothesisId, ['measured-by'])
  const risks = outgoing(graph, hypothesisId, ['constrained-by'])
  return { signals, sources, capabilities, partners, offers, functions, boards, personas, metrics, risks }
}

export interface CaseNumbers {
  pool: number
  pct: number
  capture: number
  gross: number
  net: number
  investment: number
  service: number
  firstYear: number
  payback: number
}

export function modelCase(node: GraphNode, pct?: number, capture?: number): CaseNumbers | null {
  const model = node.financialModel
  if (!model) return null
  const pool = model.annualPoolGBP ?? 0
  const opportunity = pct ?? model.opportunityPct ?? 0
  const factor = capture ?? model.captureFactor ?? 0
  const gross = (pool * opportunity) / 100 * factor
  const service = model.serviceAnnualGBP ?? 0
  const investment = model.implementationGBP ?? 0
  const net = gross - service
  return {
    pool,
    pct: opportunity,
    capture: factor,
    gross,
    net,
    investment,
    service,
    firstYear: net - investment,
    payback: net > 0 ? (12 * investment) / net : Number.NaN,
  }
}

export function compoundCase(graph: Graph, synergy: Synergy) {
  const members = synergy.hypothesisIds.map((id) => graph.byId.get(id)).filter((node): node is GraphNode => Boolean(node))
  const cases = members.map((node) => ({ node, numbers: modelCase(node) }))
  const standaloneGross = cases.reduce((sum, item) => sum + (item.numbers?.gross ?? 0), 0)
  const implementation = cases.reduce((sum, item) => sum + (item.numbers?.investment ?? 0), 0)
  const service = cases.reduce((sum, item) => sum + (item.numbers?.service ?? 0), 0)
  const overlap = standaloneGross * synergy.overlapPct / 100
  const sharedSaving = implementation * synergy.sharedImplementationPct / 100
  const combinedGross = standaloneGross - overlap
  const combinedImplementation = implementation - sharedSaving
  const combinedNet = combinedGross - service
  return {
    members,
    cases,
    standaloneGross,
    overlap,
    combinedGross,
    implementation,
    sharedSaving,
    combinedImplementation,
    service,
    combinedNet,
    payback: combinedNet > 0 ? (12 * combinedImplementation) / combinedNet : Number.NaN,
  }
}

export function sharedEnablers(graph: Graph, hypothesisIds: string[]) {
  const counts = new Map<string, number>()
  for (const id of hypothesisIds) {
    const reach = hypothesisReach(graph, id)
    const ids = new Set(
      [...reach.signals, ...reach.sources, ...reach.capabilities, ...reach.partners, ...reach.functions, ...reach.personas].map((node) => node.id),
    )
    ids.forEach((nodeId) => counts.set(nodeId, (counts.get(nodeId) ?? 0) + 1))
  }
  return [...counts.entries()]
    .filter(([, count]) => count >= 2)
    .map(([id, count]) => ({ node: graph.byId.get(id), count }))
    .filter((item): item is { node: GraphNode; count: number } => Boolean(item.node))
    .sort((a, b) => TYPE_ORDER.indexOf(a.node.type as never) - TYPE_ORDER.indexOf(b.node.type as never))
}
