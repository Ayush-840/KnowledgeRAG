import { useEffect, useRef, useState } from 'react'
import { getDocument } from '../services/api'
import SentenceHighlight from './SentenceHighlight'

export default function DocumentViewer({ sessionId, filename, highlightId, query, onClose }) {
  const [doc, setDoc] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const refs = useRef({})

  useEffect(() => {
    let alive = true
    setDoc(null)
    setError(null)
    setLoading(true)
    getDocument(sessionId, filename)
      .then((d) => {
        if (alive) setDoc(d)
      })
      .catch((e) => {
        if (alive) setError(e.message)
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [sessionId, filename])

  useEffect(() => {
    if (doc && highlightId && refs.current[highlightId]) {
      refs.current[highlightId].scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [doc, highlightId])

  return (
    <div className="docviewer-overlay" onClick={onClose}>
      <aside className="docviewer" onClick={(e) => e.stopPropagation()}>
        <header className="docviewer-header">
          <div className="docviewer-title">
            <strong>{doc ? doc.title || doc.filename : filename}</strong>
            {doc && <span className="docviewer-sub">{doc.chunk_count} chunks</span>}
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close document viewer">
            ✕
          </button>
        </header>

        <div className="docviewer-body">
          {loading && (
            <div className="msg-loading">
              <span className="spinner" aria-hidden="true" />
              Loading document…
            </div>
          )}
          {error && <div className="msg-error">Could not load document: {error}</div>}
          {doc &&
            doc.chunks.map((c) => (
              <section
                key={c.id}
                ref={(el) => (refs.current[c.id] = el)}
                className={`doc-chunk ${c.id === highlightId ? 'doc-chunk-highlight' : ''}`}
              >
                <div className="doc-chunk-label">
                  {c.row_start != null ? `rows ${c.row_start}–${c.row_end}` : `page ${c.page_number}`}
                  <span className="doc-chunk-strategy">{c.chunk_strategy}</span>
                </div>
                <p className="doc-chunk-text">
                  <SentenceHighlight text={c.text} query={query} />
                </p>
              </section>
            ))}
        </div>
      </aside>
    </div>
  )
}
