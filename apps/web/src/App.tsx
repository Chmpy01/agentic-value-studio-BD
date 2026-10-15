import { useCallback, useEffect, useMemo, useState } from 'react'
import { Boxes, Layers, Moon, Sun } from 'lucide-react'
import { api } from './api'
import { CompoundView } from './compound'
import { EconomicsView, EvidenceRiskView, ExplorerView, NewCustomerView, SignalsView } from './design'
import { buildGraph } from './graph'
import { ValueGraphView } from './graphview'
import { Icon } from './icons'
import { ReasoningView } from './reasoning'
import type { LensId, ModeId, Navigation, PackDetail, PackSummary, PublicRun } from './types'
import { EvidenceView, LiveView, NetworkView, StoryView, StudioView } from './views'

export default function App() {
  const [nav, setNav] = useState<Navigation | null>(null)
  const [packs, setPacks] = useState<PackSummary[]>([])
  const [packId, setPackId] = useState('office')
  const [pack, setPack] = useState<PackDetail | null>(null)
  const [mode, setMode] = useState<ModeId>('story')
  const [lens, setLens] = useState<LensId>('customer')
  const [scene, setScene] = useState(0)
  const [notes, setNotes] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [run, setRun] = useState<PublicRun | null>(null)
  const [orchestrator, setOrchestrator] = useState('deterministic')
  const [transport, setTransport] = useState('local')
  const [error, setError] = useState('')
  const [bootError, setBootError] = useState('')
  const [busy, setBusy] = useState(false)
  const [selected, setSelected] = useState('b1')
  const [synergyId, setSynergyId] = useState('')

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  useEffect(() => {
    Promise.all([api.navigation(), api.packs()])
      .then(([navigation, list]) => {
        setNav(navigation)
        setPacks(list)
      })
      .catch((reason: Error) => setBootError(reason.message))
  }, [])

  useEffect(() => {
    setRun(null)
    setScene(0)
    setError('')
    setSelected('b1')
    setSynergyId('')
    api.pack(packId).then(setPack).catch((reason: Error) => setBootError(reason.message))
  }, [packId])

  useEffect(() => {
    if (pack) document.documentElement.style.setProperty('--accent', pack.design.theme.accent)
  }, [pack])

  const graph = useMemo(() => (pack ? buildGraph(pack) : null), [pack])

  const runId = run?.run.id
  useEffect(() => {
    if (!runId) return
    let stop = false
    const refresh = () => {
      api.run(runId).then((data) => {
        if (!stop) setRun(data)
      }).catch(() => undefined)
    }
    refresh()
    const source = new EventSource(`/api/runs/${runId}/stream`)
    source.onmessage = () => refresh()
    source.addEventListener('done', () => refresh())
    return () => {
      stop = true
      source.close()
    }
  }, [runId])

  const chooseScene = useCallback((value: number) => setScene(value), [])
  const pickToExplorer = useCallback((id: string) => {
    setSelected(id)
    setMode('explore')
  }, [])

  async function startRun(auto: boolean) {
    setBusy(true)
    setError('')
    try {
      const created = await api.createRun({ pack: packId, orchestrator, transport, auto })
      setRun(created)
      setMode('live')
      return created
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Run failed')
      return null
    } finally {
      setBusy(false)
    }
  }

  async function onStep() {
    setError('')
    try {
      const current = run ?? (await startRun(false))
      if (!current || current.run.orchestrator === 'langgraph') return
      setRun(await api.step(current.run.id))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Step failed')
    }
  }

  async function onDecide(decision: 'approved' | 'rejected', actor: string, rationale: string) {
    if (!run?.run.planHash) return
    setError('')
    try {
      setRun(
        await api.approve(run.run.id, {
          decision,
          actor,
          rationale,
          intentHash: run.run.intentHash,
          planHash: run.run.planHash,
        }),
      )
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Approval failed')
    }
  }

  if (bootError) {
    return (
      <main className="boot">
        <h1>Studio API is not reachable</h1>
        <p>{bootError}</p>
        <p>Start it with <code>python apps/api/main.py</code> from the repository root, then refresh.</p>
      </main>
    )
  }
  if (!nav || !pack || !graph) {
    return (
      <main className="boot">
        <p>Loading value packs…</p>
      </main>
    )
  }

  const activeGroup = nav.groups.find((group) => group.modes.some((item) => item.id === mode)) || nav.groups[0]
  return (
    <div className="app">
      <a className="skip" href="#workspace">Skip to content</a>
      <header className="top">
        <div className="brand">
          <span className="mark" aria-hidden="true">
            <Boxes size={22} strokeWidth={1.75} />
          </span>
          <div>
            <h1>Cognitive Value Studio</h1>
            <p>Connected intelligence → measurable value</p>
          </div>
        </div>
        <div className="top-actions">
          <label className="select-wrap">
            <Layers size={16} strokeWidth={1.75} aria-hidden="true" />
            <span>
              <span className="tiny">Loaded knowledge pack</span>
              <select value={packId} aria-label="Industry pack" onChange={(event) => setPackId(event.target.value)}>
                {packs.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </span>
          </label>
          <button type="button" className="ui-btn" aria-label="Toggle colour theme" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
            {theme === 'light' ? <Moon size={15} /> : <Sun size={15} />}
            Theme
          </button>
        </div>
      </header>
      <div className="shell">
        <div className="toprow">
          <div className="group-switch" role="tablist" aria-label="Studio area">
            {nav.groups.map((group) => (
              <button
                key={group.id}
                type="button"
                role="tab"
                aria-selected={group.id === activeGroup.id}
                className={group.id === activeGroup.id ? 'active' : ''}
                onClick={() => group.id !== activeGroup.id && setMode(group.modes[0].id as ModeId)}
              >
                <Icon name={group.icon} size={15} />
                {group.label}
              </button>
            ))}
          </div>
          <div className="lens" role="group" aria-label="Economic lens">
            {nav.lenses.map((item) => (
              <button
                key={item.id}
                type="button"
                className={lens === item.id ? 'active' : ''}
                aria-pressed={lens === item.id}
                onClick={() => setLens(item.id as LensId)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
        <nav className="nav" aria-label={`${activeGroup.label} views`}>
          {activeGroup.modes.map((item) => (
            <button
              key={item.id}
              type="button"
              className={mode === item.id ? 'active' : ''}
              aria-current={mode === item.id ? 'page' : undefined}
              onClick={() => setMode(item.id as ModeId)}
            >
              <Icon name={item.icon} size={16} />
              {item.label}
            </button>
          ))}
        </nav>
        <div className="microbar">
          <p>
            <span className="industry">{pack.design.industry}</span>
            <span className="desc"> · {pack.design.subtitle}</span>
          </p>
          <div className="meta">
            <span className="pill synthetic">Synthetic demonstration</span>
            <span className="pill">{graph.nodes.length} knowledge nodes · {graph.edges.length} links</span>
          </div>
        </div>
        <main id="workspace" key={`${packId}-${mode}`} className="view-enter">
          {mode === 'story' && (
            <StoryView pack={pack} lens={lens} index={scene} setIndex={chooseScene} notes={notes} setNotes={setNotes} />
          )}
          {mode === 'signals' && <SignalsView pack={pack} graph={graph} lens={lens} onPick={pickToExplorer} onNavigate={setMode} />}
          {mode === 'explore' && <ExplorerView pack={pack} graph={graph} selected={selected} onSelect={setSelected} />}
          {mode === 'graph' && <ValueGraphView pack={pack} graph={graph} lens={lens} selected={selected} onSelect={setSelected} />}
          {mode === 'compound' && (
            <CompoundView pack={pack} graph={graph} lens={lens} synergyId={synergyId} setSynergyId={setSynergyId} onPick={pickToExplorer} />
          )}
          {mode === 'risk' && <EvidenceRiskView pack={pack} graph={graph} onPick={pickToExplorer} />}
          {mode === 'economics' && <EconomicsView graph={graph} lens={lens} />}
          {mode === 'new' && <NewCustomerView pack={pack} />}
          {mode === 'studio' && <StudioView pack={pack} />}
          {mode === 'reasoning' && (
            <ReasoningView
              pack={pack}
              graph={graph}
              lens={lens}
              onPick={pickToExplorer}
              onNavigate={setMode}
              onCompound={(id) => {
                setSynergyId(id)
                setMode('compound')
              }}
            />
          )}
          {mode === 'live' && (
            <LiveView
              pack={pack}
              run={run}
              busy={busy}
              error={error}
              orchestrator={orchestrator}
              setOrchestrator={setOrchestrator}
              transport={transport}
              setTransport={setTransport}
              onRun={() => void startRun(true)}
              onPause={() => run && api.pause(run.run.id).then(setRun).catch((reason: Error) => setError(reason.message))}
              onStep={() => void onStep()}
              onDecide={onDecide}
            />
          )}
          {mode === 'network' && <NetworkView pack={pack} run={run} />}
          {mode === 'evidence' && <EvidenceView pack={pack} lens={lens} run={run} />}
        </main>
      </div>
    </div>
  )
}
