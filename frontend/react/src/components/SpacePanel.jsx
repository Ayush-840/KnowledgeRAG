import { useEffect, useMemo, useState } from 'react'
import VectorSpaceView from './VectorSpaceView'
import Space2D from './Space2D'

/**
 * Vector Space Explorer panel. Renders the UMAP chunk projection in 3D
 * (React Three Fiber) on capable devices; on low-end hardware
 * (hardwareConcurrency <= 4) it falls back to a static 2D SVG scatter of the
 * same coordinates. prefers-reduced-motion disables idle auto-rotation.
 * Keyboard: focus the canvas, arrow keys cycle the selection, Enter opens the
 * chunk's detail panel.
 */
export default function SpacePanel({ points, method, clustered, pointCount, query, promotedIds, retrievedIds, error, onSelectPoint, onClose }) {
  const [selIndex, setSelIndex] = useState(0)
  const reducedMotion = useMemo(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    [],
  )
  const lowEnd = useMemo(() => (navigator.hardwareConcurrency || 8) <= 4, [])

  useEffect(() => {
    setSelIndex(0)
  }, [points])

  const selected = points.length ? points[selIndex % points.length] : null

  const onKeyDown = (e) => {
    if (!points.length) return
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault()
      setSelIndex((i) => (i + 1) % points.length)
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault()
      setSelIndex((i) => (i - 1 + points.length) % points.length)
    } else if (e.key === 'Enter' && selected) {
      e.preventDefault()
      onSelectPoint(selected.id)
    }
  }

  const projection = method === 'umap' ? 'UMAP' : method === 'pca' ? 'PCA fallback' : 'projection'

  return (
    <div className="space-panel" role="dialog" aria-label="Vector space explorer">
      <header className="space-panel-header">
        <div className="space-panel-title">
          <strong>Vector space</strong>
          <span className="space-panel-meta">
            {projection} ·{' '}
            {clustered
              ? `${points.length} clusters of ${pointCount} chunks`
              : `${points.length} chunks`}
          </span>
        </div>
        <button className="drawer-close" onClick={onClose} aria-label="Close vector space">
          ✕
        </button>
      </header>

      <div
        className="space-canvas-wrap"
        tabIndex={0}
        onKeyDown={onKeyDown}
        aria-label="Vector space: arrow keys select a chunk, Enter opens it"
      >
        {error ? (
          <p className="space-error">{error}</p>
        ) : !points.length ? (
          <p className="space-empty">No chunks to plot — upload a document first.</p>
        ) : lowEnd ? (
          <Space2D
            points={points}
            query={query}
            promotedIds={promotedIds}
            selectedId={selected?.id}
            onSelectPoint={onSelectPoint}
          />
        ) : (
          <VectorSpaceView
            points={points}
            query={query}
            promotedIds={promotedIds}
            retrievedIds={retrievedIds}
            selected={selected}
            reducedMotion={reducedMotion}
            onSelectPoint={onSelectPoint}
          />
        )}
      </div>

      <footer className="space-panel-footer">
        {query
          ? 'Cyan tetrahedron = your query · lines link the reranked chunks fed to the LLM'
          : 'Ask a question in chat — the query drops into this map live.'}
        {!lowEnd && ' · drag to orbit, scroll to zoom'}
      </footer>
    </div>
  )
}
