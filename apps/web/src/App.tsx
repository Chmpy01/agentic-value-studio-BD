import { useCallback, useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { api } from './api'
import { Icon } from './icons'
import type { LensId, ModeId, Navigation, PackDetail, PackSummary, PublicRun } from './types'
import { EvidenceView, LiveView, NetworkView, StoryView, StudioView, TwinView } from './views'

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
    api.pack(packId).then(setPack).catch((reason: Error) => setBootError(reason.message))
  }, [packId])

  useEffect(() => {
    if (pack) document.documentElement.style.setProperty('--accent', pack.design.theme.accent)
  }, [pack])

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
  if (!nav || !pack) {
    return (
      <main className="boot">
        <p>Loading value packs…</p>
      </main>
    )
  }

  return (
    <>
      <a className="skip" href="#workspace">Skip to content</a>
      <header className="topbar">
        <div className="brand-row">
          <div className="brand">
            <span className="mark" aria-hidden="true" />
            <div>
              <strong>{nav.product}</strong>
              <small>{pack.design.customer?.scope || 'Synthetic reference'}</small>
            </div>
          </div>
          <label className="select">
            <span>Industry pack</span>
            <select
              value={packId}
              aria-label="Industry pack"
              onChange={(event) => setPackId(event.target.value)}
            >
              {packs.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <div className="lenses" role="group" aria-label="Economic lens">
            {nav.lenses.map((item) => (
              <button
                key={item.id}
                type="button"
                className={lens === item.id ? 'on' : ''}
                onClick={() => setLens(item.id as LensId)}
              >
                <Icon name={item.icon} size={15} />
                {item.label}
              </button>
            ))}
          </div>
          <span className="badge">Synthetic · no live control</span>
          <button type="button" className="icon-button" aria-label="Toggle colour theme" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>
        </div>
        <nav className="modes" aria-label="Studio modes">
          {nav.modes.map((item) => (
            <button key={item.id} type="button" className={mode === item.id ? 'on' : ''} onClick={() => setMode(item.id as ModeId)}>
              <Icon name={item.icon} size={16} />
              {item.label}
            </button>
          ))}
        </nav>
      </header>
      <main id="workspace">
        {mode === 'story' && (
          <StoryView pack={pack} lens={lens} index={scene} setIndex={chooseScene} notes={notes} setNotes={setNotes} />
        )}
        {mode === 'twin' && <TwinView pack={pack} lens={lens} />}
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
        {mode === 'studio' && <StudioView pack={pack} />}
      </main>
    </>
  )
}
