export default function MetricsPanel({ metrics, counts }) {
  const r = metrics.retrieval_ms || {}
  const t = metrics.tokens || {}
  const rows = [
    ['Dense retrieval', `${r.dense ?? '—'} ms`],
    ['BM25', `${r.bm25 ?? '—'} ms`],
    ['Fusion (RRF)', `${r.fusion ?? '—'} ms`],
    ['Reranking', `${r.rerank ?? '—'} ms`],
    ['LLM generation', `${metrics.generation_ms ?? '—'} ms`],
    ['Total round-trip', `${metrics.total_ms ?? '—'} ms`],
    ['Prompt tokens', t.prompt ?? '—'],
    ['Completion tokens', t.completion ?? '—'],
    ['Total tokens', t.total ?? '—'],
  ]
  if (counts) {
    rows.push(['Candidates retrieved', String(counts.candidatesRetrieved)])
    rows.push(['Sent to LLM', String(counts.sentToLlm)])
  }
  return (
    <div className="metrics-panel">
      <div className="metrics-model">model: {metrics.model || '—'}</div>
      <table className="metrics-table">
        <tbody>
          {rows.map(([k, v]) => (
            <tr key={k}>
              <td>{k}</td>
              <td>{v}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
