import { useMemo } from 'react'
import { docColor } from '../utils/docColors'

/**
 * Low-end fallback for the vector space view: the same UMAP coordinates, just
 * dropping the z-axis, rendered as a static SVG scatter — no WebGL, no camera,
 * no animation. Same colors, same promoted/retrieved/receded emphasis, same
 * click-to-open behavior.
 */
export default function Space2D({ points, query, promotedIds, selectedId, onSelectPoint }) {
  const promoted = useMemo(() => new Set(promotedIds || []), [promotedIds])

  // Fit coordinates into the viewBox with padding
  const view = useMemo(() => {
    if (!points.length) return null
    const xs = points.map((p) => p.x)
    const ys = points.map((p) => p.y)
    const all = [...xs, ...ys, query ? query.x : 0, query ? query.y : 0]
    const min = Math.min(...all)
    const max = Math.max(...all)
    const span = max - min || 1
    const scale = (v) => 25 + ((v - min) / span) * 950
    return { sx: (v) => scale(v), sy: (v) => 975 - scale(v) } // flip y for screen coords
  }, [points, query])

  if (!view) return <p className="space-empty">No chunks to plot.</p>

  return (
    <svg className="space-2d" viewBox="0 0 1000 1000" role="group" aria-label="Vector space scatter plot">
      {points.map((p) => {
        const isPromoted = promoted.has(p.id)
        const isSelected = p.id === selectedId
        return (
          <circle
            key={p.id}
            cx={view.sx(p.x)}
            cy={view.sy(p.y)}
            r={isPromoted ? 14 : 7}
            fill={docColor(p.filename)}
            opacity={isPromoted || isSelected ? 1 : 0.45}
            stroke={isSelected ? '#ffffff' : isPromoted ? '#22d3ee' : 'none'}
            strokeWidth={2}
            role="button"
            tabIndex={0}
            aria-label={`Chunk from ${p.filename}`}
            onClick={() => onSelectPoint(p.id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') onSelectPoint(p.id)
            }}
            className="space-2d-point"
          />
        )
      })}
      {query && (
        <g transform={`translate(${view.sx(query.x)}, ${view.sy(query.y)})`} aria-label="Query">
          <polygon points="0,-18 14,0 0,18 -14,0" fill="#22d3ee" stroke="#0f172a" strokeWidth="1.5" />
        </g>
      )}
    </svg>
  )
}
