"""
LEATrace Blockchain Intelligence — Neo4j Graph Intelligence Service.

Enterprise graph operations: centrality analysis, influence scoring,
link prediction, multi-hop investigation, risk propagation,
knowledge graph construction, and community detection.
"""

import os
import logging
from typing import List, Dict, Any, Optional

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

logger = logging.getLogger("leatrace.neo4j")

# Valid node labels (whitelist to prevent Cypher injection)
VALID_NODE_LABELS = frozenset({"Wallet", "SmartContract", "Token", "NFT", "Entity", "Evidence", "Case"})


class Neo4jGraphService:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "")
        self.driver = None
        self._connected = False

        if not NEO4J_AVAILABLE:
            logger.info("Neo4j driver not installed. Graph features unavailable.")
            return

        if not self.password:
            logger.warning(
                "NEO4J_PASSWORD not set. Neo4j connection will not be attempted. "
                "Set NEO4J_PASSWORD environment variable to enable graph features."
            )
            return

        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with self.driver.session() as session:
                session.run("RETURN 1")
            self._connected = True
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            self._connected = False
            logger.warning(f"Neo4j connection failed: {e}. Graph features unavailable.")

    def is_connected(self) -> bool:
        return self._connected

    def close(self):
        if self.driver:
            self.driver.close()

    def execute_cypher(self, query: str, parameters: Optional[dict] = None) -> List[Dict[str, Any]]:
        if not self._connected:
            return []
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    # ===================================================================
    # Core CRUD Operations
    # ===================================================================

    def add_wallet_node(self, address: str, label: str, risk_score: int, is_contract: bool):
        if not self._connected:
            return
        node_label = "SmartContract" if is_contract else "Wallet"
        if node_label not in VALID_NODE_LABELS:
            logger.error(f"Invalid node label: {node_label}")
            return
        # Use parameterized query — label is whitelisted, not user input
        query = (
            f"MERGE (n:{node_label} {{address: $address}}) "
            "SET n.label = $label, n.risk_score = $risk_score"
        )
        self.execute_cypher(query, {"address": address.lower().strip(), "label": label, "risk_score": risk_score})

    def add_transaction_edge(self, from_addr: str, to_addr: str, tx_hash: str, value: float, chain: str):
        if not self._connected:
            return
        query = (
            "MATCH (u {address: $from_addr}), (v {address: $to_addr}) "
            "CREATE (u)-[r:TRANSACTION {hash: $tx_hash, value: $value, chain: $chain}]->(v)"
        )
        self.execute_cypher(query, {
            "from_addr": from_addr.lower(), "to_addr": to_addr.lower(),
            "tx_hash": tx_hash, "value": value, "chain": chain
        })

    def migrate_from_networkx(self, nx_graph: Any, confirm_delete: bool = False):
        """Copies nodes and edges from an existing NetworkX graph into Neo4j.

        WARNING: This deletes all existing graph data before migration.
        Set confirm_delete=True to proceed.
        """
        if not self._connected:
            return
        if not confirm_delete:
            logger.error("migrate_from_networkx requires confirm_delete=True to proceed (destructive operation)")
            return

        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            for node, attrs in nx_graph.nodes(data=True):
                label = "SmartContract" if attrs.get("is_contract") else "Wallet"
                if label not in VALID_NODE_LABELS:
                    continue
                session.run(
                    f"MERGE (n:{label} {{address: $address}}) "
                    "SET n.risk_score = $risk_score, n.label = $label",
                    address=str(node),
                    risk_score=attrs.get("risk_score", 0),
                    label=attrs.get("label", "Unknown")
                )
            for u, v, attrs in nx_graph.edges(data=True):
                session.run(
                    "MATCH (u {address: $u}), (v {address: $v}) "
                    "CREATE (u)-[r:TRANSACTION {hash: $hash, value: $value, chain: $chain}]->(v)",
                    u=str(u), v=str(v),
                    hash=attrs.get("hash", ""), value=float(attrs.get("value", 0.0)),
                    chain=attrs.get("chain", "ethereum")
                )
        logger.info("Completed graph migration from NetworkX.")

    # ===================================================================
    # Path Finding
    # ===================================================================

    def find_shortest_path(self, start_addr: str, end_addr: str) -> List[Dict[str, Any]]:
        """Finds shortest transaction hop path between two addresses."""
        if not self._connected:
            return []
        query = (
            "MATCH (start {address: $start}), (end {address: $end}), "
            "p = shortestPath((start)-[*..10]->(end)) "
            "RETURN nodes(p) as path_nodes, relationships(p) as path_relationships"
        )
        res = self.execute_cypher(query, {"start": start_addr.lower(), "end": end_addr.lower()})
        if not res:
            return []

        path = []
        record = res[0]
        nodes = record.get("path_nodes", [])
        rels = record.get("path_relationships", [])
        for idx, node in enumerate(nodes):
            path.append({"type": "node", "address": node["address"], "label": node.get("label", ""), "risk_score": node.get("risk_score", 0)})
            if idx < len(rels):
                rel = rels[idx]
                path.append({"type": "edge", "hash": rel["hash"], "value": rel["value"], "chain": rel["chain"]})
        return path

    def find_all_paths(self, start_addr: str, end_addr: str, max_depth: int = 6) -> List[List[Dict[str, Any]]]:
        """Finds all paths between two addresses up to max_depth."""
        if not self._connected:
            return []
        query = (
            "MATCH (start {address: $start}), (end {address: $end}), "
            f"p = allShortestPaths((start)-[*..{max_depth}]->(end)) "
            "RETURN [n IN nodes(p) | n.address] as path LIMIT 10"
        )
        res = self.execute_cypher(query, {"start": start_addr.lower(), "end": end_addr.lower()})
        return [{"path": r.get("path", []), "hop_count": len(r.get("path", [])) - 1} for r in res]

    # ===================================================================
    # Centrality Analysis
    # ===================================================================

    def get_degree_centrality(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns nodes with highest degree centrality (most connections)."""
        if not self._connected:
            return []
        query = (
            "MATCH (n)-[r]-() "
            "RETURN n.address as address, n.label as label, n.risk_score as risk_score, "
            "count(r) as degree "
            "ORDER BY degree DESC LIMIT $limit"
        )
        return self.execute_cypher(query, {"limit": limit})

    def get_betweenness_centrality(self, address: str) -> Dict[str, Any]:
        """Estimates betweenness centrality for a specific address."""
        if not self._connected:
            return {"address": address, "betweenness": 0, "note": "neo4j_offline"}
        # Approximation: count paths passing through this node
        query = (
            "MATCH (n {address: $addr}) "
            "OPTIONAL MATCH (a)-[:TRANSACTION*1..3]->(n)-[:TRANSACTION*1..3]->(b) "
            "WHERE a <> b AND a <> n AND b <> n "
            "RETURN n.address as address, count(DISTINCT a) + count(DISTINCT b) as path_involvement"
        )
        res = self.execute_cypher(query, {"addr": address.lower()})
        if res:
            return {
                "address": address,
                "betweenness_estimate": res[0].get("path_involvement", 0),
                "is_bottleneck": res[0].get("path_involvement", 0) > 10,
            }
        return {"address": address, "betweenness_estimate": 0}

    # ===================================================================
    # Influence & Community
    # ===================================================================

    def get_influence_score(self, address: str) -> Dict[str, Any]:
        """Computes influence score based on connections and their risk levels."""
        if not self._connected:
            return {"address": address, "influence_score": 0, "note": "neo4j_offline"}
        query = (
            "MATCH (n {address: $addr})-[:TRANSACTION]-(neighbor) "
            "RETURN n.address as address, n.risk_score as risk_score, "
            "count(neighbor) as neighbors, "
            "avg(neighbor.risk_score) as avg_neighbor_risk, "
            "max(neighbor.risk_score) as max_neighbor_risk"
        )
        res = self.execute_cypher(query, {"addr": address.lower()})
        if not res:
            return {"address": address, "influence_score": 0}

        record = res[0]
        neighbors = record.get("neighbors", 0)
        avg_risk = record.get("avg_neighbor_risk", 0) or 0
        own_risk = record.get("risk_score", 0) or 0

        # Influence = connections × risk impact
        influence = min(int(neighbors * 3 + own_risk * 0.5 + avg_risk * 0.3), 100)
        return {
            "address": address,
            "influence_score": influence,
            "neighbor_count": neighbors,
            "own_risk_score": own_risk,
            "avg_neighbor_risk": round(float(avg_risk), 1),
            "max_neighbor_risk": record.get("max_neighbor_risk", 0),
            "is_influential": influence > 50,
        }

    def get_community_detection(self) -> List[Dict[str, Any]]:
        """Identifies suspect clusters using degree-based community grouping."""
        if not self._connected:
            return []
        query = (
            "MATCH (n)-[:TRANSACTION]->(m) "
            "RETURN n.address as wallet, n.risk_score as risk_score, "
            "count(m) as degree, collect(m.address)[..5] as peers "
            "ORDER BY degree DESC LIMIT 20"
        )
        return self.execute_cypher(query)

    # ===================================================================
    # Risk Propagation
    # ===================================================================

    def propagate_risk(self, address: str, max_hops: int = 3) -> List[Dict[str, Any]]:
        """Propagates risk from a high-risk node to its neighbors."""
        if not self._connected:
            return []
        query = (
            f"MATCH (source {{address: $addr}})-[:TRANSACTION*1..{max_hops}]-(neighbor) "
            "WHERE neighbor.address <> $addr "
            "RETURN DISTINCT neighbor.address as address, neighbor.label as label, "
            "neighbor.risk_score as current_risk, "
            "length(shortestPath((source)-[*]-(neighbor))) as distance "
            "ORDER BY distance ASC LIMIT 30"
        )
        results = self.execute_cypher(query, {"addr": address.lower()})

        # Calculate propagated risk
        propagated = []
        for r in results:
            distance = r.get("distance", 1)
            current_risk = r.get("current_risk", 0) or 0
            # Risk decays with distance: 70% at hop 1, 40% at hop 2, 20% at hop 3
            decay = max(0.7 - (distance - 1) * 0.25, 0.1)
            propagated_risk = min(int(current_risk + 50 * decay), 100)
            propagated.append({
                "address": r["address"],
                "label": r.get("label", ""),
                "current_risk": current_risk,
                "propagated_risk": propagated_risk,
                "distance_hops": distance,
                "decay_factor": round(decay, 2),
            })

        return propagated

    # ===================================================================
    # Multi-hop Investigation
    # ===================================================================

    def investigate_neighborhood(self, address: str, depth: int = 2) -> Dict[str, Any]:
        """Returns the N-hop neighborhood of an address for investigation."""
        if not self._connected:
            return {"address": address, "nodes": [], "edges": [], "note": "neo4j_offline"}
        query = (
            f"MATCH (source {{address: $addr}})-[r:TRANSACTION*1..{depth}]-(neighbor) "
            "RETURN DISTINCT neighbor.address as address, neighbor.label as label, "
            "neighbor.risk_score as risk_score "
            "LIMIT 50"
        )
        nodes = self.execute_cypher(query, {"addr": address.lower()})

        edge_query = (
            f"MATCH (source {{address: $addr}})-[r:TRANSACTION*1..{depth}]-(n) "
            "WITH n MATCH (n)-[e:TRANSACTION]->(m) "
            "RETURN DISTINCT n.address as from_addr, m.address as to_addr, "
            "e.value as value, e.chain as chain LIMIT 100"
        )
        edges = self.execute_cypher(edge_query, {"addr": address.lower()})

        return {
            "address": address,
            "depth": depth,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
        }

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Returns global graph statistics."""
        if not self._connected:
            return {"status": "offline"}
        node_count = self.execute_cypher("MATCH (n) RETURN count(n) as count")
        edge_count = self.execute_cypher("MATCH ()-[r]->() RETURN count(r) as count")
        high_risk = self.execute_cypher("MATCH (n) WHERE n.risk_score > 60 RETURN count(n) as count")

        return {
            "total_nodes": node_count[0]["count"] if node_count else 0,
            "total_edges": edge_count[0]["count"] if edge_count else 0,
            "high_risk_nodes": high_risk[0]["count"] if high_risk else 0,
            "status": "connected",
        }


neo4j_graph = Neo4jGraphService()
