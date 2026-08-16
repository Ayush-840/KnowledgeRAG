# Knowledge RAG — Frontend

React 19 + Vite UI for Knowledge RAG. Dark glassmorphism design, single
design-token source of truth in `src/index.css`.

## Scripts

```bash
npm run dev      # start the Vite dev server (http://localhost:5173)
npm run build    # production build to dist/
npm run lint     # oxlint
npm run preview  # preview the production build
```

## Structure

- `src/App.jsx` — landing page (branded hero, features, pipeline)
- `src/Logo.jsx` — inline SVG logo mark (document + knowledge-graph motif)
- `src/index.css` — design tokens: brand colors, glass surfaces, Inter type
- `src/App.css` — component styles

Brand assets (in `public/`): `favicon.svg` (browser tab), `logo.svg`
(transparent mark), `wordmark.svg` (mark + wordmark lockup, for social/OG use).
