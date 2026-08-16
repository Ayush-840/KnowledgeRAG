import { useState } from 'react'
import useChatSessions from '../hooks/useChatSessions'
import Sidebar from '../components/Sidebar'
import ChatBox from '../components/ChatBox'
import SourceDrawer from '../components/SourceDrawer'
import DocumentViewer from '../components/DocumentViewer'
import Logo from '../Logo'

export default function Home() {
  const chat = useChatSessions()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [drawerMarker, setDrawerMarker] = useState(null)
  const [drawerQuery, setDrawerQuery] = useState('')
  const [viewer, setViewer] = useState(null) // { filename, highlightId }

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
          onClose={() => setDrawerOpen(false)}
          citations={drawerCitations(chat.active)}
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
    </div>
  )
}

function drawerCitations(session) {
  const msgs = session.messages || []
  const last = [...msgs].reverse().find((m) => m.role === 'assistant' && m.sources?.length)
  return last ? last.sources : []
}
