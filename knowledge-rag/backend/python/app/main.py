from dotenv import load_dotenv

# Load .env before any module reads configuration (CHROMA_PERSISTENCE_DIR, RRF_K, ...)
load_dotenv()

from fastapi import FastAPI
from .routes import router as api_router

app = FastAPI(title="Knowledge RAG Retrieval Service")

# Include routers
app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
