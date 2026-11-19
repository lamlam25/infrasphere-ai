"""Knowledge Graph builder for the Knowledge Grid."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import networkx as nx

    _NX_AVAILABLE = True
except ImportError:
    _NX_AVAILABLE = False
    logger.warning("networkx not installed — KnowledgeGraphBuilder will use a stub graph")


class _StubGraph:
    """Minimal stand-in when networkx is unavailable."""

    def __init__(self):
        self._nodes: Dict[str, Dict] = {}
        self._edges: List[tuple] = []

    def add_node(self, node_id, **attrs):
        self._nodes[node_id] = attrs

    def add_edge(self, src, tgt, **attrs):
        self._edges.append((src, tgt, attrs))

    def has_node(self, node_id):
        return node_id in self._nodes

    def nodes(self, data=False):
        if data:
            return self._nodes.items()
        return self._nodes.keys()

    def edges(self, data=False):
        if data:
            return [(s, t, a) for s, t, a in self._edges]
        return [(s, t) for s, t, _ in self._edges]

    def neighbors(self, node_id):
        return [t for s, t, _ in self._edges if s == node_id]

    def clear(self):
        self._nodes.clear()
        self._edges.clear()


class KnowledgeGraphBuilder:
    """
    Builds and maintains an in-memory directed knowledge graph of:
      - Incidents  (node type: incident)
      - Documents  (node type: document)
      - Assets     (node type: asset)
      - Locations  (node type: location)

    Edges encode relationships such as:
      incident → location (located_in)
      document → incident (references)
      asset    → location (located_in)
    """

    def __init__(self):
        if _NX_AVAILABLE:
            self.G = nx.DiGraph()
        else:
            self.G = _StubGraph()

    # ------------------------------------------------------------------
    # Add nodes
    # ------------------------------------------------------------------

    def add_incident(self, incident: Dict[str, Any]) -> None:
        """Add an incident node and a location edge if district is set."""
        inc_id = incident.get("id") or incident.get("incident_id")
        if not inc_id:
            return
        self.G.add_node(
            inc_id,
            label=incident.get("title", inc_id),
            type="incident",
            severity=incident.get("severity", "unknown"),
            category=incident.get("category", "other"),
            district=incident.get("district", ""),
            status=incident.get("status", ""),
        )
        district = incident.get("district")
        if district:
            loc_id = f"LOC-{district.lower().replace(' ', '_')}"
            self.G.add_node(loc_id, label=district, type="location")
            self.G.add_edge(inc_id, loc_id, relationship="located_in")

    def add_document(self, document: Dict[str, Any], incident_ids: List[str]) -> None:
        """Add a document node and edges to related incidents."""
        doc_id = document.get("id") or document.get("doc_id")
        if not doc_id:
            return
        self.G.add_node(
            doc_id,
            label=document.get("title", doc_id),
            type="document",
            file_type=document.get("file_type", ""),
            status=document.get("status", ""),
        )
        for inc_id in incident_ids or []:
            if self.G.has_node(inc_id):
                self.G.add_edge(doc_id, inc_id, relationship="references")

    def add_asset(self, asset: Dict[str, Any]) -> None:
        """Add an infrastructure asset node."""
        asset_id = asset.get("id") or asset.get("asset_id")
        if not asset_id:
            return
        self.G.add_node(
            asset_id,
            label=asset.get("name", asset_id),
            type="asset",
            asset_type=asset.get("asset_type", "other"),
            district=asset.get("district", ""),
        )
        district = asset.get("district")
        if district:
            loc_id = f"LOC-{district.lower().replace(' ', '_')}"
            if not self.G.has_node(loc_id):
                self.G.add_node(loc_id, label=district, type="location")
            self.G.add_edge(asset_id, loc_id, relationship="located_in")

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_graph_data(
        self, center_id: Optional[str] = None, depth: int = 2
    ) -> Dict[str, Any]:
        """
        Returns {nodes: [{id, label, type, ...}], edges: [{source, target, relationship}]}.

        When center_id is given, returns only the subgraph reachable within
        *depth* hops from that node.
        """
        if center_id and self.G.has_node(center_id):
            if _NX_AVAILABLE:
                reachable = set(nx.single_source_shortest_path(self.G, center_id, cutoff=depth).keys())
                # Also go backwards
                G_rev = self.G.reverse()
                reachable |= set(nx.single_source_shortest_path(G_rev, center_id, cutoff=depth).keys())
                sub_nodes = reachable
            else:
                sub_nodes = {center_id}
                frontier = {center_id}
                for _ in range(depth):
                    next_f = set()
                    for n in frontier:
                        next_f.update(self.G.neighbors(n))
                    sub_nodes |= next_f
                    frontier = next_f
        else:
            sub_nodes = None  # all nodes

        nodes = []
        for node_id, attrs in self.G.nodes(data=True):
            if sub_nodes is not None and node_id not in sub_nodes:
                continue
            nodes.append({"id": node_id, "label": attrs.get("label", node_id), **attrs})

        edges = []
        for src, tgt, attrs in self.G.edges(data=True):
            if sub_nodes is not None and (src not in sub_nodes or tgt not in sub_nodes):
                continue
            edges.append({"source": src, "target": tgt, "relationship": attrs.get("relationship", "related")})

        return {"nodes": nodes, "edges": edges}

    # ------------------------------------------------------------------
    # DB rebuild
    # ------------------------------------------------------------------

    def rebuild_from_db(self, db) -> None:
        """
        Rebuild the in-memory graph from database records on startup.
        Accepts a SQLAlchemy session or connection.
        """
        self.G.clear()
        try:
            from sqlalchemy import text as sa_text

            # Incidents
            rows = db.execute(sa_text("SELECT id, title, category, severity, status, district FROM incidents")).fetchall()
            for row in rows:
                self.add_incident(dict(row._mapping))

            # Documents
            rows = db.execute(sa_text("SELECT id, title, file_type, status FROM documents")).fetchall()
            for row in rows:
                self.add_document(dict(row._mapping), [])

            # Assets
            rows = db.execute(sa_text("SELECT id, name, asset_type, district FROM assets")).fetchall()
            for row in rows:
                self.add_asset(dict(row._mapping))

            logger.info(
                "Knowledge graph rebuilt: %d nodes, %d edges",
                len(list(self.G.nodes())),
                len(list(self.G.edges())),
            )
        except Exception as exc:
            logger.warning("Graph rebuild from DB failed (non-fatal): %s", exc)
