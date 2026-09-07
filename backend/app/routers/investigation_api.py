"""
LEATrace Investigation Router — Production.

Unified investigation API integrating:
- Chain registry (11 chains)
- Wallet profiler
- Fund tracer (multi-hop BFS)
- OFAC SDN sanctions
- Price oracle
- AML analysis

This is the primary investigation interface for law enforcement users.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from ..database import get_db
from .. import models, security
from ..chains.registry import chain_registry
from ..wallet_profiler import wallet_profiler
from ..fund_tracer import fund_tracer
from ..price_oracle import price_oracle
from ..laundering_engine import laundering_engine
from ..risk_engine import risk_engine
from ..entity_resolution import entity_resolution
from ..providers.sanctions_provider import ofac_provider

logger = logging.getLogger("leatrace.routers.investigation")

router = APIRouter(prefix="/api/investigation", tags=["Investigation Engine"])


# --- Request Models ---

class ProfileRequest(BaseModel):
    address: str
    chain: str = "ethereum"

class TraceRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    direction: str = "forward"  # forward, backward, bidirectional
    depth: int = 3
    min_value: float = 0.0

class MultiChainRequest(BaseModel):
    address: str
    chains: Optional[List[str]] = None

class SanctionsCheckRequest(BaseModel):
    addresses: List[str]


# --- Chain Management ---

@router.get("/chains")
def list_supported_chains():
    """Lists all supported blockchain chains with metadata."""
    return {
        "total_chains": len(chain_registry.get_supported_chain_ids()),
        "chains": chain_registry.get_chain_metadata(),
    }


@router.get("/chains/{chain_id}/status")
def get_chain_status(chain_id: str):
    """Gets real-time status for a specific chain."""
    chain = chain_registry.get_chain(chain_id)
    if chain is None:
        raise HTTPException(status_code=404, detail=f"Chain '{chain_id}' not supported")

    block_height = chain.get_block_height()
    return {
        "chain": chain.get_info(),
        "block_height": block_height,
        "online": block_height is not None,
    }


@router.get("/chains/{chain_id}/validate/{address}")
def validate_address(chain_id: str, address: str):
    """Validates an address format for a specific chain."""
    chain = chain_registry.get_chain(chain_id)
    if chain is None:
        raise HTTPException(status_code=404, detail=f"Chain '{chain_id}' not supported")

    return {
        "address": address,
        "chain": chain_id,
        "valid": chain.validate_address(address),
    }


@router.get("/detect-chain/{address}")
def detect_chain(address: str):
    """Attempts to detect which chain an address belongs to."""
    detected = chain_registry.detect_chain(address)
    return {
        "address": address,
        "detected_chain": detected,
        "confidence": "exact" if detected else "unknown",
    }


# --- Wallet Profiling ---

@router.get("/profile/{address}")
def get_wallet_profile(
    address: str,
    chain: str = Query("ethereum", description="Blockchain network"),
):
    """
    Comprehensive wallet profile from real blockchain data.
    Includes balance, transaction metrics, activity analysis, and token data.
    """
    return wallet_profiler.build_profile(address, chain)


@router.post("/profile")
def post_wallet_profile(req: ProfileRequest):
    """POST variant for wallet profiling."""
    return wallet_profiler.build_profile(req.address, req.chain)


@router.post("/profile/multi-chain")
def get_multi_chain_profile(req: MultiChainRequest):
    """
    Multi-chain wallet profile — queries multiple chains for the same address.
    Useful for EVM addresses with activity across L2s.
    """
    return wallet_profiler.build_multi_chain_profile(req.address, req.chains)


# --- Fund Tracing ---

@router.get("/trace/{address}")
def trace_funds(
    address: str,
    chain: str = Query("ethereum", description="Blockchain network"),
    direction: str = Query("forward", description="Trace direction: forward, backward, bidirectional"),
    depth: int = Query(3, ge=1, le=5, description="Max trace depth (1-5)"),
    min_value: float = Query(0.0, ge=0.0, description="Min transaction value to follow"),
):
    """
    Multi-hop fund tracing. Follows the flow of funds across transactions.
    - forward: Where did money from this address go?
    - backward: Where did this address get its money?
    - bidirectional: Both directions.
    """
    if direction == "forward":
        return fund_tracer.trace_forward(address, chain, depth, min_value)
    elif direction == "backward":
        return fund_tracer.trace_backward(address, chain, depth, min_value)
    elif direction == "bidirectional":
        return fund_tracer.trace_bidirectional(address, chain, depth, min_value)
    else:
        raise HTTPException(status_code=400, detail="direction must be 'forward', 'backward', or 'bidirectional'")


@router.post("/trace")
def post_trace_funds(req: TraceRequest):
    """POST variant for fund tracing."""
    return trace_funds(req.address, req.chain, req.direction, req.depth, req.min_value)


# --- Sanctions & Compliance ---

@router.get("/sanctions/check/{address}")
def check_sanctions(address: str):
    """Checks an address against OFAC SDN sanctions list."""
    is_sanctioned = ofac_provider.is_sanctioned(address)
    details = ofac_provider.get_sanction_details(address)

    # Also check entity resolution
    entity = entity_resolution.resolve_entity(address)
    entity_sanctioned = entity and entity.get("category") == "sanctioned"

    return {
        "address": address,
        "ofac_sanctioned": is_sanctioned,
        "entity_sanctioned": entity_sanctioned,
        "is_sanctioned": is_sanctioned or entity_sanctioned,
        "ofac_details": details,
        "entity": entity,
    }


@router.post("/sanctions/batch")
def batch_sanctions_check(req: SanctionsCheckRequest):
    """Batch sanctions check for multiple addresses."""
    results = []
    for addr in req.addresses[:100]:  # Limit batch size
        is_sanctioned = ofac_provider.is_sanctioned(addr)
        results.append({
            "address": addr,
            "is_sanctioned": is_sanctioned,
            "details": ofac_provider.get_sanction_details(addr) if is_sanctioned else None,
        })

    flagged = [r for r in results if r["is_sanctioned"]]
    return {
        "total_checked": len(results),
        "total_flagged": len(flagged),
        "results": results,
    }


@router.get("/sanctions/search")
def search_sanctions(query: str = Query(..., description="Search term")):
    """Searches OFAC SDN by entity name or address."""
    return {"results": ofac_provider.search(query)}


@router.get("/sanctions/stats")
def get_sanctions_stats():
    """Returns OFAC SDN loading statistics."""
    return ofac_provider.get_stats()


# --- AML Analysis ---

@router.get("/aml/{address}")
def get_aml_analysis(
    address: str,
    chain: str = Query("ethereum", description="Blockchain network"),
):
    """
    Full anti-money laundering analysis: peel chain detection,
    smurfing/structuring, layering analysis, and round amount detection.
    """
    chain_plugin = chain_registry.get_chain(chain)
    if chain_plugin is None:
        raise HTTPException(status_code=404, detail=f"Chain '{chain}' not supported")

    txs = chain_plugin.get_transactions(address, page=1, limit=100)
    return laundering_engine.full_aml_analysis(txs, address)


# --- Risk Scoring ---

@router.get("/risk/{address}")
def get_comprehensive_risk(
    address: str,
    chain: str = Query("ethereum", description="Blockchain network"),
):
    """
    Comprehensive risk assessment integrating:
    - Wallet profiling
    - OFAC sanctions
    - AML patterns
    - Entity resolution
    - Transaction analysis
    """
    chain_plugin = chain_registry.get_chain(chain)
    if chain_plugin is None:
        raise HTTPException(status_code=404, detail=f"Chain '{chain}' not supported")

    # Get real data
    txs = chain_plugin.get_transactions(address, page=1, limit=100)
    balance = chain_plugin.get_balance(address)
    is_contract = chain_plugin.is_contract(address)

    # Sanctions check
    is_sanctioned = ofac_provider.is_sanctioned(address)
    entity = entity_resolution.resolve_entity(address)
    if entity and entity.get("category") == "sanctioned":
        is_sanctioned = True

    # AML analysis
    aml = laundering_engine.full_aml_analysis(txs, address)

    # Transaction metrics
    addr_lower = address.lower()
    incoming = sum(1 for tx in txs if tx.get("to", "").lower() == addr_lower)
    outgoing = len(txs) - incoming
    total_value = sum(tx.get("value", 0.0) for tx in txs)
    unique_cps = len(set(
        tx.get("from", "").lower() for tx in txs
    ) | set(
        tx.get("to", "").lower() for tx in txs
    ))

    # Check mixer exposure via entity resolution
    mixer_exposure = 0.0
    for tx in txs:
        counterparty = tx.get("to", "") if tx.get("from", "").lower() == addr_lower else tx.get("from", "")
        cp_entity = entity_resolution.resolve_entity(counterparty)
        if cp_entity and cp_entity.get("category") == "mixer":
            mixer_exposure += tx.get("value", 0.0)
    total_outgoing_value = sum(tx.get("value", 0.0) for tx in txs if tx.get("from", "").lower() == addr_lower)
    mixer_pct = (mixer_exposure / max(total_outgoing_value, 0.01)) * 100

    # Score
    result = risk_engine.score_wallet(
        address=address,
        tx_count=len(txs),
        total_volume_eth=total_value,
        incoming_count=incoming,
        outgoing_count=outgoing,
        unique_counterparties=unique_cps,
        is_contract=is_contract,
        mixer_exposure_pct=mixer_pct,
        is_sanctioned=is_sanctioned,
        peel_chain_detected=aml.get("peel_chain", {}).get("is_peel_chain_active", False),
    )

    result["chain"] = chain
    result["entity"] = entity.get("entity_name") if entity else "Unknown"
    result["aml_risk_score"] = aml.get("aml_risk_score", 0)
    result["aml_patterns_detected"] = aml.get("patterns_detected", 0)
    result["balance"] = balance
    result["balance_usd"] = price_oracle.convert_chain_to_usd(balance, chain) if balance else None

    return result


# --- Price Oracle ---

@router.get("/price/{symbol}")
def get_token_price(symbol: str):
    """Gets the current USD price for a token symbol."""
    price = price_oracle.get_price_usd(symbol.upper())
    if price is None:
        raise HTTPException(status_code=404, detail=f"Price unavailable for {symbol}")
    return {"symbol": symbol.upper(), "price_usd": price}


@router.get("/prices")
def get_all_prices():
    """Fetches and returns prices for all supported tokens."""
    return {"prices": price_oracle.fetch_all_prices()}
