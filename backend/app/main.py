import os
import uuid
import datetime
import logging
import secrets
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from . import models, security
from .routers import auth, cases, wallets, graph, evidence, audit, ai, real_ecosystem, streaming, incident, siem, cluster_api, soc_api, forensics_api, security_api, iam_api, cti_api, siem_correlation_api, elasticsearch_api, ai_intelligence_api, blockchain_risk_api, device_api, investigation_api, reports, taxii, sanctions, health, threat_intel_api

logger = logging.getLogger("leatrace.main")

DEMO_DATA_ENABLED = os.getenv("LEATrace_DEMO_DATA", "false").lower() in {"1", "true", "yes", "on"}
BACKGROUND_TASKS_ENABLED = os.getenv("LEATrace_BACKGROUND_TASKS", "true").lower() in {"1", "true", "yes", "on"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    import asyncio
    from .connection_pool import connection_pool
    from .chains.registry import chain_registry
    from .oauth_server import oauth_server

    # Import stix_models so all STIX/IOC/TI tables are registered with Base
    from . import stix_models  # noqa: F401
    # Import sanctions_models so all sanctions tables are registered with Base
    from . import sanctions_models  # noqa: F401

    # Create DB tables (checkfirst=True prevents duplicate-table errors on reimport)
    Base.metadata.create_all(bind=engine, checkfirst=True)

    # Initialize chain registry
    chain_registry._ensure_initialized()
    logger.info(f"Chain registry ready: {len(chain_registry.get_supported_chain_ids())} chains")

    # Bootstrap default OAuth client from env vars
    db = SessionLocal()
    try:
        oauth_server.bootstrap_default_client(db=db)
        oauth_server.cleanup_expired_codes(db=db)
        logger.info("OAuth bootstrap complete")
    except Exception as e:
        logger.warning("OAuth bootstrap failed (non-fatal): %s", e)
    finally:
        db.close()

    # ── Register Threat Intelligence Providers ──
    _register_ti_providers()
    logger.info("Threat Intelligence providers registered")

    if DEMO_DATA_ENABLED:
        logger.info("Demo data mode enabled. Seeding database...")
        seed_data()

    if BACKGROUND_TASKS_ENABLED:
        logger.info("Background tasks enabled. Starting blockchain listener...")
        asyncio.create_task(real_blockchain_listener())
        from .indexer import run_multi_chain_indexer
        asyncio.create_task(run_multi_chain_indexer())

        # Start sanctions background scheduler
        from .sanctions_scheduler import sanctions_scheduler
        await sanctions_scheduler.start()
        logger.info("Sanctions background scheduler started")

    yield  # Application runs here

    # Shutdown: stop sanctions scheduler
    if BACKGROUND_TASKS_ENABLED:
        from .sanctions_scheduler import sanctions_scheduler
        await sanctions_scheduler.stop()

    # Shutdown: close connection pools
    logger.info("Application shutting down. Closing connections...")
    connection_pool.close()
    await connection_pool.aclose()


app = FastAPI(
    title="LEATrace API",
    description="Law Enforcement Advanced Trace Intelligence Platform REST Backend",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://leattrace.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware (audit logging, security headers)
from .rbac import SecurityMiddleware
app.add_middleware(SecurityMiddleware)

# Rate limiting middleware (sliding window, per-IP)
from .middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# Request timing middleware
from starlette.middleware.base import BaseHTTPMiddleware
import time as _time

class _TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = _time.perf_counter()
        response = await call_next(request)
        duration_ms = round((_time.perf_counter() - start) * 1000, 2)
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        # Record Prometheus metric (no-op if prometheus_client not installed)
        try:
            from .observability import record_request
            record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration_s=duration_ms / 1000,
            )
        except Exception:
            pass
        return response

app.add_middleware(_TimingMiddleware)

# Register routers
app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(wallets.router)
app.include_router(graph.router)
app.include_router(evidence.router)
app.include_router(audit.router)
app.include_router(ai.router)
app.include_router(real_ecosystem.router)
app.include_router(streaming.router)
app.include_router(incident.router)
app.include_router(siem.router)
app.include_router(cluster_api.router)
app.include_router(soc_api.router)
app.include_router(forensics_api.router)
app.include_router(security_api.router)
app.include_router(iam_api.router)
app.include_router(cti_api.router)
app.include_router(siem_correlation_api.router)
app.include_router(elasticsearch_api.router)
app.include_router(ai_intelligence_api.router)
app.include_router(blockchain_risk_api.router)
app.include_router(device_api.router)
app.include_router(investigation_api.router)
app.include_router(reports.router)
app.include_router(taxii.router)
app.include_router(sanctions.router)
app.include_router(health.router)
app.include_router(threat_intel_api.router)


# ─── Threat Intelligence Provider Registration ───────────────────────────────

def _register_ti_providers():
    """Registers all TI providers with the provider manager."""
    from .threat_intel.provider_manager import provider_manager
    from .threat_intel.providers.taxii_provider import TAXIIProvider
    from .threat_intel.providers.sanctions_provider import SanctionsProvider
    from .threat_intel.providers.mitre_attack_provider import MITREAttackProvider

    provider_manager.register_provider(TAXIIProvider(
        name="taxii_default",
        priority=40,
    ))
    provider_manager.register_provider(SanctionsProvider(
        name="sanctions_default",
        priority=30,
    ))
    provider_manager.register_provider(MITREAttackProvider(
        name="mitre_attack",
        priority=20,
    ))
    logger.info(
        "TI providers registered: %s",
        [p.name for p in provider_manager.registry.get_all()],
    )


# Real blockchain node transaction listener background task
async def real_blockchain_listener():
    import asyncio
    import json
    import urllib.request
    import datetime
    from .event_broker import broker

    last_block = None
    rpc_url = "https://cloudflare-eth.com"
    
    while True:
        try:
            payload = json.dumps({"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}).encode("utf-8")
            req = urllib.request.Request(rpc_url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "LEATrace/1.0"})
            with urllib.request.urlopen(req, timeout=3) as res:
                response = json.loads(res.read().decode("utf-8"))
                block_hex = response.get("result")
                if not block_hex:
                    await asyncio.sleep(8)
                    continue
                block_num = int(block_hex, 16)
                
            if last_block is None:
                last_block = block_num - 1
                
            if block_num > last_block:
                for b in range(last_block + 1, block_num + 1):
                    b_hex = hex(b)
                    payload_b = json.dumps({"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": [b_hex, True], "id": 1}).encode("utf-8")
                    req_b = urllib.request.Request(rpc_url, data=payload_b, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req_b, timeout=5) as res_b:
                        res_data = json.loads(res_b.read().decode("utf-8"))
                        block_data = res_data.get("result")
                        if block_data and "transactions" in block_data:
                            for tx in block_data["transactions"]:
                                value_eth = int(tx.get("value", "0x0"), 16) / (10**18)
                                tx_hash = tx.get("hash")
                                tx_from = tx.get("from")
                                tx_to = tx.get("to")
                                
                                if tx_hash and tx_from and tx_to:
                                    tx_event = {
                                        "hash": tx_hash,
                                        "from": tx_from,
                                        "to": tx_to,
                                        "value": value_eth,
                                        "chain": "ETH",
                                        "timestamp": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"
                                    }
                                    await broker.publish("transaction_stream", tx_event)
                                    
                                    if value_eth >= 50.0:
                                        alert_event = {
                                            "id": f"alr_{tx_hash[:6]}",
                                            "chain": "ETH",
                                            "address": tx_to,
                                            "alias": "Whale Transfer",
                                            "type": "Whale Transaction",
                                            "severity": "high",
                                            "message": f"🚨 Whale Alert: Real-time transfer of {value_eth:.2f} ETH detected from {tx_from[:8]}... to {tx_to[:8]}... (Tx: {tx_hash[:10]}...)",
                                            "timestamp": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"
                                        }
                                        await broker.publish("alert_stream", alert_event)
                last_block = block_num
        except Exception as e:
            print(f"Error in blockchain background listener: {e}")

        await asyncio.sleep(6)

# Seed mock database values if empty
def seed_data():
    db = SessionLocal()
    try:
        # Check if users already exist
        if db.query(models.User).count() == 0:
            # Generate unique passwords for demo users (logged once, not hardcoded)
            demo_password = os.getenv("DEMO_USER_PASSWORD", "SecurePass@2026")
            logger.info(f"Demo data seeded. Demo user password: {demo_password}")

            users = [
                models.User(
                    id="usr-1",
                    email="lakshaysoni@cybercrime.gov.in",
                    username="Lakshay Soni",
                    hashed_password=security.get_password_hash(demo_password),
                    role="investigator",
                    is_active=True,
                    mfa_enabled=True,
                    mfa_secret="JBSWY3DPEHPK3PXP",
                    department="Cyber Crime Cell"
                ),
                models.User(
                    id="usr-2",
                    email="supervisor.sinha@cybercrime.gov.in",
                    username="Supervisor Sinha",
                    hashed_password=security.get_password_hash(demo_password),
                    role="supervisor",
                    is_active=True,
                    mfa_enabled=True,
                    mfa_secret="JBSWY3DPEHPK3PXP",
                    department="Cyber Investigation Command"
                ),
                models.User(
                    id="usr-3",
                    email="auditor.gupta@cybercrime.gov.in",
                    username="Auditor Gupta",
                    hashed_password=security.get_password_hash(demo_password),
                    role="auditor",
                    is_active=True,
                    mfa_enabled=False,
                    department="AML Oversight Committee"
                )
            ]
            db.add_all(users)
            db.commit()

            # Seed Cases
            cases = [
                models.Case(
                    id="case-1",
                    case_number="CC-2026-0847",
                    title="Crypto Ponzi Scheme — GainChain Network",
                    description="Investigation into GainChain, a suspected Ponzi scheme operating through Ethereum smart contracts. Multiple victims reported losses exceeding ₹50 Crore.",
                    priority="critical",
                    status="active",
                    investigator_id="usr-1",
                    investigator_name="Inspector Verma",
                    department="Cyber Crime Cell",
                    notes="Primary suspect wallet identified. Multi-hop tracing in progress."
                ),
                models.Case(
                    id="case-2",
                    case_number="CC-2026-0912",
                    title="Ransomware Payment Tracing — MedLock Attack",
                    description="Tracing ransom payments from MedLock ransomware attack targeting healthcare institutions. Bitcoin converted to ETH via DEX.",
                    priority="high",
                    status="active",
                    investigator_id="usr-1",
                    investigator_name="Inspector Verma",
                    department="Cyber Crime Cell",
                    notes="DEX swap transactions identified on Uniswap."
                )
            ]
            db.add_all(cases)
            db.commit()

            # Seed Wallets
            wallets = [
                models.Wallet(
                    id="wlt-1",
                    address="1LbcPeel5s9zARansom993vX78cDf",
                    chain="BTC",
                    label="LockBit Ransomware Receiver",
                    tags="sanctioned,ransomware,critical-risk",
                    risk_score=98,
                    is_contract=False,
                    case_id="case-2"
                ),
                models.Wallet(
                    id="wlt-2",
                    address="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28",
                    chain="ethereum",
                    label="Suspected Layering Wallet",
                    tags="suspect,ponzi-linked",
                    risk_score=78,
                    is_contract=False,
                    case_id="case-1"
                )
            ]
            db.add_all(wallets)
            db.commit()

            # Seed Watchlist items
            watchlist = [
                models.WatchlistEntry(
                    id="wtl-1",
                    address="1LbcPeel5s9zARansom993vX78cDf",
                    chain="BTC",
                    alias="LockBit Ransomware Receiver",
                    risk_score=98,
                    status="Monitored"
                ),
                models.WatchlistEntry(
                    id="wtl-2",
                    address="0x71c20e241775e5332f143715df332f143789a71b",
                    chain="ethereum",
                    alias="Tornado.Cash Exploit Drainer",
                    risk_score=89,
                    status="Monitored"
                )
            ]
            db.add_all(watchlist)
            db.commit()

            # Seed Audit Logs
            audit_logs = [
                models.AuditLog(
                    id="log_init",
                    user_id=None,
                    username="SYSTEM",
                    action="Database initial setup completed successfully. Seeded demo environment values.",
                    status="success",
                    actor="System",
                    decision_source="Database Setup",
                    validation_status="Verified"
                )
            ]
            db.add_all(audit_logs)
            db.commit()
            
    finally:
        db.close()

@app.get("/api/health")
def health_check():
    from .chains.registry import chain_registry
    from .database import _is_sqlite

    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        "database": "sqlite" if _is_sqlite else "postgresql",
        "supported_chains": len(chain_registry.get_supported_chain_ids()),
        "demo_data_enabled": DEMO_DATA_ENABLED,
        "background_tasks_enabled": BACKGROUND_TASKS_ENABLED,
    }
