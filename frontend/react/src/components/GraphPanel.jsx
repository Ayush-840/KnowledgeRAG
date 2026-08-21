import { useEffect, useMemo, useRef, useState, useCallback } from 'react'

const ENTITY_COLORS = {
  PROPER_NOUN: '#6366f1',
  MONETARY: '#22c55e',
  DATE: '#f59e0b',
  PERCENTAGE: '#ef4444',
  TECHNICAL_ID: '#06b6d4',
  REGULATION: '#a855f7',
  EMAIL: '#ec4899',
  URL: '#14b8a6',
  PHONE: '#f97316',
  VERSION: '#8b5cf6',
  DURATION: '#64748b',
  QUOTED: '#6b7280',
  ABBREVIATION: '#78716c',
  SECTION_REF: '#d946ef',
  ARTICLE_REF: '#e879f9',
}

function getColor(type) {
  return ENTITY_COLORS[type] || '#94a3b8'
}

/**
 * Knowledge Graph panel — force-directed layout rendered with SVG.
 * Nodes are colored by entity type, edges show co-occurrence weight.
 */
export default function GraphPanel({ nodes = [], edges = [], stats, queryEntities = [], onClose }) {
  const svgRef = useRef(null)
  const [positions, setPositions] = useState({})
  const [hoveredNode, setHoveredNode] = useState(null)
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 })

  // Initialize positions in a circle layout, then run force simulation
  useEffect(() => {
    if (!nodes.length) return
    const w = dimensions.width
    const h = dimensions.height
    const cx = w / 2
    const cy = h / 2
    const r = Math.min(w, h) * 0.35

    const pos = {}
    nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / nodes.length
      pos[node.id] = {
        x: cx + r * Math.cos(angle),
        y: cy + r * Math.sin(angle),
        vx: 0,
        vy: 0,
      }
    })
    setPositions(pos)

    // Simple force-directed simulation
    const nodeMap = {}
    nodes.forEach(n => { nodeMap[n.id] = n })

    let iter = 0
    const maxIter = 120
    const tick = () => {
      if (iter++ > maxIter) return
      setPositions(prev => {
        const next = { ...prev }
        const alpha = 1 - iter / maxIter

        // Repulsion between all node pairs
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const a = next[nodes[i].id]
            const b = next[nodes[j].id]
            if (!a || !b) continue
            let dx = b.x - a.x
            let dy = b.y - a.y
            let dist = Math.sqrt(dx * dx + dy * dy) || 1
            let force = (200 * 200) / dist
            let fx = (dx / dist) * force * alpha
            let fy = (dy / dist) * force * alpha
            a.vx -= fx
            a.vy -= fy
            b.vx += fx
            b.vy += fy
          }
        }

        // Attraction along edges
        edges.forEach(e => {
          const a = next[e.source]
          const b = next[e.target]
          if (!a || !b) return
          let dx = b.x - a.x
          let dy = b.y - a.y
          let dist = Math.sqrt(dx * dx + dy * dy) || 1
          let force = (dist - 80) * 0.01 * alpha
          let fx = (dx / dist) * force
          let fy = (dy / dist) * force
          a.vx += fx
          a.vy += fy
          b.vx -= fx
          b.vy -= fy
        })

        // Center gravity
        nodes.forEach(n => {
          const p = next[n.id]
          if (!p) return
          p.vx += (cx - p.x) * 0.002 * alpha
          p.vy += (cy - p.y) * 0.002 * alpha
        })

        // Apply velocity with damping
        nodes.forEach(n => {
          const p = next[n.id]
          if (!p) return
          p.vx *= 0.85
          p.vy *= 0.85
          p.x += p.vx
          p.y += p.vy
          // Keep within bounds
          p.x = Math.max(40, Math.min(w - 40, p.x))
          p.y = Math.max(40, Math.min(h - 40, p.y))
        })

        return next
      })
      requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [nodes, edges, dimensions])

  // Resize observer
  useEffect(() => {
    const el = svgRef.current?.parentElement
    if (!el) return
    const ro = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      if (width > 0 && height > 0) setDimensions({ width, height })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const nodeMap = useMemo(() => {
    const map = {}
    nodes.forEach(n => { map[n.id] = n })
    return map
  }, [nodes])

  const isQueryEntity = useCallback(
    (nodeId) => queryEntities.some(q => q.toLowerCase() === (nodeMap[nodeId]?.label || '').toLowerCase()),
    [queryEntities, nodeMap],
  )

  if (!nodes.length) {
    return (
      <div className="graph-panel">
        <header className="space-panel-header">
          <strong>Knowledge Graph</strong>
          <button className="space-panel-close" onClick={onClose} aria-label="Close">×</button>
        </header>
        <div className="graph-empty">No entities found. Ingest documents to build the knowledge graph.</div>
      </div>
    )
  }

  return (
    <div className="graph-panel">
      <header className="space-panel-header">
        <div className="space-panel-title">
          <strong>Knowledge Graph</strong>
          <span className="space-panel-meta">
            {stats?.total_nodes || nodes.length} entities · {stats?.total_edges || edges.length} relationships
          </span>
        </div>
        <button className="space-panel-close" onClick={onClose} aria-label="Close">×</button>
      </header>

      {/* Entity type legend */}
      <div className="graph-legend">
        {Object.entries(stats?.entity_type_counts || {}).slice(0, 8).map(([type, count]) => (
          <span key={type} className="graph-legend-item" style={{ borderLeftColor: getColor(type) }}>
            {type.replace('_', ' ')} ({count})
          </span>
        ))}
      </div>

      <div className="graph-canvas" style={{ width: '100%', height: 400 }}>
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
          style={{ background: '#0f172a', borderRadius: 8 }}
        >
          {/* Edges */}
          {edges.map((e, i) => {
            const a = positions[e.source]
            const b = positions[e.target]
            if (!a || !b) return null
            const isHighlighted = hoveredNode === e.source || hoveredNode === e.target
            return (
              <line
                key={i}
                x1={a.x} y1={a.y}
                x2={b.x} y2={b.y}
                stroke={isHighlighted ? '#60a5fa' : '#334155'}
                strokeWidth={isHighlighted ? 2 : 1}
                strokeOpacity={isHighlighted ? 0.9 : 0.4}
              />
            )
          })}

          {/* Nodes */}
          {nodes.map(node => {
            const pos = positions[node.id]
            if (!pos) return null
            const color = getColor(node.entity_type)
            const isQuery = isQueryEntity(node.id)
            const isHovered = hoveredNode === node.id
            const r = isHovered ? 10 : isQuery ? 8 : 6

            return (
              <g key={node.id}>
                {isQuery && (
                  <circle cx={pos.x} cy={pos.y} r={r + 6} fill={color} opacity={0.2} />
                )}
                <circle
                  cx={pos.x} cy={pos.y} r={r}
                  fill={color}
                  stroke={isHovered ? '#fff' : 'transparent'}
                  strokeWidth={2}
                  style={{ cursor: 'pointer', transition: 'r 0.15s' }}
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                />
                {(isHovered || isQuery) && (
                  <text
                    x={pos.x} y={pos.y - r - 6}
                    textAnchor="middle"
                    fill="#e2e8f0"
                    fontSize={11}
                    fontWeight={isQuery ? 700 : 400}
                  >
                    {node.label.length > 30 ? node.label.slice(0, 28) + '…' : node.label}
                  </text>
                )}
              </g>
            )
          })}
        </svg>
      </div>

      {/* Stats footer */}
      {stats && (
        <div className="graph-stats">
          <span>{stats.subgraph_nodes} visible / {stats.total_nodes} total entities</span>
          <span>{stats.subgraph_edges} / {stats.total_edges} relationships</span>
        </div>
      )}
    </div>
  )
}
