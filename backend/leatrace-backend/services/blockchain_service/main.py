from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import random
from shared.logger import logger

app = FastAPI(title="Blockchain Intelligence Service", version="1.0.0")

# --- Schemas ---
class TraceRequest(BaseModel):
    address: str
    depth: int = 3

class ConnectionNode(BaseModel):
    from_address: str
    to_address: str
    value: float

class TraceResponse(BaseModel):
    wallet: str
    connections: List[ConnectionNode]
    risk_score: float
    analysis: str

# --- Mock Blockchain Ledger (EVM) ---
MOCK_LEDGER = [
    {"from": "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28", "to": "0x123f72a855f72a855f72a855f72a855f72a855f7", "value": 15.5},
    {"from": "0x123f72a855f72a855f72a855f72a855f72a855f7", "to": "0x456f72a855f72a855f72a855f72a855f72a855f7", "value": 12.0},
    {"from": "0x456f72a855f72a855f72a855f72a855f72a855f7", "to": "0xTornadoCashMixerAddress000000000000000", "value": 10.0},
    {"from": "0xTornadoCashMixerAddress000000000000000", "to": "0x890f72a855f72a855f72a855f72a855f72a855f7", "value": 9.5},
]

try:
    import networkx as nx
    
    def build_network_graph(txs: List[Dict[str, Any]]) -> nx.DiGraph:
        G = nx.DiGraph()
        for tx in txs:
            G.add_edge(tx["from"], tx["to"], weight=tx["value"])
        return G
except ImportError:
    logger.warning("networkx not installed. Fallback to basic dictionary graph structures.")
    build_network_graph = None

def compute_risk(address: str, txs: List[Dict[str, Any]]) -> float:
    score = 0.1
    # Rule 1: Mixer usage
    if any(tx["to"] == "0xTornadoCashMixerAddress000000000000000" or tx["from"] == "0xTornadoCashMixerAddress000000000000000" for tx in txs):
        score += 0.5
    # Rule 2: Tx count
    if len(txs) > 3:
        score += 0.2
    # Rule 3: High value transfers
    if any(tx["value"] > 10.0 for tx in txs):
        score += 0.2
    return min(score, 1.0)

@app.post("/blockchain/trace", response_model=TraceResponse)
def trace(request: TraceRequest):
    logger.info(f"Tracing blockchain wallet address: {request.address} at depth {request.depth}")
    
    # Filter related transaction paths
    related_txs = []
    visited = set()
    queue = [(request.address, 0)]
    
    while queue:
        curr_addr, curr_depth = queue.pop(0)
        if curr_depth >= request.depth or curr_addr in visited:
            continue
        visited.add(curr_addr)
        
        for tx in MOCK_LEDGER:
            if tx["from"] == curr_addr:
                related_txs.append(tx)
                queue.append((tx["to"], curr_depth + 1))
            elif tx["to"] == curr_addr:
                related_txs.append(tx)
                queue.append((tx["from"], curr_depth + 1))
                
    connections = [
        ConnectionNode(from_address=tx["from"], to_address=tx["to"], value=tx["value"])
        for tx in related_txs
    ]
    
    risk = compute_risk(request.address, related_txs)
    
    # Basic report generation
    analysis = "Standard transaction activity."
    if risk > 0.8:
        analysis = "ALERT: Direct or secondary exposure to mixing service detected (Tornado Cash). High risk layering pattern."
    elif risk > 0.4:
        analysis = "WARNING: Significant flow volume and multi-hop structure identified."

    return TraceResponse(
        wallet=request.address,
        connections=connections,
        risk_score=risk,
        analysis=analysis
    )
