from typing import List, Dict, Any

class CrossChainGraphBuilder:
    def build_flow_graph(self, hops: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Constructs a node-edge graph modeling asset movements across different chain hubs."""
        nodes = []
        edges = []
        
        seen_nodes = set()
        for idx, hop in enumerate(hops):
            src_node = f"node_{hop['source_chain']}_{idx}"
            dst_node = f"node_{hop['destination_chain']}_{idx+1}"
            
            if src_node not in seen_nodes:
                nodes.append({"id": src_node, "label": f"Bridge In ({hop['source_chain']})", "chain": hop["source_chain"]})
                seen_nodes.add(src_node)
            if dst_node not in seen_nodes:
                nodes.append({"id": dst_node, "label": f"Release ({hop['destination_chain']})", "chain": hop["destination_chain"]})
                seen_nodes.add(dst_node)
                
            edges.append({
                "id": f"edge_hop_{idx}",
                "source": src_node,
                "target": dst_node,
                "value": f"{hop['amount_sent']} {hop['token']}"
            })
            
        return {"nodes": nodes, "edges": edges}

cross_chain_graph = CrossChainGraphBuilder()
