import { useCallback, useEffect, useRef, useState } from 'react'
import { chatRequest } from '../services/api'

const STORAGE_KEY = 'knowledge-rag:sessions'
const GREETINGS = new Set(['hi', 'hello', 'hey', 'hi there', 'hello there', 'hey there', 'yo', 'sup'])

function loadSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function createSession() {
  return {
    id: crypto.randomUUID(),
    title: 'New chat',
    files: [],
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }
}

export default function useChatSessions() {
  const [sessions, setSessions] = useState(loadSessions)
  const [activeId, setActiveId] = useState(null)
  const abortRef = useRef(null)

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
    } catch {
      /* storage full/unavailable — session keeps working in memory */
    }
  }, [sessions])

  const active = sessions.find((s) => s.id === activeId) || null

  const patch = (id, updater) =>
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...updater(s), updatedAt: Date.now() } : s)))

  const newSession = () => {
    const s = createSession()
    setSessions((prev) => [s, ...prev])
    setActiveId(s.id)
    return s.id
  }

  const selectSession = (id) => setActiveId(id)

  const renameSession = (id, title) => patch(id, (s) => ({ ...s, title: title.trim() || 'Untitled chat' }))

  const deleteSession = (id) => {
    setSessions((prev) => prev.filter((s) => s.id !== id))
    setActiveId((cur) => (cur === id ? null : cur))
  }

  const addFiles = (id, files) => patch(id, (s) => ({ ...s, files: [...s.files, ...files] }))

  const removeFile = (id, name) => patch(id, (s) => ({ ...s, files: s.files.filter((f) => f.name !== name) }))

  const togglePin = (id) => patch(id, (s) => ({ ...s, pinned: !s.pinned }))

  const addTag = (id, tag) =>
    patch(id, (s) => (s.tags?.includes(tag) ? s : { ...s, tags: [...(s.tags || []), tag] }))

  const removeTag = (id, tag) =>
    patch(id, (s) => ({ ...s, tags: (s.tags || []).filter((t) => t !== tag) }))

  const addMessage = (id, msg) => patch(id, (s) => ({ ...s, messages: [...s.messages, msg] }))

  const updateLastMessage = (id, updater) =>
    patch(id, (s) => ({
      ...s,
      messages: s.messages.map((m, i) => (i === s.messages.length - 1 ? updater(m) : m)),
    }))

  const ask = useCallback(
    async (query) => {
      if (!activeId) return
      const q = query.trim()
      if (!q) return
      addMessage(activeId, { role: 'user', content: q })

      // Client-side intent interceptor: greetings never hit the RAG pipeline
      const lower = q.toLowerCase()
      if (GREETINGS.has(lower)) {
        setTimeout(() => {
          addMessage(activeId, {
            role: 'assistant',
            content: 'Hello! How can I assist you with your document?',
            sources: [],
          })
        }, 400)
        return
      }

      addMessage(activeId, { role: 'assistant', content: '', loading: true })
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller
      try {
        const data = await chatRequest(activeId, q, controller.signal)
        updateLastMessage(activeId, (m) => ({
          ...m,
          content: data.answer,
          sources: data.citations || [],
          metrics: data.metrics,
          counts: {
            candidatesRetrieved: data.candidates_retrieved,
            sentToLlm: data.candidates_sent_to_llm,
          },
          loading: false,
        }))
      } catch (err) {
        if (err.name === 'AbortError') return // superseded by a newer ask
        updateLastMessage(activeId, (m) => ({
          ...m,
          content: '',
          error: err.message || 'Something went wrong — check that the backend is running.',
          loading: false,
        }))
      }
    },
    [activeId],
  )

  const stop = () => abortRef.current?.abort()

  return {
    sessions,
    active,
    activeId,
    newSession,
    selectSession,
    renameSession,
    deleteSession,
    addFiles,
    removeFile,
    togglePin,
    addTag,
    removeTag,
    addMessage,
    ask,
    stop,
  }
}
