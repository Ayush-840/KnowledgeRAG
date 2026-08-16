"""3D vector space projection for the Vector Space Explorer.

Reduces the session's chunk embeddings (384-dim MiniLM, or whatever the
configured embedder produces) to 3D with UMAP. UMAP is chosen over t-SNE for
two concrete reasons:

- Its fitted model can .transform() a *new* point (an incoming query embedding)
  into the existing map without recomputing the whole projection — t-SNE is
  non-parametric and cannot do this. Every query therefore drops into the scene
  live, in real time.
- UMAP preserves global structure (relative distance between clusters) better
  than t-SNE, which is what lets a user see "which document is this cluster".

Discipline: the full fit is cached per document set (recomputed only when
chunks are added/removed — re-running it per query would jitter every point and
destroy the "map" mental model). The query transform is the only per-query
work. Above UMAP_CLUSTER_THRESHOLD chunks, points are grid-clustered into
representative markers sized by cluster count so the scene never degrades into
a laggy point cloud on modest hardware.

If UMAP is unavailable or the corpus is too small for it (n < 6), we fall back
to a 3-component PCA (same caching + transform discipline), reported via the
`method` field so the UI can label it honestly.
"""

import hashlib
import os
from typing import Dict, List, Optional

import numpy as np

from .dependencies import get_session_vectors
from .utils import embed_chunks

UMAP_CLUSTER_THRESHOLD = int(os.getenv("UMAP_CLUSTER_THRESHOLD", "4000"))
BOUND = 8.0  # normalized coordinates live in [-BOUND, BOUND] for a stable camera


def _fingerprint(session_id: str) -> str:
    """Fingerprint the document set so the cached projection only recomputes
    when chunks are added/removed."""
    session = get_session_vectors(session_id)
    collection = session["collection"]
    got = collection.get(include=["metadatas"])
    filenames = sorted({m.get("filename", "") for m in got["metadatas"]})
    embedders = sorted({m.get("embedder", "") for m in got["metadatas"]})
    raw = f"{session_id}|{len(got['ids'])}|{filenames}|{embedders}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _umap_fit(embed_matrix: np.ndarray, n_samples: int):
    from umap import UMAP

    n_neighbors = min(15, max(2, n_samples - 1))
    transformer = UMAP(n_components=3, n_neighbors=n_neighbors, min_dist=0.1, random_state=42)
    return transformer.fit(embed_matrix)


def _pca_fit(embed_matrix: np.ndarray):
    """3-component PCA via SVD — the small-corpus / UMAP-unavailable fallback.
    Returns (basis, s, mean) so new points transform with the same basis:
    coords = (X - mean) @ basis * s. basis is the (d, 3) right-singular-vector
    frame, padded to 3 columns so even a 1-2 chunk session projects cleanly."""
    mean = embed_matrix.mean(axis=0)
    centered = embed_matrix - mean
    _, s, vt = np.linalg.svd(centered, full_matrices=False)
    basis = vt.T[:, :3]  # right singular vectors: (d, 3)
    if basis.shape[1] < 3:
        basis = np.hstack([basis, np.zeros((basis.shape[0], 3 - basis.shape[1]))])
        s = np.pad(s, (0, max(0, 3 - len(s))))
    return basis, s[:3], mean


def _normalize(coords: np.ndarray) -> tuple:
    """Center + scale coordinates into [-BOUND, BOUND]; returns (offset, scale)."""
    offset = coords.mean(axis=0)
    span = np.abs(coords - offset).max() or 1.0
    return offset, span


