import csv
import os
import re
from typing import List, Optional, Tuple

from pypdf import PdfReader
import pdfplumber

from rank_bm25 import BM25Okapi

from .dependencies import get_session_vectors, persist_bm25
from .embedders import get_embedder

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md", ".csv"}
MAX_CSV_ROWS = int(os.getenv("MAX_CSV_ROWS", "50000"))

# ----- Text extraction -----

def extract_text_from_pdf(file_path: str) -> List[Tuple[int, str]]:
    """Extract text from each page of a PDF.
    Returns a list of (page_number, page_text).
    """
    pages = []
    # Try pypdf first
    try:
        reader = PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append((i + 1, text))
        return pages
    except Exception:
        # Fallback to pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages.append((i + 1, text))
        return pages


def extract_text_from_txt(file_path: str) -> List[Tuple[int, str]]:
    """Treat a plain text file as a single page.
    Returns a list with one tuple (1, content).
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return [(1, content)]


def extract_blocks_from_docx(file_path: str) -> List[dict]:
    """Extract paragraphs from a .docx, preserving heading structure.
    Returns a list of {"text": str, "heading": Optional[str]} — a heading paragraph
    becomes a block with heading set and empty text.
    """
    from docx import Document

    doc = Document(file_path)
    blocks = []
    for para in doc.paragraphs:
        text = para.text.strip()
        style_name = getattr(para.style, "name", None)
        style = (style_name or "").lower()
        if style.startswith("heading"):
            blocks.append({"text": "", "heading": text})
        else:
            blocks.append({"text": text, "heading": None})
    return blocks


def extract_blocks_from_markdown(file_path: str) -> List[dict]:
    """Extract a .md into paragraph blocks; heading lines (#..######) become
    heading blocks so the structure-aware chunker can split along headings.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    blocks = []
    for para in re.split(r"\n\s*\n", content):
        para = para.strip()
        if not para:
            continue
        lines = para.splitlines()
        m = re.match(r"^(#{1,6})\s+(.*)", lines[0])
        if m:
            blocks.append({"text": "", "heading": m.group(2).strip()})
            body = "\n".join(lines[1:]).strip()
            if body:
                blocks.append({"text": body, "heading": None})
        else:
            blocks.append({"text": para, "heading": None})
    return blocks


def extract_csv_chunks(file_path: str, max_words: int = 500) -> Tuple[List[Tuple[str, int, int]], int]:
    """Chunk a .csv row-wise: each chunk keeps the header row and groups data rows
    until max_words is reached, so chunks stay tabular and coherent.
    Returns ([(chunk_text, first_data_row, last_data_row)], data_row_count) — row
    numbers are 1-indexed file rows (header is row 1).
    """
    with open(file_path, newline="", encoding="utf-8", errors="ignore") as f:
        rows = [row for row in csv.reader(f) if any(cell.strip() for cell in row)]
    if not rows:
        raise ValueError("CSV file is empty")
    header = rows[0]
    body = rows[1:]
    if len(body) > MAX_CSV_ROWS:
        raise ValueError(f"CSV exceeds row limit of {MAX_CSV_ROWS} data rows")

    header_text = ", ".join(header)
    chunks = []
    current = []
    current_words = 0
    current_start = 2  # data rows start at file row 2 (header is row 1)
    for file_row, row in enumerate(body, start=2):
        row_text = ", ".join(row)
        words = len(row_text.split())
        if current and current_words + words > max_words:
            chunks.append(("\n".join([header_text, *current]), current_start, file_row - 1))
            current, current_words = [], 0
            current_start = file_row
        current.append(row_text)
        current_words += words
    if current:
        chunks.append(("\n".join([header_text, *current]), current_start, len(body) + 1))

    return chunks, len(body)

# ----- Chunking -----

def chunk_text(page_text: str, max_words: int = 500, overlap: int = 100) -> List[str]:
    """Fixed-size chunking: split page text into overlapping word windows.
    Returns a list of chunk strings.
    """
    words = page_text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i : i + max_words]
        chunks.append(" ".join(chunk))
        i += max_words - overlap
    return chunks


