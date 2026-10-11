from typing import List, Dict, Any, Optional
from app.core.neo4j import neo4j_client
from app.core.logging import logger

NODE_TYPES = [
    "Case",
    "Person",
    "Account",
    "Device",
    "Location",
    "Evidence",
    "Event",
    "VehicleObject"
]

RELATIONSHIP_TYPES = [
    "ASSOCIATED_WITH",
    "USES",
    "LOCATED_AT",
    "APPEARS_IN",
    "MENTIONED_IN",
    "OCCURRED_AT",
    "SUPPORTED_BY",
    "CORRELATES_WITH"
]

class KnowledgeGraphBuilder:
    """Helper class to build, format, and sync Neo4j & in-memory graph structures."""

    @staticmethod
    def create_node(node_id: str, label: str, name: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        valid_label = label if label in NODE_TYPES else "Person"
        props = properties or {}
        return {
            "id": node_id,
            "label": valid_label,
            "name": name,
            "type": valid_label.upper(),
            "properties": props
        }

    @staticmethod
    def create_relationship(
        source_id: str,
        target_id: str,
        rel_type: str,
        confidence: float = 1.0,
        supporting_evidence: Optional[List[Dict[str, Any]]] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        valid_rel = rel_type if rel_type in RELATIONSHIP_TYPES else "ASSOCIATED_WITH"
        props = properties or {}
        evidence_list = supporting_evidence or []

        return {
            "source": source_id,
            "target": target_id,
            "relationship": valid_rel,
            "confidence": round(confidence, 2),
            "supporting_evidence": evidence_list,
            "disclaimer": "Evidence-backed correlation for investigator review. Correlation does not prove identity or guilt.",
            "properties": props
        }

    @staticmethod
    async def sync_to_neo4j(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> bool:
        """Syncs in-memory graph nodes and edges to Neo4j database using Cypher."""
        if not neo4j_client.connected:
            logger.debug("Neo4j not connected. Knowledge graph stored in memory.")
            return False

        try:
            # Sync Nodes
            cypher_nodes = """
            UNWIND $nodes AS n
            MERGE (e:Entity {id: n.id})
            SET e.name = n.name, e.label = n.label, e.type = n.type
            """
            await neo4j_client.execute_cypher(cypher_nodes, {"nodes": nodes})

            # Sync Edges
            cypher_edges = """
            UNWIND $edges AS r
            MATCH (a:Entity {id: r.source})
            MATCH (b:Entity {id: r.target})
            MERGE (a)-[rel:CORRELATES_WITH {type: r.relationship}]->(b)
            SET rel.confidence = r.confidence, rel.disclaimer = r.disclaimer
            """
            await neo4j_client.execute_cypher(cypher_edges, {"edges": edges})

            logger.info(f"Successfully synced {len(nodes)} nodes and {len(edges)} edges to Neo4j.")
            return True
        except Exception as e:
            logger.warning(f"Error syncing to Neo4j: {e}")
            return False
