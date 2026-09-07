import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, security

router = APIRouter(prefix="/api/graph", tags=["Graph Analytics"])

@router.get("/{chain}/{address}")
def get_transaction_graph(chain: str, address: str, depth: int = 3, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    # Standard security check on length
    if len(address) < 10:
        raise HTTPException(status_code=400, detail="Invalid address format")

    # Specific graph setups for realistic demonstration
    address_short = f"{address[:6]}...{address[-4:]}"
    
    # We will build a structured graph
    nodes = []
    edges = []

    # Check if LockBit Ransomware Campaign
    if address == "1LbcPeel5s9zARansom993vX78cDf" or "ransom" in address.lower():
        # Central target node
        nodes = [
            {"id": address, "label": "LockBit Ransomware Receiver (BTC)", "type": "investigated", "balance": 1842.11, "riskScore": 98, "tags": ["ransomware", "OFAC"]},
            # Tier 1 inputs (Victim deposit wallets)
            {"id": "BTC_Victim_Corp_A", "label": "Victim Corp A Payment Node", "type": "wallet", "balance": 0.05, "riskScore": 25, "tags": ["victim"]},
            {"id": "BTC_Victim_Gov_B", "label": "Victim Health Dept", "type": "wallet", "balance": 0.01, "riskScore": 15, "tags": ["victim"]},
            # Tier 1 outputs (Peeling Chain hop 1)
            {"id": "BTC_Peel_Hop_1", "label": "Peeling Splitter Node 1", "type": "wallet", "balance": 45.3, "riskScore": 85, "tags": ["peeling-chain"]},
            {"id": "BTC_Peel_Hop_2", "label": "Peeling Splitter Node 2", "type": "wallet", "balance": 12.8, "riskScore": 82, "tags": ["peeling-chain"]},
            # Tier 2 outputs (Mixer / High Risk Exchanges)
            {"id": "Wasabi_Mixer_Entrance", "label": "Wasabi Wallet CoinJoin", "type": "watchlisted", "balance": 520.4, "riskScore": 95, "tags": ["mixer"]},
            {"id": "HighRisk_Ex_Ru", "label": "Garantex sanctioned broker", "type": "exchange", "balance": 8940.1, "riskScore": 92, "tags": ["exchange", "sanctioned"]},
            {"id": "Binance_Deposit", "label": "Binance OTC Broker Node", "type": "exchange", "balance": 145000.2, "riskScore": 40, "tags": ["exchange"]}
        ]
        
        edges = [
            # Inflows from Victims
            {"id": "e_vic_1", "source": "BTC_Victim_Corp_A", "target": address, "value": 450.0, "timestamp": "2026-06-10T08:00:00Z"},
            {"id": "e_vic_2", "source": "BTC_Victim_Gov_B", "target": address, "value": 1392.11, "timestamp": "2026-06-12T11:20:00Z"},
            # Outflows (peeling splitters)
            {"id": "e_peel_1", "source": address, "target": "BTC_Peel_Hop_1", "value": 900.0, "timestamp": "2026-06-13T14:45:00Z"},
            {"id": "e_peel_2", "source": address, "target": "BTC_Peel_Hop_2", "value": 850.0, "timestamp": "2026-06-14T09:10:00Z"},
            # Next hop to mixers
            {"id": "e_mix_1", "source": "BTC_Peel_Hop_1", "target": "Wasabi_Mixer_Entrance", "value": 850.0, "timestamp": "2026-06-14T17:00:00Z"},
            {"id": "e_ex_1", "source": "BTC_Peel_Hop_2", "target": "HighRisk_Ex_Ru", "value": 800.0, "timestamp": "2026-06-15T12:00:00Z"},
            {"id": "e_ex_2", "source": "BTC_Peel_Hop_2", "target": "Binance_Deposit", "value": 30.0, "timestamp": "2026-06-15T13:30:00Z"}
        ]
    
    elif address.lower().startswith("0x71c") or "tornado" in address.lower():
        # Tornado Cash exploter graph
        nodes = [
            {"id": address, "label": "Tornado Exploit Drainer (ETH)", "type": "investigated", "balance": 450.84, "riskScore": 89, "tags": ["exploit", "hacker"]},
            {"id": "0xTornado_Cash_Router", "label": "Tornado.Cash: Proxy 0x72a", "type": "watchlisted", "balance": 2390145.2, "riskScore": 99, "tags": ["mixer", "sanctioned"]},
            {"id": "0xUniswap_V3_Router", "label": "Uniswap V3: Router", "type": "contract", "balance": 0.0, "riskScore": 20, "tags": ["dex", "defi"]},
            {"id": "0xLiq_Pool_USDC", "label": "Uniswap: USDC/ETH Pool", "type": "contract", "balance": 48200.0, "riskScore": 15, "tags": ["liquidity-pool"]},
            {"id": "0xExchange_Deposit", "label": "Huobi Gateway Node", "type": "exchange", "balance": 23410.8, "riskScore": 48, "tags": ["exchange"]}
        ]
        
        edges = [
            {"id": "e_torn_in", "source": "0xTornado_Cash_Router", "target": address, "value": 1500.0, "timestamp": "2026-06-18T10:00:00Z"},
            {"id": "e_uni_swap", "source": address, "target": "0xUniswap_V3_Router", "value": 800.0, "timestamp": "2026-06-18T11:30:00Z"},
            {"id": "e_pool_interact", "source": "0xUniswap_V3_Router", "target": "0xLiq_Pool_USDC", "value": 800.0, "timestamp": "2026-06-18T11:31:00Z"},
            {"id": "e_ex_deposit", "source": address, "target": "0xExchange_Deposit", "value": 240.0, "timestamp": "2026-06-18T13:00:00Z"}
        ]
        
    else:
        # Default dynamic graph generator
        nodes = [
            {"id": address, "label": address_short, "type": "investigated", "balance": 15.5, "riskScore": 45},
            {"id": f"inflow_{address[:4]}", "label": "Inflow Origin Wallet", "type": "wallet", "balance": 120.3, "riskScore": 12},
            {"id": f"outflow_1_{address[:4]}", "label": "Outflow Exchange node", "type": "exchange", "balance": 4890.0, "riskScore": 8},
            {"id": f"outflow_2_{address[:4]}", "label": "Hop Change Address", "type": "wallet", "balance": 2.5, "riskScore": 55}
        ]
        
        edges = [
            {"id": "e_in", "source": f"inflow_{address[:4]}", "target": address, "value": 50.0, "timestamp": "2026-06-15T09:00:00Z"},
            {"id": "e_out_1", "source": address, "target": f"outflow_1_{address[:4]}", "value": 35.0, "timestamp": "2026-06-16T12:00:00Z"},
            {"id": "e_out_2", "source": address, "target": f"outflow_2_{address[:4]}", "value": 15.0, "timestamp": "2026-06-17T15:22:00Z"}
        ]

    # Log query
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=current_user.id,
        username=current_user.username,
        action=f"Generated multi-hop transaction tracing graph for {chain}:{address} (Depth: {depth})",
        status="success"
    )
    db.add(audit_entry)
    db.commit()

    return {
        "address": address,
        "chain": chain,
        "depth": depth,
        "nodes": nodes,
        "edges": edges
    }


