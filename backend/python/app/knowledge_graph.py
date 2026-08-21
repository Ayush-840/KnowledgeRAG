"""Knowledge graph construction and query using NetworkX.

Builds a typed, attributed graph from extracted entities and their co-occurrence
within document chunks.  Nodes represent entities (with label, source chunk,
document); edges represent co-occurrence within the same chunk (weighted by
frequency).

The graph is per-session and rebuilt from the ChromaDB collection on demand.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import networkx as nx

from .entities import Entity, extract_entities


@dataclass
class GraphNode:
    id: str
    label: str
    entity_type: str
    source_chunks: list[str] = field(default_factory=list)
    source_documents: list[str] = field(default_factory=list)
    count: int = 1

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GraphEdge:
    source: str
    target: str
    weight: float = 1.0
    relationship: str = "co_occurs"
    shared_chunks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GraphResult:
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    stats: dict
    query_entities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "stats": self.stats,
            "query_entities": self.query_entities,
        }


def _make_node_id(text: str, entity_type: str) -> str:
    """Stable node id: lowercased text + type."""
    return f"{entity_type}:{text.lower().strip()}"


def build_graph_from_chunks(chunks: list[dict]) -> nx.Graph:
    """Build a NetworkX graph from ingested chunks.

    Each chunk dict should have: {id, text, filename, ...}.
    Entities are extracted from each chunk, and co-occurring entities within
    the same chunk are connected with weighted edges.
    """
    G = nx.Graph()

    # Extract entities per chunk
    chunk_entities: dict[str, list[Entity]] = {}
    for chunk in chunks:
        text = chunk.get("text", "")
        if not text:
            continue
        ents = extract_entities(text, dedupe=True)
        if ents:
            chunk_entities[chunk["id"]] = ents

    # Aggregate entity counts and source mappings
    entity_info: dict[str, dict] = {}  # node_id -> {text, type, chunks, docs, count}
    for chunk_id, ents in chunk_entities.items():
        chunk = next((c for c in chunks if c["id"] == chunk_id), None)
        if not chunk:
            continue
        filename = chunk.get("filename", "unknown")

        for ent in ents:
            nid = _make_node_id(ent.text, ent.label)
            if nid not in entity_info:
                entity_info[nid] = {
                    "text": ent.text,
                    "type": ent.label,
                    "chunks": set(),
                    "docs": set(),
                    "count": 0,
                }
            entity_info[nid]["chunks"].add(chunk_id)
            entity_info[nid]["docs"].add(filename)
            entity_info[nid]["count"] += 1

    # Add nodes to graph
    for nid, info in entity_info.items():
        G.add_node(nid, **{
            "text": info["text"],
            "entity_type": info["type"],
            "source_chunks": list(info["chunks"]),
            "source_documents": list(info["docs"]),
            "count": info["count"],
        })

    # Build edges: co-occurrence within the same chunk
    edge_weights: dict[tuple[str, str], dict] = defaultdict(lambda: {"weight": 0, "chunks": set()})
    for chunk_id, ents in chunk_entities.items():
        # Only connect distinct entity types (avoid self-loops and same-type clutter)
        unique_nids = list({_make_node_id(e.text, e.label) for e in ents})
        for i, nid_a in enumerate(unique_nids):
            for nid_b in unique_nids[i + 1:]:
                # Sort to make undirected edge canonical
                edge_key = tuple(sorted([nid_a, nid_b]))
                edge_weights[edge_key]["weight"] += 1
                edge_weights[edge_key]["chunks"].add(chunk_id)

    for (nid_a, nid_b), info in edge_weights.items():
        # Determine relationship type from entity types
        type_a = G.nodes[nid_a].get("entity_type", "")
        type_b = G.nodes[nid_b].get("entity_type", "")
        rel = _infer_relationship(type_a, type_b)

        G.add_edge(nid_a, nid_b, **{
            "weight": info["weight"],
            "relationship": rel,
            "shared_chunks": list(info["chunks"]),
        })

    return G


def _infer_relationship(type_a: str, type_b: str) -> str:
    """Infer a human-readable relationship label from entity types."""
    pair = frozenset([type_a, type_b])
    if "PROPER_NOUN" in pair and "TECHNICAL_ID" in pair:
        return "associated_with"
    if "MONETARY" in pair and "PROPER_NOUN" in pair:
        return "has_value"
    if "REGULATION" in pair and "PROPER_NOUN" in pair:
        return "regulated_by"
    if "DATE" in pair and "PROPER_NOUN" in pair:
        return "dated"
    if "PERCENTAGE" in pair and "PROPER_NOUN" in pair:
        return "has_percentage"
    if "DURATION" in pair and "PROPER_NOUN" in pair:
        return "has_duration"
    return "co_occurs"


def query_graph(G: nx.Graph, query_entities: list[str], *, max_nodes: int = 50) -> GraphResult:
    """Query the knowledge graph for subgraph relevant to query entities.

    Finds nodes matching any of the query entities, then expands to their
    1-hop neighbors.  Returns the most connected subgraph up to *max_nodes*.
    """
    # Find matching nodes
    matched: set[str] = set()
    for qe in query_entities:
        qe_lower = qe.lower().strip()
        for nid, data in G.nodes(data=True):
            if qe_lower in data.get("text", "").lower():
                matched.add(nid)

    # Expand to 1-hop neighbors
    expanded: set[str] = set(matched)
    for nid in matched:
        expanded.update(G.neighbors(nid))

    # Limit to most-connected nodes if too large
    if len(expanded) > max_nodes:
        # Sort by degree, keep top N
        node_degrees = [(n, G.degree(n)) for n in expanded]
        node_degrees.sort(key=lambda x: x[1], reverse=True)
        expanded = {n for n, _ in node_degrees[:max_nodes]}

    # Build subgraph
    subgraph = G.subgraph(expanded)

    nodes = []
    for nid, data in subgraph.nodes(data=True):
        nodes.append(GraphNode(
            id=nid,
            label=data.get("text", nid),
            entity_type=data.get("entity_type", "UNKNOWN"),
            source_chunks=data.get("source_chunks", []),
            source_documents=data.get("source_documents", []),
            count=data.get("count", 1),
        ))

    edges = []
    for u, v, data in subgraph.edges(data=True):
        edges.append(GraphEdge(
            source=u,
            target=v,
            weight=data.get("weight", 1.0),
            relationship=data.get("relationship", "co_occurs"),
            shared_chunks=data.get("shared_chunks", []),
        ))

    stats = {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "subgraph_nodes": subgraph.number_of_nodes(),
        "subgraph_edges": subgraph.number_of_edges(),
        "query_entities_found": len(matched),
        "entity_type_counts": _count_entity_types(subgraph),
    }

    return GraphResult(
        nodes=nodes,
        edges=edges,
        stats=stats,
        query_entities=[n.label for n in nodes if n.id in matched],
    )


def get_full_graph(G: nx.Graph, *, max_nodes: int = 100) -> GraphResult:
    """Return the full graph (capped at *max_nodes* by degree)."""
    if G.number_of_nodes() > max_nodes:
        top = sorted(G.nodes(), key=lambda n: G.degree(n), reverse=True)[:max_nodes]
        subgraph = G.subgraph(top)
    else:
        subgraph = G

    nodes = [
        GraphNode(
            id=nid,
            label=data.get("text", nid),
            entity_type=data.get("entity_type", "UNKNOWN"),
            source_chunks=data.get("source_chunks", []),
            source_documents=data.get("source_documents", []),
            count=data.get("count", 1),
        )
        for nid, data in subgraph.nodes(data=True)
    ]

    edges = [
        GraphEdge(
            source=u,
            target=v,
            weight=data.get("weight", 1.0),
            relationship=data.get("relationship", "co_occurs"),
            shared_chunks=data.get("shared_chunks", []),
        )
        for u, v, data in subgraph.edges(data=True)
    ]

    stats = {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "subgraph_nodes": subgraph.number_of_nodes(),
        "subgraph_edges": subgraph.number_of_edges(),
        "entity_type_counts": _count_entity_types(subgraph),
    }

    return GraphResult(nodes=nodes, edges=edges, stats=stats)


def _count_entity_types(G: nx.Graph) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for _, data in G.nodes(data=True):
        counts[data.get("entity_type", "UNKNOWN")] += 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def graph_to_json(G: nx.Graph) -> str:
    """Serialize graph to JSON string."""
    return json.dumps(nx.node_link_data(G), default=str)


def graph_from_json(json_str: str) -> nx.Graph:
    """Deserialize graph from JSON string."""
    data = json.loads(json_str)
    return nx.node_link_graph(data)
