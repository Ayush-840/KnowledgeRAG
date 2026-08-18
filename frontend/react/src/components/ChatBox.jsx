import { useEffect, useRef, useState } from 'react'
import Message from './Message'
import FileUpload from './FileUpload'

export default function ChatBox({ session, onAsk, onStop, onOpenSource, onFilesAdded, onFileRemoved }) {
  const [input, setInput] = useState('')
  const scrollRef = useRef(null)
  const areaRef = useRef(null)
  const loading = session?.messages?.some((m) => m.loading) || false

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [session?.messages])

  const send = () => {
    if (!input.trim() || loading) return
    onAsk(input)
    setInput('')
    if (areaRef.current) areaRef.current.style.height = 'auto'
  }

  return (
    <div className="chatbox">
      <div className="chat-scroll" ref={scrollRef}>
        {session && (
          <FileUpload
            sessionId={session.id}
            files={session.files}
            onFilesAdded={onFilesAdded}
            onFileRemoved={onFileRemoved}
          />
        )}
        {session?.messages?.length === 0 && (
          <div className="chat-empty">
            <p>Upload a document, then ask a question.</p>
            <p className="chat-empty-sub">Answers are grounded in your documents with labeled source scores.</p>
          </div>
        )}
        {session?.messages?.map((m, i) => (
          <Message key={i} message={m} onOpenSource={onOpenSource} />
        ))}
      </div>

      <div className="composer">
        <textarea
          ref={areaRef}
          rows={1}
          placeholder="Ask about your documents…  (Enter to send, Shift+Enter for a new line)"
          value={input}
          onChange={(e) => {
            setInput(e.target.value)
            e.target.style.height = 'auto'
            e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              send()
            }
          }}
        />
        {loading ? (
          <button className="send-btn stop" onClick={onStop}>
            Stop
          </button>
        ) : (
          <button className="send-btn" onClick={send} disabled={!input.trim()}>
            Send
          </button>
        )}
      </div>
    </div>
  )
}
