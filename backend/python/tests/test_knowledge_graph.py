"""Tests for entity extraction and knowledge graph modules.

Run from backend/python:  .venv/bin/python -m pytest tests/test_knowledge_graph.py -v
Hermetic: no network, no LLM keys, no ChromaDB — pure unit tests on the
entity extraction and graph construction logic.
"""

import pytest

from app.entities import Entity, extract_entities, extract_entities_batch
from app.knowledge_graph import (
    build_graph_from_chunks,
    query_graph,
    get_full_graph,
    _make_node_id,
    _infer_relationship,
)


# ---------- Entity Extraction ----------


class TestEntityExtraction:
    """Regex-based entity extraction from text."""

    def test_monetary_values(self):
        text = "Atlas costs $49 per user. Enterprise is $1,500 annually."
        ents = extract_entities(text)
        monetary = [e for e in ents if e.label == "MONETARY"]
        texts = [e.text for e in monetary]
        assert "$49" in texts
        assert "$1,500" in texts

    def test_percentages(self):
        text = "The platform offers 99.99 percent uptime. Discount is 20%."
        ents = extract_entities(text)
        pcts = [e for e in ents if e.label == "PERCENTAGE"]
        texts = [e.text for e in pcts]
        assert "99.99 percent" in texts
        assert "20%" in texts

    def test_dates_iso(self):
        text = "The contract was signed on 2024-01-15 and expires 2025/06/30."
        ents = extract_entities(text)
        dates = [e for e in ents if e.label == "DATE"]
        texts = [e.text for e in dates]
        assert "2024-01-15" in texts
        assert "2025/06/30" in texts

    def test_dates_written(self):
        text = "Published on January 15, 2024. Updated 15 March 2024."
        ents = extract_entities(text)
        dates = [e for e in ents if e.label == "DATE"]
        texts = [e.text for e in dates]
        assert any("January" in t for t in texts)
        assert any("March" in t for t in texts)

    def test_technical_ids(self):
        text = "Equipment EQ-1001 failed. Permit PRM-2026-5000 was issued."
        ents = extract_entities(text)
        ids = [e for e in ents if e.label == "TECHNICAL_ID"]
        texts = [e.text for e in ids]
        assert "EQ-1001" in texts
        assert "PRM-2026-5000" in texts

    def test_proper_nouns_multi_word(self):
        text = "Aurora Labs integrates with Microsoft Teams."
        ents = extract_entities(text)
        pns = [e for e in ents if e.label == "PROPER_NOUN"]
        texts = [e.text for e in pns]
        assert "Aurora Labs" in texts
        assert "Microsoft Teams" in texts

    def test_proper_nouns_single_word(self):
        # Words after sentence boundaries (. ! ?) are matched as single-word proper nouns
        text = "Atlas platform costs $49. Beacon is a service."
        ents = extract_entities(text)
        pns = [e for e in ents if e.label == "PROPER_NOUN"]
        texts = [e.text for e in pns]
        assert "Atlas" in texts
        assert "Beacon" in texts

    def test_stopwords_excluded(self):
        """Common words like 'The', 'A', 'And' should NOT be extracted as entities."""
        text = "The quick brown fox jumps over the lazy dog."
        ents = extract_entities(text)
        pns = [e for e in ents if e.label == "PROPER_NOUN"]
        texts = [e.text.lower() for e in pns]
        assert "the" not in texts
        assert "quick" not in texts  # not after sentence boundary

    def test_no_garbage_entities(self):
        """Entities should not start with punctuation like '. '"""
        text = "Atlas costs $49. Beacon integrates with Slack."
        ents = extract_entities(text)
        for e in ents:
            assert not e.text.startswith("."), f"Garbage entity: {e.text}"
            assert not e.text.startswith("!"), f"Garbage entity: {e.text}"

    def test_regulation_not_false_match(self):
        """AES-256 should NOT be tagged as REGULATION."""
        text = "Data is encrypted with AES-256 and TLS 1.3."
        ents = extract_entities(text)
        regs = [e for e in ents if e.label == "REGULATION"]
        texts = [e.text for e in regs]
        assert "AES-256" not in texts
        assert "TLS" not in texts

    def test_version_requires_prefix(self):
        """VERSION should require 'v' or 'version' prefix, not match standalone decimals."""
        text = "Version 3.0 is available. The uptime is 99.99 percent."
        ents = extract_entities(text)
        vers = [e for e in ents if e.label == "VERSION"]
        pcts = [e for e in ents if e.label == "PERCENTAGE"]
        # "99.99" should be PERCENTAGE, not VERSION
        assert any("99.99" in e.text for e in pcts)
        assert not any("99.99" in e.text for e in vers)

    def test_quoted_strings(self):
        text = 'The system is called "Aurora" and nicknamed \'The Beast\'.'
        ents = extract_entities(text)
        quoted = [e for e in ents if e.label == "QUOTED"]
        texts = [e.text for e in quoted]
        assert "Aurora" in texts
        assert "The Beast" in texts

    def test_section_references(self):
        text = "See Section 36 for details. Also Section 3.2.1 applies."
        ents = extract_entities(text)
        refs = [e for e in ents if e.label == "SECTION_REF"]
        texts = [e.text for e in refs]
        assert "Section 36" in texts
        assert "Section 3.2.1" in texts

    def test_deduplication(self):
        """Same entity appearing twice should be deduplicated."""
        text = "Atlas costs $49. Later, Atlas is mentioned again at $49."
        ents = extract_entities(text, dedupe=True)
        monetary = [e for e in ents if e.label == "MONETARY"]
        # $49 appears twice but should be deduplicated
        assert len([e for e in monetary if e.text == "$49"]) == 1

    def test_empty_text(self):
        ents = extract_entities("")
        assert ents == []

    def test_entity_positions(self):
        """Entity positions should be correct relative to the text."""
        text = "Atlas costs $49 per month."
        ents = extract_entities(text)
        for e in ents:
            assert text[e.start:e.end] == e.text, f"Position mismatch for {e.text}"

    def test_batch_extraction(self):
        texts = ["Atlas costs $49.", "Beacon costs $19."]
        results = extract_entities_batch(texts)
        assert len(results) == 2
        for text, ents in results.items():
            assert len(ents) > 0

    def test_entity_to_dict(self):
        e = Entity(text="Atlas", label="PROPER_NOUN", start=0, end=5)
        d = e.to_dict()
        assert d["text"] == "Atlas"
        assert d["label"] == "PROPER_NOUN"
        assert d["start"] == 0
        assert d["end"] == 5
        assert d["confidence"] == 1.0


