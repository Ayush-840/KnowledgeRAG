import os

from dotenv import load_dotenv

# Load .env before any module reads configuration (CHROMA_PERSISTENCE_DIR, RRF_K, ...)
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router as api_router

app = FastAPI(title="Knowledge RAG Retrieval Service")

# The frontend is served from a different origin (e.g. Vercel) in production,
# so cross-origin requests must be allowed. Default "*" works for a keyless,
# cookie-free API; restrict it with CORS_ORIGINS=https://app.example.com,https://...
# when the deployment should only accept known origins.
_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
