import { useState } from 'react'
import MetricsPanel from './MetricsPanel'

function renderAnswer(text, onOpenSource) {
  const parts = text.split(/(\[\d+\])/g)
  return parts.map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/)
    if (m) {
      return (
        <button key={i} className="cite-pill" onClick={() => onOpenSource(Number(m[1]))}>
          {m[0]}
        </button>
      )
    }
    return <span key={i}>{part}</span>
  })
}

export default function Message({ message, onOpenSource }) {
  const [showMetrics, setShowMetrics] = useState(false)
  const isUser = message.role === 'user'
  const sourceCount = message.sources?.length || 0

  return (
    <div className={`msg ${isUser ? 'msg-user' : 'msg-assistant'}`}>
      <div className="msg-bubble">
        {message.loading ? (
          <div className="msg-loading">
            <span className="spinner" aria-hidden="true" />
            Searching your documents…
          </div>
        ) : message.error ? (
          <div className="msg-error">{message.error}</div>
        ) : (
          <div className="msg-content">{renderAnswer(message.content || '', onOpenSource)}</div>
        )}

        {!message.loading && !message.error && sourceCount > 0 && (
          <div className="msg-meta">
            <button className="sources-btn" onClick={() => onOpenSource(null)}>
              Sources ({sourceCount})
            </button>
            {message.metrics && (
              <button className="metrics-btn" onClick={() => setShowMetrics((v) => !v)}>
                {showMetrics ? 'Hide metrics' : 'Dev metrics'}
              </button>
            )}
          </div>
        )}

        {showMetrics && message.metrics && (
          <MetricsPanel metrics={message.metrics} counts={message.counts} />
        )}
      </div>
    </div>
  )
}
