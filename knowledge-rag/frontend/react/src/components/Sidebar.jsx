import { useMemo, useState } from 'react'

const DAY = 24 * 60 * 60 * 1000
const tagHues = {}

function tagColor(tag) {
  if (!(tag in tagHues)) {
    let h = 0
    for (const ch of tag) h = (h * 31 + ch.charCodeAt(0)) % 360
    tagHues[tag] = h
  }
  const h = tagHues[tag]
  return {
    color: `hsl(${h} 72% 68%)`,
    background: `hsl(${h} 72% 55% / 0.16)`,
    border: `hsl(${h} 72% 60% / 0.45)`,
  }
}

function ageGroup(ts) {
  const age = Date.now() - ts
  if (age < DAY) return 'Today'
  if (age < 7 * DAY) return 'Previous 7 days'
  if (age < 30 * DAY) return 'Previous 30 days'
  return 'Older'
}

function exportSession(s) {
  const blob = new Blob([JSON.stringify(s, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${(s.title || 'chat').replace(/[^\w-]+/g, '_')}.json`
  a.click()
  URL.revokeObjectURL(url)
}

export default function Sidebar({
  sessions,
  activeId,
  onSelect,
  onNew,
  onRename,
  onDelete,
  onTogglePin,
  onAddTag,
  onRemoveTag,
}) {
  const [search, setSearch] = useState('')
  const [tagFilter, setTagFilter] = useState(null)
  const [openMenu, setOpenMenu] = useState(null)

  const allTags = useMemo(() => [...new Set(sessions.flatMap((s) => s.tags || []))], [sessions])

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase()
    return sessions.filter((s) => {
      if (tagFilter && !(s.tags || []).includes(tagFilter)) return false
      if (!q) return true
      const hay = [s.title, ...(s.messages || []).map((m) => m.content || '')].join(' ').toLowerCase()
      return hay.includes(q)
    })
  }, [sessions, search, tagFilter])

  const groups = {}
  for (const s of visible) {
    const label = s.pinned ? 'Pinned' : ageGroup(s.createdAt)
    ;(groups[label] = groups[label] || []).push(s)
  }
  const order = ['Pinned', 'Today', 'Previous 7 days', 'Previous 30 days', 'Older']

  const menuAction = (fn) => {
    setOpenMenu(null)
    fn()
  }

  return (
    <aside className="sidebar">
      <button className="new-chat" onClick={onNew}>
        + New chat
      </button>

      <div className="sidebar-search">
        <input
          type="search"
          placeholder="Search chats…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {allTags.length > 0 && (
        <div className="tag-filter">
          {allTags.map((t) => (
            <button
              key={t}
              className={`tag-chip ${tagFilter === t ? 'tag-chip-active' : ''}`}
              style={tagFilter === t ? tagColor(t) : undefined}
              onClick={() => setTagFilter((cur) => (cur === t ? null : t))}
            >
              {t}
            </button>
          ))}
          {tagFilter && (
            <button className="tag-filter-clear" onClick={() => setTagFilter(null)}>
              clear
            </button>
          )}
        </div>
      )}

      <div className="sidebar-scroll">
        {order.map(
          (label) =>
            groups[label] && (
              <div key={label} className="session-group">
                <h4 className="session-group-label">
                  {label}
                  {label === 'Pinned' && <span className="pin-mark">📌</span>}
                </h4>
                {groups[label].map((s) => (
                  <div
                    key={s.id}
                    className={`session-item ${s.id === activeId ? 'session-active' : ''}`}
                    onClick={() => onSelect(s.id)}
                    title="Click to open"
                  >
                    <span className="session-title">
                      {s.pinned && <span className="pin-glyph">📌</span>}
                      {s.title}
                    </span>
                    {s.tags?.length > 0 && (
                      <span className="session-tags">
                        {s.tags.map((t) => (
                          <button
                            key={t}
                            className="tag-chip tag-chip-sm"
                            style={tagColor(t)}
                            onClick={(e) => {
                              e.stopPropagation()
                              setTagFilter((cur) => (cur === t ? null : t))
                            }}
                            title={`Filter by ${t}`}
                          >
                            {t}
                          </button>
                        ))}
                      </span>
                    )}
                    <button
                      className="session-menu-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        setOpenMenu((cur) => (cur === s.id ? null : s.id))
                      }}
                      aria-label="Chat actions"
                    >
                      ⋯
                    </button>
                    {openMenu === s.id && (
                      <div className="session-menu" onClick={(e) => e.stopPropagation()}>
                        <button onClick={() => menuAction(() => onRename(s.id, window.prompt('Rename chat', s.title) ?? s.title))}>
                          Rename
                        </button>
                        <button onClick={() => menuAction(() => onTogglePin(s.id))}>
                          {s.pinned ? 'Unpin' : 'Pin to top'}
                        </button>
                        <button
                          onClick={() =>
                            menuAction(() => {
                              const tag = window.prompt('Add a tag (e.g. Legal, Research)')
                              if (tag?.trim()) onAddTag(s.id, tag.trim())
                            })
                          }
                        >
                          Add tag…
                        </button>
                        {s.tags?.length > 0 && (
                          <button
                            onClick={() =>
                              menuAction(() => {
                                const tag = window.prompt(`Remove tag from ${s.title}`, s.tags[0])
                                if (tag?.trim()) onRemoveTag(s.id, tag.trim())
                              })
                            }
                          >
                            Remove tag…
                          </button>
                        )}
                        <button onClick={() => menuAction(() => exportSession(s))}>Export</button>
                        <button className="menu-danger" onClick={() => menuAction(() => onDelete(s.id))}>
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ),
        )}
        {visible.length === 0 && <p className="sidebar-empty">{sessions.length === 0 ? 'No chats yet' : 'No matching chats'}</p>}
      </div>
    </aside>
  )
}
