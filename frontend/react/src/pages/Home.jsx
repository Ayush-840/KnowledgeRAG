import { lazy, Suspense, useCallback, useEffect, useState } from 'react'
import useChatSessions from '../hooks/useChatSessions'
import Sidebar from '../components/Sidebar'
import ChatBox from '../components/ChatBox'
import SourceDrawer from '../components/SourceDrawer'
import DocumentViewer from '../components/DocumentViewer'
import Logo from '../Logo'
import { getSpace, querySpace, getDocument, getGraph } from '../services/api'

// The 3D stack (three.js + R3F) is heavy — load it only when the explorer
// opens, so it never taxes the main chat bundle.
const SpacePanel = lazy(() => import('../components/SpacePanel'))
const GraphPanel = lazy(() => import('../components/GraphPanel'))

export default function Home() {
  const chat = useChatSessions()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [drawerMarker, setDrawerMarker] = useState(null)
  const [drawerQuery, setDrawerQuery] = useState('')
  const [viewer, setViewer] = useState(null) // { filename, highlightId }

  // Vector space explorer state
  const [spaceOpen, setSpaceOpen] = useState(false)
  const [spaceData, setSpaceData] = useState(null) // { points, method, clustered, pointCount }
  const [spaceQuery, setSpaceQuery] = useState(null) // { point, promoted_ids, retrieved_ids }
  const [standaloneCitation, setStandaloneCitation] = useState(null) // chunk detail for non-cited points

  // Knowledge graph state
  const [graphOpen, setGraphOpen] = useState(false)
  const [graphData, setGraphData] = useState(null) // { nodes, edges, stats, query_entities }

  const openSources = (marker) => {
    // find the last assistant message to source from
    const msgs = chat.active?.messages || []
    const last = [...msgs].reverse().find((m) => m.role === 'assistant' && m.sources?.length)
    if (!last) return
    setDrawerQuery(last.content || '')
    setDrawerMarker(marker)
    setDrawerOpen(true)
  }

  const newSession = () => {
    chat.newSession()
    setDrawerOpen(false)
    setSpaceOpen(false)
    setGraphOpen(false)
    setStandaloneCitation(null)
  }

  // Load the projection whenever the explorer opens (or docs change)
  const loadSpace = useCallback(async () => {
    if (!chat.active) return
    try {
      const data = await getSpace(chat.active.id)
      setSpaceData(data)
    } catch (e) {
      setSpaceData({ error: e.message })
    }
  }, [chat.active])

  useEffect(() => {
    if (spaceOpen) loadSpace()
  }, [spaceOpen, loadSpace])

  // Load the knowledge graph when the graph panel opens
  const loadGraph = useCallback(async () => {
    if (!chat.active) return
    try {
      const data = await getGraph(chat.active.id)
      setGraphData(data)
    } catch (e) {
      setGraphData({ error: e.message })
    }
  }, [chat.active])

  useEffect(() => {
    if (graphOpen) loadGraph()
  }, [graphOpen, loadGraph])

  // Follow the last completed chat query: drop it into the map live
  const lastAnswer = chat.active?.messages?.filter(
    (m) => m.role === 'assistant' && !m.loading && m.content,
  ).at(-1)
  useEffect(() => {
    if (!spaceOpen || !lastAnswer || !chat.active) return
    const msgs = chat.active.messages
    const ai = msgs.lastIndexOf(lastAnswer)
    const userMsg = [...msgs.slice(0, ai)].reverse().find((m) => m.role === 'user')
    if (!userMsg) return
    querySpace(chat.active.id, userMsg.content)
      .then(setSpaceQuery)
      .catch(() => {})
  }, [spaceOpen, lastAnswer, chat.active])

  // A clicked point opens the SAME citation panel: focus the citation when the
  // point is one of the current answer's sources, else fetch its chunk and show
  // a single-citation detail (one source of truth — no second chunk UI).
  const selectSpacePoint = useCallback(
    async (pointId) => {
      const session = chat.active
      const point = spaceData?.points?.find((p) => p.id === pointId)
      if (!session || !point) return
      const msgs = session.messages || []
      const last = [...msgs].reverse().find((m) => m.role === 'assistant' && m.sources?.length)
      const cit = last?.sources.find((c) => c.id === pointId)
      if (cit) {
        setStandaloneCitation(null)
        setDrawerQuery(last.content || '')
        setDrawerMarker(cit.marker)
        setDrawerOpen(true)
        return
      }
      try {
        const doc = await getDocument(session.id, point.filename)
        const chunk = doc.chunks.find((c) => c.id === pointId)
        if (!chunk) return
        setStandaloneCitation({
          marker: 1,
          id: chunk.id,
          filename: point.filename,
          title: doc.title,
          page_number: chunk.page_number,
          text: chunk.text,
          scores: null,
          confidence: null,
        })
        setDrawerQuery('')
        setDrawerMarker(1)
        setDrawerOpen(true)
      } catch {
        /* ignore fetch errors — the view stays usable */
      }
    },
    [chat.active, spaceData],
  )

  const closeDrawer = () => {
    setDrawerOpen(false)
    setStandaloneCitation(null)
  }

  return (
    <div className="app">
      <Sidebar
        sessions={chat.sessions}
        activeId={chat.activeId}
        onSelect={chat.selectSession}
        onNew={newSession}
        onRename={chat.renameSession}
        onDelete={chat.deleteSession}
        onTogglePin={chat.togglePin}
        onAddTag={chat.addTag}
        onRemoveTag={chat.removeTag}
      />

      <main className="chat-main">
        <header className="chat-header">
          <div className="chat-header-brand">
            <Logo size={26} />
            <span>Knowledge RAG</span>
          </div>
          {chat.active && <span className="chat-header-title">{chat.active.title}</span>}
          {chat.active && (
            <div className="header-toggles">
              <button
                className={`space-toggle ${spaceOpen ? 'space-toggle-active' : ''}`}
                onClick={() => setSpaceOpen((v) => !v)}
                aria-pressed={spaceOpen}
              >
                Vector space
              </button>
              <button
                className={`space-toggle ${graphOpen ? 'space-toggle-active' : ''}`}
                onClick={() => setGraphOpen((v) => !v)}
                aria-pressed={graphOpen}
              >
                Knowledge graph
              </button>
            </div>
          )}
        </header>

        {chat.active ? (
          <ChatBox
            session={chat.active}
            onAsk={chat.ask}
            onStop={chat.stop}
            onOpenSource={openSources}
            onFilesAdded={(files) => chat.addFiles(chat.active.id, files)}
            onFileRemoved={(name) => chat.removeFile(chat.active.id, name)}
          />
        ) : (
          <div className="chat-empty chat-empty-hero">
            <p>Start a new chat to upload documents and ask questions.</p>
            <button className="btn btn-primary" onClick={newSession}>
              New chat
            </button>
          </div>
        )}
      </main>

      {chat.active && (
        <SourceDrawer
          open={drawerOpen}
          onClose={closeDrawer}
          citations={drawerCitations(chat.active, standaloneCitation)}
          query={drawerQuery}
          focusMarker={drawerMarker}
          onViewDocument={(c) => {
            setDrawerOpen(false)
            setViewer({ filename: c.filename, highlightId: c.id })
          }}
        />
      )}

      {chat.active && viewer && (
        <DocumentViewer
          sessionId={chat.active.id}
          filename={viewer.filename}
          highlightId={viewer.highlightId}
          query={drawerQuery}
          onClose={() => setViewer(null)}
        />
      )}

      {chat.active && spaceOpen && (
        <Suspense fallback={<div className="space-panel space-panel-loading">Loading vector space…</div>}>
          <SpacePanel
            points={spaceData?.points || []}
            method={spaceData?.method}
            clustered={spaceData?.clustered}
            pointCount={spaceData?.pointCount}
            query={spaceQuery?.point}
            promotedIds={spaceQuery?.promoted_ids}
            retrievedIds={spaceQuery?.retrieved_ids}
            error={spaceData?.error}
            onSelectPoint={selectSpacePoint}
            onClose={() => setSpaceOpen(false)}
          />
        </Suspense>
      )}

      {chat.active && graphOpen && (
        <Suspense fallback={<div className="space-panel space-panel-loading">Loading knowledge graph…</div>}>
          <GraphPanel
            nodes={graphData?.nodes || []}
            edges={graphData?.edges || []}
            stats={graphData?.stats}
            queryEntities={graphData?.query_entities || []}
            error={graphData?.error}
            onClose={() => setGraphOpen(false)}
          />
        </Suspense>
      )}
    </div>
  )
}

function drawerCitations(session, standalone) {
  if (standalone) return [standalone]
  const msgs = session.messages || []
  const last = [...msgs].reverse().find((m) => m.role === 'assistant' && m.sources?.length)
  return last ? last.sources : []
}
