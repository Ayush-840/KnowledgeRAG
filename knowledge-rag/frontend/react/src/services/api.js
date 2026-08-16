// API client for the Knowledge RAG backend.
// Uses same-origin relative paths (Vite dev proxy -> backend); override the
// base with VITE_API_URL when the backend lives elsewhere.

const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, { method = 'GET', body, timeoutMs = 120000, signal } = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(new DOMException('Request timed out', 'TimeoutError')), timeoutMs)
  const onAbort = () => controller.abort(signal?.reason || new DOMException('Aborted', 'AbortError'))
  signal?.addEventListener('abort', onAbort, { once: true })
  try {
    const res = await fetch(`${BASE}${path}`, {
      method,
      headers: body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
      body: body instanceof FormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })
    if (!res.ok) {
      let detail = `Request failed (${res.status})`
      try {
        const data = await res.json()
        detail = data.detail || detail
      } catch {
        /* keep default message */
      }
      throw new Error(detail)
    }
    return await res.json()
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', onAbort)
  }
}

/** Upload a document into a session. params: { chunk_size, overlap, strategy }. */
export function ingestFile(sessionId, file, params = {}) {
  const fd = new FormData()
  fd.append('file', file)
  const qs = new URLSearchParams(params).toString()
  return request(`/ingest/${sessionId}${qs ? `?${qs}` : ''}`, {
    method: 'POST',
    body: fd,
    timeoutMs: 300000, // heavy embedding/ingest
  })
}

/** Full RAG chat: retrieval -> rerank -> LLM generation with citations. */
export function chatRequest(sessionId, query, signal) {
  return request(`/chat/${sessionId}`, { method: 'POST', body: { query }, signal })
}

/** List documents in a session (filename, chunk/page counts, embedder). */
export function getDocuments(sessionId) {
  return request(`/documents/${sessionId}`)
}

/** Fetch one document's chunks in document order, for the in-context viewer. */
export function getDocument(sessionId, filename) {
  return request(`/documents/${sessionId}/${encodeURIComponent(filename)}`)
}
