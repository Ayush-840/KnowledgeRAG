import { useEffect, useRef } from 'react'
import SentenceHighlight from './SentenceHighlight'

export default function SourceDrawer({ open, onClose, citations, query, focusMarker, onViewDocument }) {
  const refs = useRef({})
  useEffect(() => {
    if (open && focusMarker && refs.current[focusMarker]) {
      refs.current[focusMarker].scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [open, focusMarker])

  if (!open) return null

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <header className="drawer-header">
          <h3>Sources ({citations.length})</h3>
          <button className="drawer-close" onClick={onClose} aria-label="Close sources">
            ✕
          </button>
        </header>
        <div className="drawer-body">
          {citations.length === 0 && <p className="drawer-empty">No source chunks were cited.</p>}
          {citations.map((c) => (
            <article
              key={c.id}
              ref={(el) => (refs.current[c.marker] = el)}
              className={`source-card ${focusMarker === c.marker ? 'source-card-focused' : ''}`}
            >
              <header className="source-card-header">
                <span className="source-marker">[{c.marker}]</span>
                <span className="source-filename">{c.filename}</span>
                <span className="source-page">page {c.page_number}</span>
                {c.confidence != null && (
                  <span className="source-confidence">{(c.confidence * 100).toFixed(1)}%</span>
                )}
              </header>
              <div className="source-scores">
                <span title="Dense cosine similarity">dense {fmt(c.scores?.dense_similarity)}</span>
                <span title="Raw BM25 score">bm25 {fmt(c.scores?.bm25)}</span>
                <span title="RRF fusion score">rrf {fmt(c.scores?.rrf)}</span>
                <span title="Cross-encoder relevance">rerank {fmt(c.scores?.rerank)}</span>
              </div>
              <p className="source-quote">
                <SentenceHighlight text={c.text} query={query} />
              </p>
              <button className="view-doc-btn" onClick={() => onViewDocument(c)}>
                View in document →
              </button>
            </article>
          ))}
        </div>
      </aside>
    </div>
  )
}

function fmt(v) {
  return v == null ? '—' : Number(v).toFixed(4)
}
