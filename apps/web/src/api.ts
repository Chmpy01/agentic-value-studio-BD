import type {
  DiscoveryDocument,
  DiscoveryInput,
  DiscoveryStageAgent,
  Interop,
  Navigation,
  PackDetail,
  PackSummary,
  PublicRun,
} from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      ...(init?.body ? { 'content-type': 'application/json' } : {}),
      ...init?.headers,
    },
  })
  if (!response.ok) {
    let message = response.statusText
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') message = body.detail
      else if (body.detail) message = JSON.stringify(body.detail)
    } catch {
      /* keep status text */
    }
    throw new Error(message)
  }
  return (await response.json()) as T
}

export const api = {
  navigation: () => request<Navigation>('/api/navigation'),
  packs: () => request<PackSummary[]>('/api/packs'),
  pack: (id: string) => request<PackDetail>(`/api/packs/${id}`),
  interop: () => request<Interop>('/api/interop'),
  createRun: (body: {
    pack: string
    orchestrator: string
    transport: string
    auto: boolean
  }) => request<PublicRun>('/api/runs', { method: 'POST', body: JSON.stringify(body) }),
  run: (id: string) => request<PublicRun>(`/api/runs/${id}`),
  step: (id: string) => request<PublicRun>(`/api/runs/${id}/step`, { method: 'POST' }),
  pause: (id: string) => request<PublicRun>(`/api/runs/${id}/pause`, { method: 'POST' }),
  approve: (
    id: string,
    body: { decision: string; actor: string; intentHash: string; planHash: string; rationale: string },
  ) => request<PublicRun>(`/api/runs/${id}/approval`, { method: 'POST', body: JSON.stringify(body) }),
  discoveryAgents: () => request<DiscoveryStageAgent[]>('/api/discovery/agents'),
  createDiscovery: (body: DiscoveryInput) =>
    request<PublicRun>('/api/discovery/runs', { method: 'POST', body: JSON.stringify(body) }),
  discoveryRun: (id: string) => request<PublicRun>(`/api/discovery/runs/${id}`),
  discoveryStep: (id: string) => request<PublicRun>(`/api/discovery/runs/${id}/step`, { method: 'POST' }),
  discoveryPause: (id: string) => request<PublicRun>(`/api/discovery/runs/${id}/pause`, { method: 'POST' }),
  discoveryPack: (id: string) => request<DiscoveryDocument>(`/api/discovery/runs/${id}/pack`),
  validate: (document: unknown) =>
    request<{ ok: boolean; errors: string[]; kind?: string }>('/api/studio/validate', {
      method: 'POST',
      body: JSON.stringify(document),
    }),
}
