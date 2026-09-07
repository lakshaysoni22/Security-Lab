from typing import List, Dict, Any

class AssetFlowEngine:
    def reconstruct_splits(self, transactions: List[Dict[str, Any]], target_address: str) -> List[Dict[str, Any]]:
        """Calculates split percentage outflows from a given target address node."""
        flows = []
        total_outflow = sum(tx.get("value", 0.0) for tx in transactions if tx.get("from", "").lower() == target_address.lower())
        
        if total_outflow <= 0:
            return flows
            
        for tx in transactions:
            if tx.get("from", "").lower() == target_address.lower():
                val = tx.get("value", 0.0)
                pct = (val / total_outflow) * 100.0
                flows.append({
                    "tx_hash": tx.get("hash"),
                    "receiver": tx.get("to"),
                    "value": val,
                    "split_percentage": f"{pct:.2f}%"
                })
        return flows

asset_flow_engine = AssetFlowEngine()
