from pydantic import BaseModel, Field
from typing import List, Optional

class IngestResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    filename: str = Field(..., description="Original uploaded filename")
    title: Optional[str] = Field(None, description="Best-effort document title (PDF /Title, DOCX core props, MD H1, TXT first line) — None when only the filename should be displayed")
    page_count: int = Field(..., description="Number of pages extracted (for CSVs: number of data rows)")
    chunk_count: int = Field(..., description="Number of text chunks created")
    chunk_size: int = Field(..., description="Chunk size used for this upload")
    overlap: int = Field(..., description="Chunk overlap used for this upload")
    chunk_strategy: str = Field(..., description="Chunking strategy used (fixed | structure_aware)")

class RetrievalScores(BaseModel):
    """Scores from each retrieval stage, kept separate and labeled (never blended)."""
    dense_similarity: Optional[float] = Field(None, description="Raw cosine similarity from dense (Chroma) search")
    bm25: Optional[float] = Field(None, description="Raw BM25 score from sparse search")
    rrf: Optional[float] = Field(None, description="Reciprocal Rank Fusion score combining dense + sparse ranks")
    rerank: Optional[float] = Field(None, description="Cross-encoder reranker relevance score")

class SearchResultChunk(BaseModel):
    id: str = Field(..., description="Chunk identifier (stable per chunk, used for citations and logs)")
    text: str = Field(..., description="Chunk text")
    filename: str = Field(..., description="Source document filename")
    title: Optional[str] = Field(None, description="Best-effort document title, when one exists")
    page_number: int = Field(..., description="Page number of the source document")
    chunk_strategy: str = Field("fixed", description="Chunking strategy that produced this chunk")
    retrieval_scores: RetrievalScores = Field(..., description="Stage-wise retrieval scores (labeled)")
    confidence: Optional[float] = Field(None, description="Reranker score if available, else RRF score")

class SearchResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., description="Original query string")
    results: List[SearchResultChunk] = Field(..., description="Top-k chunks after reranking (sent to generation)")
    candidates_retrieved: int = Field(..., description="Number of fused candidates retrieved before reranking")
    candidates_sent_to_llm: int = Field(..., description="Number of chunks sent to generation after reranking")

class Citation(BaseModel):
    marker: int = Field(..., description="Inline citation marker ([n] in the answer)")
    id: str = Field(..., description="Chunk identifier")
    filename: str = Field(..., description="Source document filename")
    title: Optional[str] = Field(None, description="Best-effort document title, when one exists")
    page_number: int = Field(..., description="Page (or CSV row range start) of the source")
    text: str = Field(..., description="Chunk text quote")
    scores: RetrievalScores = Field(..., description="Stage-wise retrieval scores (labeled)")
    confidence: Optional[float] = Field(None, description="Reranker score if available, else RRF score")

class ChatMetrics(BaseModel):
    retrieval_ms: dict = Field(..., description="Retrieval stage latencies: {dense, bm25, fusion, rerank, total}")
    generation_ms: float = Field(..., description="LLM generation latency in ms")
    total_ms: float = Field(..., description="End-to-end round-trip latency in ms")
    tokens: dict = Field(..., description="Token usage: {prompt, completion, total}")
    model: str = Field(..., description="Generation model used")

class ChatResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., description="Original query string")
    answer: str = Field(..., description="Generated answer with [n] citation markers")
    citations: List[Citation] = Field(..., description="Verified citations referenced by the answer")
    metrics: ChatMetrics = Field(..., description="Latency and token-usage breakdown")
    candidates_retrieved: int = Field(..., description="Number of fused candidates retrieved before reranking")
    candidates_sent_to_llm: int = Field(..., description="Number of chunks sent to generation after reranking")
