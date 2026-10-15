export type ModeId = 'story' | 'twin' | 'live' | 'network' | 'evidence' | 'studio'
export type LensId = 'customer' | 'partner' | 'cisco'

export interface NavItem {
  id: string
  label: string
  icon: string
}

export interface Navigation {
  product: string
  modes: NavItem[]
  lenses: NavItem[]
}

export interface PackSummary {
  id: string
  name: string
  industry: string
  accent: string
  status: string
}

export interface GraphNode {
  id: string
  type: string
  title: string
  summary: string
  icon: string
  evidenceStatus: string
  confidence?: string
  financialModel?: {
    annualPoolGBP?: number
    opportunityPct?: number
    captureFactor?: number
    implementationGBP?: number
    serviceAnnualGBP?: number
    currency?: string
  }
  dataClassification?: string
}

export interface GraphEdge {
  from: string
  to: string
  relation: string
  rationale?: string
}

export interface StoryScene {
  id: string
  title: string
  eyebrow: string
  headline: string
  explanation: string
  visual: string
  focusNodeIds: string[]
  keyPoints: string[]
  presenterNotes: string
  transition: string
  lensTalkingPoints: Record<string, string>
}

export interface DesignPack {
  packId: string
  name: string
  industry: string
  subtitle: string
  status: string
  provenance?: { disclaimer?: string }
  theme: { accent: string }
  navigation: NavItem[]
  lenses: Record<string, { label: string; icon: string; description: string }>
  nodes: GraphNode[]
  edges: GraphEdge[]
  story: StoryScene[]
  tracks: { id: string; label: string; nodeIds: string[] }[]
  scene: { hotspots: { nodeId: string; x: number; y: number }[] }
  validation?: { missingData?: string[]; stage?: string }
  evidenceRegister?: { id: string; nodeId: string; status: string; dataOwner: string; validationAction: string }[]
  customer?: { name?: string; scope?: string }
}

export interface Scenario {
  title: string
  subtitle?: string
  status: string
  valueIntent: {
    objective: string
    accountableOwner: string
    metric: string
    baseline: string
    target: string
    benefitHypothesis: string
    riskBoundary: string
    approvalAuthority: string
    valueStatus: string
  }
  signalSnapshot: { source: string; name: string; value: string; quality: string }[]
  partnerRole?: string
  ciscoRole?: string
  workflow: { id: string; name: string; agent: string; description: string; detail?: string }[]
  controls: { allowPhysicalControl: boolean; requireHumanApproval: boolean; allowedActions?: string[] }
  provenance?: { verified?: boolean; sources?: string }
  connectors?: string[]
}

export interface Intent {
  schemaVersion: string
  packId: string
  intentVersion: string
  intentHash: string
  status: string
  valueIntent: {
    owner: string
    metric: string
    baselineText: string
    targetText: string
    hypothesis: string
    valueStatus: string
    objective: string
    primaryRefIds: string[]
    boardObjectives: { id: string; name: string }[]
    approvalAuthority: string
    riskBoundary: string
  }
  evidence: {
    provenance: string
    evidenceStatus: string
    confounders: string[]
    verification: string
    snapshots: { source: string; name: string; value: string; quality: string }[]
  }
  governance: {
    mode: string
    allowedActions: string[]
    deniedActions: string[]
    externalSystemsEnabled: boolean
    approval: { required: boolean; role: string }
    riskBoundary: string
  }
  commercial: {
    customer: { objective: string; hypothesis: string; status: string }
    partner: { role?: string; status: string }
    cisco: { capabilityPositioning?: string; status: string }
    separation: string
  }
  runtime: { outcomeState: string }
  presentation: { title: string; subtitle?: string; industry?: string }
  agentPlan: { agents: { id: string; title: string; authority: string; purpose: string }[]; flow: string[] }
}

export interface AgentInfo {
  id: string
  title: string
  authority: string
  purpose: string
  hosting: string
  placement: string
}

export interface PackDetail {
  design: DesignPack
  scenario: Scenario
  intent: Intent
  validation: { ok: boolean; errors: string[] }
  lineage: { design: string; scenario: string; legacyManifest: string; modules: string[] }
  network: AgentInfo[]
  imageUrl: string
  legacy: { apiVersion?: string; sha256?: string; outcomeState: string; externalSystemsEnabled: boolean }
}

export interface TraceEvent {
  seq: number
  eventId: string
  runId: string
  traceId: string
  correlationId: string
  packId: string
  intentVersion: string
  intentHash: string
  agent: string
  stage: string
  type: string
  message: string
  details: Record<string, unknown>
  graphRefs: string[]
  evidenceStatus: string
  actor: string
  timestamp: string
}

export interface RunRecord {
  id: string
  pack: string
  state: string
  approval: string | null
  intentHash: string
  planHash: string | null
  traceId: string
  correlationId: string
  intentVersion: string
  expiresAt: string | null
  orchestrator: string
  transport: string
  actor: string | null
  rationale: string | null
  actionKey: string | null
  actionConsumed: boolean
  auto: boolean
  ticket: {
    ticketType: string
    status: string
    summary: string
    externalSystemWritten: boolean
    idempotencyKey: string
  } | null
}

export interface PublicRun {
  run: RunRecord
  events: TraceEvent[]
}

export interface Interop {
  a2a: { configuredUrl: string; reachable: boolean; protocol: string; scope: string }
  agntcyDirectory: { enabled: boolean; status: string; reason: string }
  slim: { enabled: boolean; status: string; reason: string }
}
