import { useEffect, useState } from 'react'
import Logo from './Logo'
import Home from './pages/Home'
import './App.css'
import './chat.css'

const features = [
  {
    title: 'Hybrid retrieval',
    text: 'Dense embeddings and BM25 sparse search, fused with Reciprocal Rank Fusion — no hand-tuned score blending.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M7 4v7a3 3 0 0 0 3 3h7" />
        <path d="M7 4L4 7l3 3" />
        <path d="M17 20v-7a3 3 0 0 0-3-3H7" />
        <path d="M17 20l3-3-3-3" />
      </svg>
    ),
  },
  {
    title: 'Cross-encoder reranking',
    text: 'Retrieve wide, rerank narrow: a fused pool of candidates is re-scored by a cross-encoder before the top few reach the model.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M3 5h18" />
        <path d="M6 12h12" />
        <path d="M9 19h6" />
      </svg>
    ),
  },
  {
    title: 'Component-wise evaluation',
    text: 'Context precision, context recall, faithfulness and answer relevance measured separately — not one unverifiable quality score.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M4 19h16" />
        <path d="M4 15l4-6 4 3 5-8" />
        <path d="M17 4h3v3" />
      </svg>
    ),
  },
  {
    title: 'Retrieval transparency',
    text: 'Every source chunk carries its stage-wise scores — dense, BM25, RRF and reranker — clearly labeled, never blended.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
]

const pipeline = ['Ingest', 'Chunk', 'Embed', 'Retrieve', 'Rerank', 'Answer']

function App() {
  const [view, setView] = useState(() => (window.location.hash === '#/chat' ? 'chat' : 'landing'))

  useEffect(() => {
    const onHash = () => setView(window.location.hash === '#/chat' ? 'chat' : 'landing')
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const goChat = (e) => {
    e?.preventDefault()
    window.location.hash = '#/chat'
  }

  if (view === 'chat') return <Home />

  return (
    <div className="page">
      <header className="site-header">
        <a className="brand" href="/" aria-label="Knowledge RAG home">
          <Logo size={34} />
          <span className="brand-name">
            Knowledge <span className="brand-accent">RAG</span>
          </span>
        </a>
        <nav className="site-nav" aria-label="Primary">
          <a href="#features">Features</a>
          <a href="#pipeline">Pipeline</a>
          <a className="nav-cta" href="#/chat" onClick={goChat}>Get started</a>
        </nav>
      </header>

      <main>
        <section className="hero">
          <span className="hero-badge">
            <span className="pulse" aria-hidden="true" />
            Hybrid RAG · RRF fusion · Reranking
          </span>
          <h1 className="hero-title">
            Ask your documents.
            <br />
            <span className="hero-gradient">Get grounded answers.</span>
          </h1>
          <p className="hero-sub">
            Knowledge RAG turns your PDFs and notes into an answerable corpus —
            hybrid retrieval, cross-encoder reranking, and every score in the
            pipeline exposed for inspection.
          </p>
          <div className="hero-actions">
            <a className="btn btn-primary" href="#/chat" onClick={goChat}>Upload a document</a>
            <a className="btn btn-ghost" href="#pipeline">See how it works</a>
          </div>
        </section>

        <section id="features" className="features">
          <h2 className="section-title">Built to be checked, not trusted</h2>
          <div className="feature-grid">
            {features.map((f) => (
              <article key={f.title} className="feature-card">
                <div className="feature-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="pipeline" className="pipeline">
          <h2 className="section-title">The retrieval pipeline</h2>
          <ol className="pipeline-steps">
            {pipeline.map((step, i) => (
              <li key={step}>
                <span className="step-num">{i + 1}</span>
                <span className="step-name">{step}</span>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <footer className="site-footer">
        <div className="footer-brand">
          <Logo size={22} />
          <span>Knowledge RAG</span>
        </div>
        <p className="footer-note">
          Hybrid retrieval with honest answers — every claim traceable to a source chunk.
        </p>
        <p className="footer-copy">© {new Date().getFullYear()} Knowledge RAG</p>
      </footer>
    </div>
  )
}

export default App