def _cluster_points(points: List[dict], max_clusters: int = 800) -> List[dict]:
    """Grid-bin the normalized coordinates into representative cluster markers
    (centroid position, count, nearest chunk as the clickable representative)."""
    coords = np.array([[p["x"], p["y"], p["z"]] for p in points])
    cells = max(2, int(round(max_clusters ** (1 / 3))))
    mins = coords.min(axis=0)
    span = np.maximum(coords.max(axis=0) - mins, 1e-9)
    cell_idx = np.floor((coords - mins) / span * (cells - 1e-6)).astype(int)
    groups: Dict[tuple, List[int]] = {}
    for i, key in enumerate(map(tuple, cell_idx)):
        groups.setdefault(key, []).append(i)
    clusters = []
    for members in groups.values():
        centroid = coords[members].mean(axis=0)
        rep = min(members, key=lambda i: float(np.sum((coords[i] - centroid) ** 2)))
        filename_counts: Dict[str, int] = {}
        for i in members:
            filename_counts[points[i]["filename"]] = filename_counts.get(points[i]["filename"], 0) + 1
        clusters.append({
            "id": points[rep]["id"],
            "x": round(float(centroid[0]), 4),
            "y": round(float(centroid[1]), 4),
            "z": round(float(centroid[2]), 4),
            "filename": max(filename_counts, key=filename_counts.get),
            "count": len(members),
        })
    return clusters


def get_space(session_id: str, force: bool = False) -> dict:
    """Project every chunk in the session to 3D (cached per document set).

    Returns {method, embedder, point_count, clustered, threshold, points} where
    each point is {id, x, y, z, filename, chunk_index, count?}.
    """
    session = get_session_vectors(session_id)
    collection = session["collection"]
    got = collection.get(include=["embeddings", "metadatas"])
    ids: List[str] = list(got["ids"])
    if not ids:
        raise ValueError("Session has no indexed chunks — upload a document first")

    fp = _fingerprint(session_id)
    cached = session.get("space")
    if cached and cached.get("fingerprint") == fp and not force:
        return cached

    embed_matrix = np.array(got["embeddings"], dtype="float64")
    n = len(ids)
    method = "umap"
    try:
        if n < 6:
            raise ValueError("corpus too small for UMAP")  # -> PCA fallback
        transformer = _umap_fit(embed_matrix, n)
        coords = transformer.embedding_
        query_transform = ("umap", transformer, None)
    except Exception:  # noqa: BLE001 - UMAP unavailable or too-small corpus
        method = "pca"
        basis, s, mean = _pca_fit(embed_matrix)
        coords = (embed_matrix - mean) @ basis
        coords = coords * s  # scale components so distances are meaningful
        query_transform = ("pca", None, (basis, s, mean))

    offset, scale = _normalize(coords)
    norm = (coords - offset) / scale * BOUND

    embedder = (got["metadatas"][0] or {}).get("embedder", "unknown")
    points = [
        {
            "id": ids[i],
            "x": round(float(norm[i, 0]), 4),
            "y": round(float(norm[i, 1]), 4),
            "z": round(float(norm[i, 2]), 4),
            "filename": got["metadatas"][i].get("filename", ""),
            "chunk_index": i,
        }
        for i in range(n)
    ]

    clustered = False
    if n > UMAP_CLUSTER_THRESHOLD:
        points = _cluster_points(points)
        clustered = True

    space = {
        "fingerprint": fp,
        "method": method,
        "embedder": embedder,
        "point_count": n,
        "clustered": clustered,
        "threshold": UMAP_CLUSTER_THRESHOLD,
        "points": points,
        "_transform": query_transform,
        "_normalize": (offset.tolist(), float(scale)),
        "_n": n,
    }
    session["space"] = space
    return space


def transform_query(session_id: str, query: str) -> dict:
    """Drop a query embedding into the existing (cached) map — the only
    per-query computation. Returns {point: {x,y,z}, method}."""
    space = get_space(session_id)
    query_embedding = embed_chunks([query])[0]
    kind, transformer, pca_params = space["_transform"]
    if kind == "umap":
        raw = transformer.transform(np.array([query_embedding], dtype="float64"))[0]
    else:
        basis, s, mean = pca_params
        raw = ((query_embedding - mean) @ basis) * s
    offset, scale = space["_normalize"]
    point = ((np.asarray(raw, dtype="float64") - np.asarray(offset)) / scale * BOUND).tolist()
    # UMAP .transform() is approximate and can extrapolate outside the fitted
    # range; clamp per axis (monotonic, so neighborhoods are preserved) so the
    # marker always renders inside the view.
    point = np.clip(point, -BOUND * 1.1, BOUND * 1.1).tolist()
    return {
        "method": space["method"],
        "point": {
            "x": round(float(point[0]), 4),
            "y": round(float(point[1]), 4),
            "z": round(float(point[2]), 4),
        },
    }
