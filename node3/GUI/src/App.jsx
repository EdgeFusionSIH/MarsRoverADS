import { useState, useEffect, useRef } from 'react'
import './App.css'

/* ═══════════════════════════════════════════
   SVG LINE GRAPH
   ═══════════════════════════════════════════ */
function LineGraph({ slipData, torqueData }) {
  const pad = { top: 14, right: 12, bottom: 22, left: 32 }
  const viewW = 400
  const viewH = 180
  const w = viewW - pad.left - pad.right
  const h = viewH - pad.top - pad.bottom

  const slipMax = 60
  const torqueMax = 10
  const points = Math.max(slipData.length, torqueData.length)

  const toPath = (data, max) => {
    if (data.length < 2) return { line: '', area: '', dots: [] }
    const step = w / (data.length - 1)
    const pts = data.map((v, i) => ({
      x: pad.left + i * step,
      y: pad.top + h - (Math.min(v, max) / max) * h
    }))
    const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
    const area = line + ` L${pts[pts.length - 1].x},${pad.top + h} L${pts[0].x},${pad.top + h} Z`
    return { line, area, dots: pts }
  }

  const slip = toPath(slipData, slipMax)
  const torque = toPath(torqueData, torqueMax)

  // Grid lines (4 horizontal)
  const gridLines = [0.25, 0.5, 0.75, 1].map(frac => pad.top + h * (1 - frac))

  return (
    <div className="graph-wrapper">
      <svg viewBox={`0 0 ${viewW} ${viewH}`} preserveAspectRatio="none">
        {/* Grid */}
        {gridLines.map((y, i) => (
          <line key={i} x1={pad.left} y1={y} x2={pad.left + w} y2={y} className="graph-grid-line" />
        ))}
        <line x1={pad.left} y1={pad.top} x2={pad.left} y2={pad.top + h} className="graph-grid-line" />
        <line x1={pad.left} y1={pad.top + h} x2={pad.left + w} y2={pad.top + h} className="graph-grid-line" />

        {/* Y-axis labels for slip */}
        <text x={pad.left - 4} y={pad.top + 3} textAnchor="end" className="graph-axis-label">{slipMax}%</text>
        <text x={pad.left - 4} y={pad.top + h * 0.5 + 3} textAnchor="end" className="graph-axis-label">{slipMax / 2}%</text>
        <text x={pad.left - 4} y={pad.top + h + 3} textAnchor="end" className="graph-axis-label">0</text>

        {/* X-axis labels */}
        {slipData.map((_, i) => (
          <text
            key={i}
            x={pad.left + (i * w) / Math.max(slipData.length - 1, 1)}
            y={pad.top + h + 14}
            textAnchor="middle"
            className="graph-axis-label"
          >
            t-{slipData.length - 1 - i}
          </text>
        ))}

        {/* Torque area fill */}
        <path d={torque.area} className="graph-area torque" />
        {/* Slip area fill */}
        <path d={slip.area} className="graph-area slip" />

        {/* Torque line */}
        <path d={torque.line} className="graph-line torque" />
        {/* Slip line */}
        <path d={slip.line} className="graph-line slip" />

        {/* Torque dots */}
        {torque.dots.map((p, i) => (
          <circle key={`t${i}`} cx={p.x} cy={p.y} r={2.5} className="graph-dot torque" />
        ))}
        {/* Slip dots */}
        {slip.dots.map((p, i) => (
          <circle key={`s${i}`} cx={p.x} cy={p.y} r={2.5} className="graph-dot slip" />
        ))}
      </svg>
    </div>
  )
}

/* ═══════════════════════════════════════════
   GAUGE
   ═══════════════════════════════════════════ */
function Gauge({ value, label, color, warning }) {
  const v = Math.min(100, Math.max(0, value))
  return (
    <div className="gauge-container">
      <div
        className={`gauge-ring${warning ? ' warning' : ''}`}
        style={{ background: `conic-gradient(${color} 0% ${v}%, rgba(255,255,255,0.04) ${v}% 100%)` }}
      >
        <span className="gauge-value">{v.toFixed(1)}%</span>
      </div>
      <span className="gauge-label">{label}</span>
    </div>
  )
}

/* ═══════════════════════════════════════════
   NODE HEALTH CARD (used inside Complexity Engine)
   ═══════════════════════════════════════════ */