def chunk_text_structure_aware(page_text: str, max_words: int = 500, overlap: int = 100) -> List[str]:
    """Structure-aware chunking: respect paragraph boundaries (blank-line separated).
    Paragraphs are grouped into chunks up to max_words; a single oversized paragraph
    is split with the fixed-size splitter. Falls back to fixed-size chunking when the
    text has no paragraph breaks (unstructured text).
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", page_text) if p.strip()]
    if not paragraphs:
        return chunk_text(page_text, max_words, overlap)

    chunks = []
    current: List[str] = []
    current_len = 0
    for para in paragraphs:
        para_words = para.split()
        if current_len + len(para_words) <= max_words:
            current.append(para)
            current_len += len(para_words)
        else:
            if current:
                chunks.append("\n\n".join(current))
            if len(para_words) > max_words:
                # Oversized paragraph: split fixed-size, then continue fresh
                chunks.extend(chunk_text(para, max_words, overlap))
                current, current_len = [], 0
            else:
                current, current_len = [para], len(para_words)
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def chunk_blocks(blocks: List[dict], max_words: int = 500, overlap: int = 100, structure_aware: bool = False) -> List[str]:
    """Chunk block lists (docx/md). structure_aware: heading blocks start a new chunk
    (the heading is carried into the chunk); body blocks group up to max_words, with
    oversized blocks split fixed-size. fixed: flatten all blocks and word-split.
    """
    if not structure_aware:
        full = "\n\n".join(b["text"] for b in blocks if b["text"])
        return chunk_text(full, max_words, overlap)

    chunks = []
    current: List[str] = []
    current_len = 0
    for b in blocks:
        heading = b.get("heading")
        text = b["text"]
        if heading:
            if current:
                chunks.append("\n\n".join(current))
                current, current_len = [], 0
            current.append(heading)
            current_len = len(heading.split())
            continue
        if not text:
            continue
        words = text.split()
        if current_len + len(words) <= max_words:
            current.append(text)
            current_len += len(words)
        else:
            if current:
                chunks.append("\n\n".join(current))
                current, current_len = [], 0
            if len(words) > max_words:
                chunks.extend(chunk_text(text, max_words, overlap))
            else:
                current, current_len = [text], len(words)
    if current:
        chunks.append("\n\n".join(current))
    return chunks


CHUNKERS = {
    "fixed": chunk_text,
    "structure_aware": chunk_text_structure_aware,
}

# ----- Embedding -----

def embed_chunks(chunks: List[str]):
    """Return a list of dense vector embeddings for the given chunks."""
    return get_embedder().embed(chunks)

# ----- BM25 -----

def build_bm25_index(chunks: List[str]):
    """Create a BM25Okapi index from tokenized chunks.
    Returns the BM25 object and the tokenized corpus (list of list of tokens).
    """
    tokenized = [c.lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized)
    return bm25, tokenized

# ----- Ingestion helper -----

def ingest_document(
    session_id: str,
    filename: str,
    file_path: str,
    chunk_size: int = 500,
    overlap: int = 100,
    strategy: str = "fixed",
) -> Tuple[int, int]:
    """Process an uploaded document and store its vectors and BM25 index.
    Returns (page_count, chunk_count).

    chunk_size/overlap/strategy are per-upload settings; the strategy that
    produced the index is recorded in each chunk's metadata so retrieval
    results stay explainable.
    """
    if strategy not in CHUNKERS:
        raise ValueError(f"Unknown chunking strategy: {strategy}")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")

    embedder_name = get_embedder().name
    all_chunks = []
    metadata = []

    def add_chunks(chunks: List[str], page_number: int, extra: Optional[dict] = None):
        for chunk in chunks:
            all_chunks.append(chunk)
            meta = {
                "filename": filename,
                "page_number": page_number,
                "chunk_strategy": strategy,
                "chunk_size": chunk_size,
                "overlap": overlap,
                "embedder": embedder_name,
            }
            if extra:
                meta.update(extra)
            metadata.append(meta)

    page_count = 1
    if ext == ".pdf":
        pages = extract_text_from_pdf(file_path)
        chunker = CHUNKERS[strategy]
        for page_num, page_text in pages:
            add_chunks(chunker(page_text, chunk_size, overlap), page_num)
        page_count = len(pages)
    elif ext == ".txt":
        pages = extract_text_from_txt(file_path)
        chunker = CHUNKERS[strategy]
        for page_num, page_text in pages:
            add_chunks(chunker(page_text, chunk_size, overlap), page_num)
    elif ext == ".docx":
        blocks = extract_blocks_from_docx(file_path)
        add_chunks(chunk_blocks(blocks, chunk_size, overlap, structure_aware=(strategy == "structure_aware")), 1)
    elif ext == ".md":
        blocks = extract_blocks_from_markdown(file_path)
        add_chunks(chunk_blocks(blocks, chunk_size, overlap, structure_aware=(strategy == "structure_aware")), 1)
    elif ext == ".csv":
        csv_chunks, data_rows = extract_csv_chunks(file_path, chunk_size)
        for chunk_text, row_start, row_end in csv_chunks:
            add_chunks([chunk_text], 1, {"row_start": row_start, "row_end": row_end})
        page_count = data_rows  # page_count carries the data-row count for CSVs

    embeddings = embed_chunks(all_chunks)

    # Store in Chroma collection
    session = get_session_vectors(session_id)
    collection = session["collection"]
    ids = [f"{filename}_p{meta['page_number']}_c{i}" for i, meta in enumerate(metadata)]
    collection.add(
        documents=all_chunks,
        embeddings=embeddings.tolist(),
        metadatas=metadata,
        ids=ids,
    )

    # Rebuild the session BM25 index over the FULL corpus so every document in the
    # session stays sparse-searchable (ingest is per-document, but the index is per-session).
    all_docs = collection.get(include=["documents"])
    bm25, tokenized = build_bm25_index(all_docs["documents"])
    persist_bm25(session_id, tokenized, all_docs["ids"])
    session["bm25"] = bm25
    session["bm25_ids"] = all_docs["ids"]

    return page_count, len(all_chunks)
