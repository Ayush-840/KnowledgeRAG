// Highlight the sentence in `text` with the most word overlap against the query.
export default function SentenceHighlight({ text, query }) {
  const words = new Set((query || '').toLowerCase().match(/[a-z0-9$%.-]+/g) || [])
  if (words.size === 0) return <>{text}</>
  const sentences = text.split(/(?<=[.!?])\s+|\n+/).filter(Boolean)
  let best = null
  let bestScore = -1
  for (const s of sentences) {
    const sw = new Set(s.toLowerCase().match(/[a-z0-9$%.-]+/g) || [])
    let score = 0
    for (const w of words) if (sw.has(w)) score += 1
    if (score > bestScore) {
      bestScore = score
      best = s
    }
  }
  if (!best || bestScore === 0) return <>{text}</>
  const idx = text.indexOf(best)
  return (
    <>
      {text.slice(0, idx)}
      <mark>{best}</mark>
      {text.slice(idx + best.length)}
    </>
  )
}
