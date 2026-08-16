import { useRef, useState } from 'react'
import { ingestFile } from '../services/api'

const ACCEPT = ['.pdf', '.txt', '.docx', '.md', '.csv']
const MAX_MB = 50

const STAGES = ['Uploading…', 'Parsing…', 'Chunking…', 'Embedding…', 'Indexed']

function humanSize(bytes) {
  if (!bytes && bytes !== 0) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function FileUpload({ sessionId, files, onFilesAdded, onFileRemoved }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [items, setItems] = useState([]) // { name, status: 0..4, error }
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [settings, setSettings] = useState({ chunk_size: 500, overlap: 100, strategy: 'fixed' })

  const validate = (file) => {
    const ext = '.' + (file.name.split('.').pop() || '').toLowerCase()
    if (!ACCEPT.includes(ext)) return `Unsupported file type (${ext}). Supported: ${ACCEPT.join(', ')}`
    if (file.size > MAX_MB * 1024 * 1024) return `File exceeds the ${MAX_MB} MB limit`
    return null
  }

  const upload = async (file) => {
    const err = validate(file)
    if (err) {
      setItems((prev) => [...prev, { name: file.name, size: file.size, status: -1, error: err }])
      return
    }
    const item = { name: file.name, size: file.size, status: 0 }
    setItems((prev) => [...prev, item])
    const tick = setInterval(() => {
      setItems((prev) =>
        prev.map((it) =>
          it.name === file.name && it.status >= 0 && it.status < 4 ? { ...it, status: it.status + 1 } : it,
        ),
      )
    }, 350)
    try {
      const res = await ingestFile(sessionId, file, settings)
      clearInterval(tick)
      setItems((prev) => prev.map((it) => (it.name === file.name ? { ...it, status: 4, info: res } : it)))
      onFilesAdded([{ name: file.name, size: file.size, chunkCount: res.chunk_count }])
    } catch (e) {
      clearInterval(tick)
      setItems((prev) => prev.map((it) => (it.name === file.name ? { ...it, status: -1, error: e.message } : it)))
    }
  }

  const handleFiles = (list) => Array.from(list).forEach(upload)

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  return (
    <div className={`upload ${dragging ? 'upload-dragging' : ''}`}>
      <div
        className="dropzone"
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT.join(',')}
          multiple
          hidden
          onChange={(e) => {
            handleFiles(e.target.files)
            e.target.value = ''
          }}
        />
        <p className="dropzone-title">Drop documents here, or click to browse</p>
        <div className="dropzone-glow" aria-hidden="true" />
        <p className="dropzone-sub">PDF · TXT · DOCX · MD · CSV — max {MAX_MB} MB each</p>
        <button
          type="button"
          className="advanced-toggle"
          onClick={(e) => {
            e.stopPropagation()
            setShowAdvanced((v) => !v)
          }}
        >
          {showAdvanced ? 'Hide' : 'Show'} advanced settings
        </button>
        {showAdvanced && (
          <div className="advanced-settings" onClick={(e) => e.stopPropagation()}>
            <label>
              Chunk size
              <input
                type="number"
                min={50}
                max={2000}
                value={settings.chunk_size}
                onChange={(e) => setSettings((s) => ({ ...s, chunk_size: Number(e.target.value) }))}
              />
            </label>
            <label>
              Overlap
              <input
                type="number"
                min={0}
                value={settings.overlap}
                onChange={(e) => setSettings((s) => ({ ...s, overlap: Number(e.target.value) }))}
              />
            </label>
            <label>
              Strategy
              <select
                value={settings.strategy}
                onChange={(e) => setSettings((s) => ({ ...s, strategy: e.target.value }))}
              >
                <option value="fixed">fixed</option>
                <option value="structure_aware">structure_aware</option>
              </select>
            </label>
          </div>
        )}
      </div>

      {items.length > 0 && (
        <ul className="upload-items">
          {items.map((it) => {
            const ext = it.name.split('.').pop()?.toUpperCase() || 'FILE'
            const isCsv = ext === 'CSV'
            return (
              <li key={it.name} className="upload-item">
                <div className="upload-item-head">
                  <span className="file-badge">{ext}</span>
                  <span className="upload-name">{it.name}</span>
                  <span className="upload-size">{humanSize(it.size)}</span>
                </div>
                {it.status === -1 ? (
                  <span className="upload-error">{it.error}</span>
                ) : (
                  <div className="upload-progress">
                    <div className="stage-track">
                      <div className="stage-fill" style={{ width: `${(it.status / 4) * 100}%` }} />
                    </div>
                    <span className="upload-stage-label">{STAGES[it.status]}</span>
                  </div>
                )}
                {it.status === 4 && it.info && (
                  <div className="upload-meta">
                    <span>
                      {it.info.page_count} {isCsv ? 'rows' : 'pages'}
                    </span>
                    <span>{it.info.chunk_count} chunks</span>
                    <span>{it.info.chunk_strategy}</span>
                    <span className="upload-meta-ok">✓ indexed</span>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}

      {files.length > 0 && (
        <ul className="session-files">
          {files.map((f) => (
            <li key={f.name} className="session-file">
              <span className="file-badge">{f.name.split('.').pop().toUpperCase()}</span>
              <span className="file-name">{f.name}</span>
              <button
                className="file-remove"
                onClick={() => {
                  onFileRemoved(f.name)
                  setItems((prev) => prev.filter((it) => it.name !== f.name))
                }}
                aria-label={`Remove ${f.name}`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