# ===================================================================
# Graph Intelligence Endpoints
# ===================================================================

from ..neo4j_service import neo4j_graph


@router.get("/centrality/degree")
def get_degree_centrality(
    limit: int = 20,
    current_user: models.User = Depends(security.get_current_user),
):
    """Returns nodes with highest degree centrality (most connections)."""
    return {"centrality_type": "degree", "results": neo4j_graph.get_degree_centrality(limit)}


@router.get("/centrality/{address}")
def get_address_centrality(
    address: str,
    current_user: models.User = Depends(security.get_current_user),
):
    """Returns centrality metrics for a specific address."""
    betweenness = neo4j_graph.get_betweenness_centrality(address)
    influence = neo4j_graph.get_influence_score(address)
    return {
        "address": address,
        "betweenness": betweenness,
        "influence": influence,
    }


@router.get("/influence/{address}")
def get_influence_score(
    address: str,
    current_user: models.User = Depends(security.get_current_user),
):
    """Computes influence score based on connections and risk levels."""
    return neo4j_graph.get_influence_score(address)


@router.get("/paths/{start}/{end}")
def find_paths(
    start: str,
    end: str,
    max_depth: int = 6,
    current_user: models.User = Depends(security.get_current_user),
):
    """Finds all paths between two addresses up to max_depth."""
    shortest = neo4j_graph.find_shortest_path(start, end)
    all_paths = neo4j_graph.find_all_paths(start, end, max_depth)
    return {
        "start": start,
        "end": end,
        "shortest_path": shortest,
        "all_paths": all_paths,
    }


@router.get("/communities")
def get_communities(
    current_user: models.User = Depends(security.get_current_user),
):
    """Identifies wallet communities using graph clustering."""
    return {"communities": neo4j_graph.get_community_detection()}


@router.get("/risk-propagation/{address}")
def get_risk_propagation(
    address: str,
    max_hops: int = 3,
    current_user: models.User = Depends(security.get_current_user),
):
    """Propagates risk from a node to its neighborhood."""
    return {
        "source_address": address,
        "max_hops": max_hops,
        "propagated_risks": neo4j_graph.propagate_risk(address, max_hops),
    }


@router.get("/investigation/{address}")
def investigate_neighborhood(
    address: str,
    depth: int = 2,
    current_user: models.User = Depends(security.get_current_user),
):
    """Returns the N-hop neighborhood for investigation."""
    return neo4j_graph.investigate_neighborhood(address, depth)


@router.get("/statistics")
def get_graph_statistics(
    current_user: models.User = Depends(security.get_current_user),
):
    """Returns global graph database statistics."""
    return neo4j_graph.get_graph_statistics()
