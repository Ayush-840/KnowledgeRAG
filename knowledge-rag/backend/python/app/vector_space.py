"""3D Vector Space Projection & UMAP Dimensionality Reduction Module.

Projects high-dimensional document chunk embeddings (e.g. 384-dim) into 3D (x, y, z)
coordinates for the 3D Vector Space Explorer UI.

Features:
- Parametric UMAP projection (umap-learn) preserving global/local cluster structures.
- Caching fitted UMAP models per session so query embeddings are transformed (.transform())
  into the existing 3D space in real time (<10 ms) without re-layout jitter.
- Fallback for small corpora (< 3 points) or environments without UMAP.
"""

import os
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# Global in-memory cache for fitted UMAP projections per session
# Format: session_id -> {"model": UMAP, "points": dict, "embeddings": np.ndarray, "doc_ids": list}
_UMAP_CACHE: Dict[str, Dict[str, Any]] = {}


def clear_session_vector_space_cache(session_id: str):
    """Clear cached 3D vector space projection for a session (called after ingest)."""
    _UMAP_CACHE.pop(session_id, None)


def _compute_fallback_3d(embeddings: np.ndarray) -> np.ndarray:
    """Fallback 3D reduction using TruncatedSVD or PCA when UMAP is unavailable
    or point count N < 3.
    """
    n_samples, n_features = embeddings.shape
    if n_samples == 0:
        return np.zeros((0, 3))
    if n_samples == 1:
        return np.array([[0.0, 0.0, 0.0]])
    if n_samples == 2:
        return np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])

    try:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=min(3, n_samples, n_features))
        coords = pca.fit_transform(embeddings)
        if coords.shape[1] < 3:
            padding = np.zeros((n_samples, 3 - coords.shape[1]))
            coords = np.hstack([coords, padding])
        return coords
    except Exception as e:
        logger.warning(f"PCA fallback error: {e}")
        # Return simple normalized slice of first 3 dimensions
        if n_features >= 3:
            return embeddings[:, :3]
        padding = np.zeros((n_samples, 3 - n_features))
        return np.hstack([embeddings, padding])


def get_or_compute_3d_projection(session_id: str, collection) -> Dict[str, Any]:
    """Retrieve or compute 3D UMAP coordinates for all chunks in a session.
    
    Returns dict with:
      "points": list of {"id", "x", "y", "z", "filename", "page_number", "text_snippet"}
      "has_model": bool (whether parametric transform is ready for queries)
    """
    if session_id in _UMAP_CACHE:
        return _UMAP_CACHE[session_id]["projection_data"]

    # Fetch all vectors and metadata from Chroma
    data = collection.get(include=["embeddings", "metadatas", "documents"])
    ids = data.get("ids", [])
    embeddings_raw = data.get("embeddings", [])
    metadatas = data.get("metadatas", [])
    documents = data.get("documents", [])

    if not ids or len(embeddings_raw) == 0:
        res = {"points": [], "has_model": False}
        _UMAP_CACHE[session_id] = {"projection_data": res, "model": None}
        return res

    embeddings = np.array(embeddings_raw, dtype=np.float32)
    n_samples = len(ids)
    model = None
    coords_3d = None

    # Try fitting UMAP if n_samples >= 3
    if n_samples >= 3:
        try:
            import umap
            # Use parametric UMAP with fixed seed for stability
            n_neighbors = min(15, n_samples - 1)
            model = umap.UMAP(
                n_components=3,
                n_neighbors=n_neighbors,
                min_dist=0.1,
                metric="cosine",
                random_state=42,
            )
            coords_3d = model.fit_transform(embeddings)
        except Exception as e:
            logger.warning(f"UMAP fit failed for session {session_id}: {e}")
            model = None

    if coords_3d is None:
        coords_3d = _compute_fallback_3d(embeddings)

    # Normalize coordinates to roughly [-10, 10] box for pleasant rendering
    if len(coords_3d) > 0:
        max_abs = np.max(np.abs(coords_3d))
        if max_abs > 1e-5:
            coords_3d = (coords_3d / max_abs) * 10.0

    points = []
    for i, chunk_id in enumerate(ids):
        meta = metadatas[i] if i < len(metadatas) else {}
        doc_text = documents[i] if i < len(documents) else ""
        snippet = doc_text[:150] + ("..." if len(doc_text) > 150 else "")
        points.append({
            "id": chunk_id,
            "x": round(float(coords_3d[i, 0]), 3),
            "y": round(float(coords_3d[i, 1]), 3),
            "z": round(float(coords_3d[i, 2]), 3),
            "filename": meta.get("filename", "document"),
            "page_number": meta.get("page_number", 1),
            "snippet": snippet,
        })

    projection_data = {"points": points, "has_model": model is not None}
    _UMAP_CACHE[session_id] = {
        "projection_data": projection_data,
        "model": model,
        "embeddings": embeddings,
        "ids": ids,
    }
    return projection_data


def project_query_point(session_id: str, query_embedding: List[float], collection) -> Optional[Dict[str, float]]:
    """Project a query embedding into the session's existing 3D UMAP coordinate space.
    Uses UMAP .transform() when available for instant <10ms positioning without jitter.
    """
    proj_data = get_or_compute_3d_projection(session_id, collection)
    if not proj_data["points"]:
        return None

    cache_item = _UMAP_CACHE.get(session_id)
    query_vec = np.array([query_embedding], dtype=np.float32)

    model = cache_item.get("model") if cache_item else None
    if model is not None:
        try:
            coords = model.transform(query_vec)
            # Apply same normalization scale
            existing_embeddings = cache_item["embeddings"]
            existing_coords = model.transform(existing_embeddings)
            max_abs = np.max(np.abs(existing_coords))
            if max_abs > 1e-5:
                coords = (coords / max_abs) * 10.0
            return {
                "x": round(float(coords[0, 0]), 3),
                "y": round(float(coords[0, 1]), 3),
                "z": round(float(coords[0, 2]), 3),
            }
        except Exception as e:
            logger.warning(f"UMAP query transform error: {e}")

    # Fallback positioning: find nearest neighbor in existing embeddings
    existing_embeddings = cache_item.get("embeddings") if cache_item else None
    if existing_embeddings is not None and len(existing_embeddings) > 0:
        # Cosine similarity to find closest point and place query near it
        norm_q = query_vec / (np.linalg.norm(query_vec) + 1e-9)
        norm_e = existing_embeddings / (np.linalg.norm(existing_embeddings, axis=1, keepdims=True) + 1e-9)
        sims = np.dot(norm_e, norm_q.T).squeeze()
        best_idx = int(np.argmax(sims))
        pt = proj_data["points"][best_idx]
        return {
            "x": round(pt["x"] + 0.5, 3),
            "y": round(pt["y"] + 0.5, 3),
            "z": round(pt["z"] + 0.5, 3),
        }

    return {"x": 0.0, "y": 0.0, "z": 0.0}