# ---------- Knowledge Graph ----------


SAMPLE_CHUNKS = [
    {
        "id": "c0",
        "text": "Atlas costs $49 per user per month. Beacon costs $19 per user per month and integrates with Slack.",
        "filename": "products.csv",
    },
    {
        "id": "c1",
        "text": "Nimbus Enterprise adds private networking and a 99.99 percent uptime commitment.",
        "filename": "products.csv",
    },
    {
        "id": "c2",
        "text": "Aurora Labs holds SOC 2 Type II certification and encrypts data with AES-256. GDPR compliant.",
        "filename": "security.txt",
    },
    {
        "id": "c3",
        "text": "All Aurora Labs products are billed monthly. Annual billing is available at a 20 percent discount.",
        "filename": "pricing.md",
    },
]


class TestKnowledgeGraph:
    """NetworkX knowledge graph construction and query."""

    def test_build_graph_returns_networkx(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        import networkx as nx
        assert isinstance(G, nx.Graph)

    def test_graph_has_nodes(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        assert G.number_of_nodes() > 0

    def test_graph_has_edges(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        assert G.number_of_edges() > 0

    def test_graph_node_attributes(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        for nid, data in G.nodes(data=True):
            assert "text" in data
            assert "entity_type" in data
            assert "source_chunks" in data
            assert "source_documents" in data
            assert "count" in data

    def test_graph_edge_attributes(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        for u, v, data in G.edges(data=True):
            assert "weight" in data
            assert "relationship" in data
            assert "shared_chunks" in data
            assert data["weight"] >= 1

    def test_graph_co_occurrence(self):
        """Entities in the same chunk should be connected."""
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        # Atlas and $49 are in the same chunk (c0)
        atlas_id = _make_node_id("Atlas", "PROPER_NOUN")
        price_id = _make_node_id("$49", "MONETARY")
        assert G.has_edge(atlas_id, price_id)

    def test_graph_cross_chunk_no_edge(self):
        """Entities in different chunks should NOT be directly connected."""
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        # Atlas (c0) and AES-256 (c2) are in different chunks
        atlas_id = _make_node_id("Atlas", "PROPER_NOUN")
        aes_id = _make_node_id("AES-256", "TECHNICAL_ID")
        assert not G.has_edge(atlas_id, aes_id)

    def test_relationship_inference(self):
        assert _infer_relationship("PROPER_NOUN", "MONETARY") == "has_value"
        assert _infer_relationship("MONETARY", "PROPER_NOUN") == "has_value"
        assert _infer_relationship("PROPER_NOUN", "TECHNICAL_ID") == "associated_with"
        assert _infer_relationship("PROPER_NOUN", "PERCENTAGE") == "has_percentage"
        assert _infer_relationship("PROPER_NOUN", "DATE") == "dated"
        assert _infer_relationship("PROPER_NOUN", "PROPER_NOUN") == "co_occurs"

    def test_empty_chunks(self):
        G = build_graph_from_chunks([])
        assert G.number_of_nodes() == 0
        assert G.number_of_edges() == 0

    def test_empty_text_chunks(self):
        G = build_graph_from_chunks([{"id": "c0", "text": "", "filename": "empty.txt"}])
        assert G.number_of_nodes() == 0

    def test_get_full_graph(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        result = get_full_graph(G)
        assert len(result.nodes) > 0
        assert len(result.edges) > 0
        assert "total_nodes" in result.stats
        assert "total_edges" in result.stats
        assert "entity_type_counts" in result.stats

    def test_get_full_graph_caps_at_max_nodes(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        result = get_full_graph(G, max_nodes=3)
        assert len(result.nodes) <= 3

    def test_query_graph_finds_matching_entities(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        result = query_graph(G, ["Atlas"])
        assert result.query_entities
        assert "Atlas" in result.query_entities

    def test_query_graph_expands_to_neighbors(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        result = query_graph(G, ["Atlas"])
        # Atlas should have neighbors (e.g., $49, Beacon)
        assert len(result.nodes) > 1  # Atlas + at least one neighbor

    def test_query_graph_empty_query(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        result = query_graph(G, ["nonexistent_entity_xyz"])
        assert len(result.nodes) == 0
        assert result.query_entities == []

    def test_query_graph_max_nodes_limit(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        result = query_graph(G, ["Aurora"], max_nodes=2)
        assert len(result.nodes) <= 2

    def test_graph_node_id_stability(self):
        """Same text + type should produce the same node ID."""
        id1 = _make_node_id("Atlas", "PROPER_NOUN")
        id2 = _make_node_id("Atlas", "PROPER_NOUN")
        assert id1 == id2
        # Different type = different ID
        id3 = _make_node_id("Atlas", "MONETARY")
        assert id1 != id3

    def test_graph_result_to_dict(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        result = get_full_graph(G)
        d = result.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert "stats" in d
        assert isinstance(d["nodes"], list)
        assert isinstance(d["edges"], list)
        for node in d["nodes"]:
            assert "id" in node
            assert "label" in node
            assert "entity_type" in node

    def test_graph_stats_entity_type_counts(self):
        G = build_graph_from_chunks(SAMPLE_CHUNKS)
        result = get_full_graph(G)
        counts = result.stats["entity_type_counts"]
        assert "PROPER_NOUN" in counts
        assert counts["PROPER_NOUN"] > 0

    def test_graph_single_chunk(self):
        """A single chunk should still produce a valid graph."""
        chunks = [{"id": "c0", "text": "Atlas costs $49. Beacon is $19.", "filename": "test.txt"}]
        G = build_graph_from_chunks(chunks)
        assert G.number_of_nodes() >= 2
        assert G.number_of_edges() >= 1
