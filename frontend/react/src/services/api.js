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
    // Detect SPA fallback: if the response is HTML instead of JSON, the request
    // was caught by a client-side router rewrite instead of reaching the backend.
    const ct = res.headers.get('content-type') || ''
    if (ct.includes('text/html')) {
      throw new Error(
        'The API returned HTML instead of JSON. '
        + 'This usually means the backend URL is not configured. '
        + 'Set VITE_API_URL to your backend URL (e.g. https://your-backend.onrender.com) '
        + 'in your hosting environment variables and redeploy.',
      )
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

/**
 * Upload with real progress: the backend streams SSE-style events for each
 * pipeline stage (parsing/chunking/embedding/indexing) plus a final `done`
 * event carrying the IngestResponse. onEvent({ stage, error, result }) fires
 * for every event. Resolves with the final result; rejects on an error event.
 */
export async function ingestFileStream(sessionId, file, params = {}, onEvent) {
  const fd = new FormData()
  fd.append('file', file)
  const qs = new URLSearchParams({ ...params, stream: '1' }).toString()
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(new DOMException('Request timed out', 'TimeoutError')), 300000)
  try {
    const res = await fetch(`${BASE}/ingest/${sessionId}?${qs}`, {
      method: 'POST',
      body: fd,
      signal: controller.signal,
      // Do NOT set Content-Type for FormData — the browser must set the
      // multipart boundary automatically. Setting it manually breaks uploads.
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
    // Detect SPA fallback: if the response is HTML instead of SSE, the request
    // was caught by a client-side router rewrite (e.g. Vercel SPA catch-all)
    // instead of reaching the backend. This happens when VITE_API_URL is not set
    // and the frontend is deployed to a different origin than the backend.
    const ct = res.headers.get('content-type') || ''
    if (ct.includes('text/html')) {
      throw new Error(
        'The upload endpoint returned HTML instead of a stream. '
        + 'This usually means the backend URL is not configured. '
        + 'Set VITE_API_URL to your backend URL (e.g. https://your-backend.onrender.com) '
        + 'in your Vercel/hosting environment variables and redeploy.',
      )
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      let idx
      while ((idx = buf.indexOf('\n\n')) !== -1) {
        const raw = buf.slice(0, idx)
        buf = buf.slice(idx + 2)
        const line = raw.split('\n').find((l) => l.startsWith('data: '))
        if (!line) continue
        let evt
        try {
          evt = JSON.parse(line.slice(6))
        } catch {
          continue
        }
        onEvent?.(evt)
        if (evt.stage === 'error') throw new Error(evt.error || 'Ingestion failed')
        if (evt.stage === 'done') return evt.result
      }
    }
    throw new Error('Ingestion stream ended unexpectedly')
  } finally {
    clearTimeout(timer)
  }
}

/** Short chat title for a query (LLM summary when a key is configured, else heuristic). */
export async function generateTitle(query) {
  const data = await request('/title', { method: 'POST', body: { query }, timeoutMs: 15000 })
  return data.title
}

/** 3D projection of every chunk in a session: { method, points: [{id,x,y,z,filename,count?}], clustered }. */
export function getSpace(sessionId) {
  return request(`/space/${sessionId}`, { timeoutMs: 120000 })
}

/** Drop a query into the existing map: { point: {x,y,z}, promoted_ids, retrieved_ids }. */
export function querySpace(sessionId, query) {
  return request(`/space/${sessionId}/query`, { method: 'POST', body: { query } })
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

/** Get the knowledge graph for a session. */
export function getGraph(sessionId) {
  return request(`/graph/${sessionId}`, { timeoutMs: 60000 })
}

/** Query the knowledge graph with entities from a query string. */
export function queryGraph(sessionId, query) {
  return request(`/graph/${sessionId}/query`, { method: 'POST', body: { query } })
}