function NodeHealthCard({ title, hw }) {
  return (
    <div className="node-health-card">
      <div className="node-health-title">{title}</div>
      <div className="gauges-grid-mini">
        <Gauge value={hw.cpu_percent || 0} label="CPU" color="var(--cyan)" />
        <Gauge value={hw.vram_percent || 0} label="VRAM" color="var(--emerald)" />
        <Gauge value={hw.ram_percent || 0} label="RAM" color="var(--amber)" />
        <Gauge value={hw.disk_percent || 0} label="DISK" color="var(--cyan-dim)" />
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════
   APP
   ═══════════════════════════════════════════ */
export default function App() {
  const [telemetry, setTelemetry] = useState(null)
  const [connected, setConnected] = useState(false)
  const [missionTime, setMissionTime] = useState('')
  const [imgSrc, setImgSrc] = useState('/last_frame.jpg')
  const [imgReady, setImgReady] = useState(false)
  const termRef = useRef(null)

  const [chaosStorm, setChaosStorm] = useState(false)
  const [chaosSand, setChaosSand] = useState(false)
  const [chaosUplink, setChaosUplink] = useState(false)

  /* Clock — 1s */
  useEffect(() => {
    const tick = () => {
      const utc = new Date().toISOString().slice(11, 19)
      setMissionTime(`SOL 847 // ${utc} UTC`)
    }
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])

  /* Write chaos state to output JSON via API */
  useEffect(() => {
    const writeChaos = async () => {
      try {
        await fetch('/api/chaos', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            duststorm: chaosStorm ? 1 : 0,
            sandtrap: chaosSand ? 1 : 0,
            earthuplink: chaosUplink ? 1 : 0
          })
        })
      } catch {
        // Backend might not support POST yet, chaos state still shown in UI
      }
    }
    writeChaos()
  }, [chaosStorm, chaosSand, chaosUplink])

  /* Telemetry — 100ms poll */
  useEffect(() => {
    let live = true, timer

    const poll = async () => {
      if (!live) return
      try {
        const r = await fetch('/telemetry.json?_=' + Date.now())
        if (!r.ok) throw new Error()
        const d = await r.json()

        // Chaos-driven data is now produced by node2's core engine
        // via the real CSV, so we just pass it through.
        // Only the earth uplink toggle still needs a client-side override
        // since it controls the documentation_engine sync status display.
        if (chaosUplink) {
          d.documentation_engine.sync_status = 'SYNCING TO EARTH'
        }

        setTelemetry(d)
        setConnected(true)
      } catch {
        setConnected(false)
      }
      if (live) timer = setTimeout(poll, 100)
    }

    poll()
    return () => { live = false; clearTimeout(timer) }
  }, [chaosUplink])

  /* Image preload — flicker-free */
  useEffect(() => {
    let live = true, timer
    const load = () => {
      if (!live) return
      const img = new Image()
      const url = '/last_frame.jpg?_=' + Date.now()
      img.onload = () => { if (live) { setImgSrc(url); setImgReady(true) } }
      img.src = url
      if (live) timer = setTimeout(load, 200)
    }
    load()
    return () => { live = false; clearTimeout(timer) }
  }, [])

  /* Terminal auto-scroll */
  useEffect(() => {
    if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight
  }, [telemetry?.documentation_engine?.logs])

  /* Derived */
  const hw = telemetry?.hardware || {}
  const kin = telemetry?.kinematics || {}
  const ce = telemetry?.complexity_engine || {}
  const cls = telemetry?.classifying_engine || {}
  const doc = telemetry?.documentation_engine || {}
  const logs = doc.logs || []

  const node1Hw = ce.node1_hardware || {}
  const node2Hw = ce.node2_hardware || {}

  const isCritical = cls.rover_command === 'HALT' || cls.rover_command === 'SAFE_MODE' || (cls.fusion_output || '').includes('CRITICAL')
  const syncOffline = (doc.sync_status || '').toUpperCase().includes('OFFLINE') || (doc.sync_status || '').toUpperCase().includes('BUFFER')

  return (
    <div className="dashboard">
      {/* ════ HEADER ════ */}
      <header className="header">
        <div className="header-brand">
          <h1>EDGEFUSE</h1>
          <span>Mars Rover Mission Control</span>
        </div>
        <div className="header-meta">
          <div className="mission-clock">{missionTime}</div>
          <div className="connection-status">
            <div className={`status-dot ${connected ? 'online' : 'offline'}`} />
            {connected ? 'LINKED' : 'NO SIGNAL'}
          </div>
        </div>
      </header>

      {/* ════ 6-PANEL GRID ════ */}
      <div className="grid-container">

        {/* 1. NavCam */}
        <div className="panel navcam-panel">
          <div className="panel-header">
            <span className="panel-title">NavCam Perception</span>
            <span className="panel-status">LIVE</span>
          </div>
          <div className="navcam-image-container">
            {imgReady
              ? <img className="navcam-image" src={imgSrc} alt="NavCam" />
              : <div className="navcam-image" style={{ background: 'linear-gradient(135deg, #0e141e, #1a2332)', width: '100%', height: '100%' }} />
            }
            <div className="scan-overlay" />
            <div className="navcam-overlay">
              <span className="overlay-model">{telemetry?.active_model || '—'}</span>
              <span className="overlay-latency">{telemetry ? `${telemetry.inference_latency_ms} ms` : '—'}</span>
            </div>
          </div>
        </div>

        {/* 2. Kinematic Telemetry */}
        <div className="panel kinematics-panel">
          <div className="panel-header">
            <span className="panel-title">Kinematic Telemetry</span>
            <span className="panel-status">SCROLLING</span>
          </div>
          <div className="panel-body">
            <div className="chart-container">
              <LineGraph
                slipData={kin.wheel_slip_history || []}
                torqueData={kin.motor_torque_history || []}
              />
              <div className="graph-legend">
                <div className="legend-item"><span className="legend-dot slip" /> Wheel Slip %</div>
                <div className="legend-item"><span className="legend-dot torque" /> Motor Torque Nm</div>
              </div>
              <div className="graph-current-values">
                <span className="current-val slip">SLIP: {kin.wheel_slip_percent?.toFixed(1) || '0'}%</span>
                <span className="current-val torque">TORQUE: {kin.motor_torque_nm?.toFixed(1) || '0'} Nm</span>
              </div>
            </div>
          </div>
        </div>

        {/* 3. Complexity Engine — Split into Node 1 & Node 2 */}
        <div className="panel complexity-panel">
          <div className="panel-header">
            <span className="panel-title">Complexity Engine</span>
            <span className="panel-status">NODE HEALTH</span>
          </div>
          <div className="panel-body">
            <div className="node-health-split">
              <NodeHealthCard title="NODE 1 — VISION" hw={node1Hw} />
              <NodeHealthCard title="NODE 2 — CONTROL" hw={node2Hw} />
            </div>
            <div className="scheduled-model">
              <div className="model-name">ACTIVE: {ce.scheduled_model || '—'}</div>
              <div className="model-reason">{ce.reason || ''}</div>
            </div>
          </div>
        </div>

        {/* 4. Fusion Brain */}
        <div className="panel fusion-panel">
          <div className="panel-header">
            <span className="panel-title">Fusion Brain</span>
            <span className="panel-status">MULTIMODAL</span>
          </div>
          <div className="panel-body">
            <div className="fusion-grid">
              <div className="fusion-item">
                <div className="fusion-label">Vision</div>
                <div className="fusion-value">{cls.vision_classification || '—'}</div>
              </div>
              <div className="fusion-item">
                <div className="fusion-label">Telemetry</div>
                <div className="fusion-value">{cls.telemetry_classification || '—'}</div>
              </div>
              <div className="fusion-item">
                <div className="fusion-label">Confidence</div>
                <div className="fusion-value">{cls.fusion_confidence ? (cls.fusion_confidence * 100).toFixed(0) + '%' : '—'}</div>
              </div>
              <div className="fusion-item">
                <div className="fusion-label">Output</div>
                <div className="fusion-value" style={{ fontSize: 10 }}>{cls.fusion_output || '—'}</div>
              </div>
            </div>

            {isCritical ? (
              <div className="fusion-alert critical">
                ⚠ {cls.fusion_output || 'CRITICAL'}
              </div>
            ) : (
              <div className="fusion-alert nominal">
                {cls.fusion_output || 'NOMINAL — No Fusion Conflict Detected'}
              </div>
            )}

            <div className={`fusion-command ${isCritical ? 'halt' : 'nominal'}`}>
              CMD: {cls.rover_command || 'NOMINAL'}
            </div>
          </div>
        </div>

        {/* 5. Flight Recorder */}
        <div className="panel docs-panel">
          <div className="panel-header">
            <span className="panel-title">Flight Recorder</span>
            <span className="panel-status">DELAY: {doc.earth_signal_delay_sec || 0}s</span>
          </div>
          <div className="panel-body">
            <div className="docs-header-bar">
              <span className={`sync-badge ${syncOffline ? 'offline' : 'online'}`}>
                ● {syncOffline ? 'BUFFERING OFFLINE' : 'SYNCING TO EARTH'}
              </span>
              <span className="signal-delay">
                {doc.earth_signal_delay_sec ? (doc.earth_signal_delay_sec / 60).toFixed(0) + ' min' : '—'}
              </span>
            </div>
            <div className="terminal" ref={termRef}>
              {logs.map((e, i) => (
                <div className="log-entry" key={i}>
                  <span className="log-time">{e.time}</span>
                  <span className={`log-level ${e.level.toLowerCase()}`}>[{e.level}]</span>
                  <span className="log-msg">{e.msg}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 6. Chaos Bench */}
        <div className="panel chaos-panel">
          <div className="panel-header">
            <span className="panel-title">Chaos Bench</span>
            <span className="panel-status">SIMULATION</span>
          </div>
          <div className="panel-body">
            <div className="chaos-buttons">
              <button className={`chaos-btn storm${chaosStorm ? ' active' : ''}`} onClick={() => setChaosStorm(s => !s)}>
                {chaosStorm ? '■ STOP DUST STORM' : '▶ SIMULATE DUST STORM'}
              </button>
              <button className={`chaos-btn sand${chaosSand ? ' active' : ''}`} onClick={() => setChaosSand(s => !s)}>
                {chaosSand ? '■ CLEAR SAND TRAP' : '▶ INJECT SAND TRAP'}
              </button>
              <button className={`chaos-btn uplink${chaosUplink ? ' active' : ''}`} onClick={() => setChaosUplink(s => !s)}>
                {chaosUplink ? '● EARTH UPLINK: ON' : '○ TOGGLE EARTH UPLINK'}
              </button>
            </div>
            <div className="chaos-status">
              STORM: {chaosStorm ? 'ACTIVE' : 'OFF'} // TRAP: {chaosSand ? 'INJECTED' : 'OFF'} // UPLINK: {chaosUplink ? 'SYNC' : 'BUFFER'}
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
