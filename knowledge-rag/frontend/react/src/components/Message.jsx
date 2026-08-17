import { useState } from 'react'
import MetricsPanel from './MetricsPanel'

// Renders assistant answers with the three structures the generation prompt
// produces: clickable [n] citation pills, **bold** headings, and "-" bullets.
// No markdown dependency — this covers the actual output contract.
function renderRich(text, onOpenSource) {
  const tokens = text.split(/(\[\d+\]|\*\*[^*]+\*\*)/g)
  return tokens.map((token, i) => {
    const cite = token.match(/^\[(\d+)\]$/)
    if (cite) {
      return (
        <button key={i} className="cite-pill" onClick={() => onOpenSource(Number(cite[1]))}>
          {token}
        </button>
      )
    }
    const bold = token.match(/^\*\*([^*]+)\*\*$/)
    if (bold) return <strong key={i}>{bold[1]}</strong>
    return <span key={i}>{token}</span>
  })
}

function renderAnswer(text, onOpenSource) {
  const blocks = []
  let list = []
  const flushList = () => {
    if (list.length) {
      blocks.push(
        <ul key={`list-${blocks.length}`} className="answer-list">
          {list.map((item, i) => (
            <li key={i}>{renderRich(item, onOpenSource)}</li>
          ))}
        </ul>
      )
      list = []
    }
  }
  text.split('\n').forEach((line, i) => {
    const bullet = line.trim().match(/^[-•*]\s+(.*)$/)
    if (bullet) {
      list.push(bullet[1])
      return
    }
    flushList()
    if (line.trim()) {
      blocks.push(
        <p key={`line-${i}`} className="answer-line">
          {renderRich(line, onOpenSource)}
        </p>
      )
    }
  })
  flushList()
  return blocks
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
