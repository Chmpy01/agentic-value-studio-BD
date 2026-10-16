export type ModeId = 'story' | 'discovery' | 'twin' | 'live' | 'network' | 'evidence' | 'studio'
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

export type DiscoveryLayerId =
  | 'industry_context'
  | 'industry_value_stream'
  | 'customer_value_stream'
  | 'function'
  | 'persona'

export interface DiscoveryLayer {
  id: DiscoveryLayerId
  label: string
  order: number
  description: string
}

export interface DiscoveryGraphNode {
  id: string
  layer: DiscoveryLayerId
  title: string
  summary: string
  evidence_type: string
  confidence: string
  validation_status: string
  source_refs: string[]
  validation_questions: string[]
  design_pack_refs: string[]
  detail: Record<string, unknown>
}

export interface DiscoveryEvidenceRow {
  id: string
  claim: string
  evidence_type: string
  confidence: string
  validation_status: string
  sensitivity: string
  source_refs: string[]
  applies_to: string[]
  validation_question: string | null
}

export interface DiscoverySourceNote {
  id: string
  name: string
  source_class: string
  reference: string
  reference_type: string
  content_status: string
  date_observed: string
  confidence: string
  sensitivity: string
  cited_in_graph: boolean
}

export interface DiscoveryGate {
  id: string
  question: string
  blocks: string[]
  owner_to_confirm: string
  status: string
  raised_by: string
}

export interface DiscoveryAiCase {
  id: string
  name: string
  value_stream_ref: string
  impact: string
  complexity: string
  confidence: string
  rai_risk: string
  rai_notes: string
  data_dependencies: string[]
  human_in_the_loop: string
  next_validation_action: string
}

export interface DiscoveryDocument {
  schemaVersion: string
  discoveryHash: string
  meta: {
    template_name: string
    template_version: string
    pack_id: string
    generated_by: string
    outcome_state: string
    external_research_calls: boolean
    disclaimer: string
    research_corpus: string
    source_register: string
  }
  customer: {
    name: string
    industry: string
    geography: string
    business_model: string
    account_stage: string
    input_provenance: string
    strategic_context: { signal: string; source_type: string; confidence: string; sensitivity?: string }[]
  }
  evidence_register: DiscoveryEvidenceRow[]
  company_insights: {
    industry_context: { name: string; definition: string; scope_notes: string }
    industry_pressures: { id: string; statement: string; evidence_type: string; confidence: string }[]
    known: string[]
    inferred: string[]
    unknown: string[]
    evidence_coverage: { counts: Record<string, number>; total: number; validatedShare: number }
  }
  knowledge_graph: {
    layers: DiscoveryLayer[]
    nodes: DiscoveryGraphNode[]
    edges: { from: string; to: string; relation: string; evidence_type?: string }[]
    counts: Record<string, number>
    note: string
  }
  value_twin_nodes: {
    node_id: string
    node_name: string
    business_function: string
    frictions: string[]
    capability_needs: string[]
    validation_questions: string[]
  }[]
  current_state: {
    maturity_stage: string
    operating_model_gaps: { gap: string; value_stream_ref: string; confidence: string }[]
    technical_model_gaps: { gap: string; value_stream_ref: string }[]
    organisational_model_gaps: { gap: string; function_ref: string }[]
    missing_data: string[]
  }
  outcomes: { id: string; outcome: string; kpi: string; stakeholders: string[]; status: string; note: string }[]
  portfolio_mapping: {
    gap: string
    capability_need: string
    portfolio_domain: string | null
    priority: string
    confidence: string
    status: string
  }[]
  partner_landscape: {
    id: string
    name: string
    role: string
    evidence_type: string
    confidence: string
    validation_question: string
    p360_guidance: string
  }[]
  role_insights: { role: string; focus: string; next_actions: string[] }[]
  ai_value_twin: DiscoveryAiCase[]
  validation_gates: DiscoveryGate[]
  roadmap: { step: number; action: string; depends_on: string[]; evidence_needed: string }[]
  source_notes: DiscoverySourceNote[]
}

export interface DiscoveryStageAgent {
  id: string
  title: string
  authority: string
  purpose: string
  evidenceStatus: string
}

export interface DiscoveryInput {
  pack: string
  customerName: string
  geography: string
  businessModel: string
  accountStage: string
  signals: { signal: string; sensitivity: string; confidence: string }[]
  auto: boolean
}

export interface Interop {
  a2a: { configuredUrl: string; reachable: boolean; protocol: string; scope: string }
  agntcyDirectory: { enabled: boolean; status: string; reason: string }
  slim: { enabled: boolean; status: string; reason: string }
}
