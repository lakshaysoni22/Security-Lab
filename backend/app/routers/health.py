"""
LEATrace Health & Metrics Router — Production.

Endpoints:
  GET /health          — Liveness probe (always 200 if app is running)
  GET /health/ready    — Readiness probe (checks DB, Redis, RPC)
  GET /health/detail   — Full component status
  GET /metrics         — Prometheus text format metrics
"""

from __future__ import annotations

import datetime
import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..observability import get_metrics_output, get_content_type, PROMETHEUS_ENABLED

logger = logging.getLogger("leatrace.routers.health")

router = APIRouter(tags=["Health & Observability"])

_START_TIME = datetime.datetime.now(datetime.timezone.utc)


# ─── Liveness ─────────────────────────────────────────────────────────────────

@router.get("/health", status_code=200)
def liveness_probe() -> Dict[str, Any]:
    """
    Liveness probe — returns 200 as long as the application process is running.
    Used by Kubernetes/Docker to determine if the container should be restarted.
    """
    uptime = (datetime.datetime.now(datetime.timezone.utc) - _START_TIME).total_seconds()
    return {
        "status": "alive",
        "uptime_seconds": round(uptime, 1),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


# ─── Readiness ────────────────────────────────────────────────────────────────

@router.get("/health/ready")
def readiness_probe(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Readiness probe — checks all critical dependencies.
    Returns 200 if ready to serve traffic, 503 if any critical dependency is down.
    """
    checks: Dict[str, Any] = {}
    all_healthy = True

    # ── Database check
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)[:100]}
        all_healthy = False

    # ── Redis check (optional)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            checks["redis"] = {"status": "healthy", "url": redis_url}
        except ImportError:
            checks["redis"] = {"status": "not_installed", "url": redis_url}
        except Exception as e:
            checks["redis"] = {"status": "error", "error": str(e)[:100]}
            # Redis is optional — don't fail readiness
    else:
        checks["redis"] = {"status": "not_configured"}

    # ── Ethereum RPC check (optional, lightweight)
    eth_rpc = os.getenv("ETH_RPC_URL", "https://cloudflare-eth.com")
    try:
        import json
        import urllib.request
        payload = json.dumps({"jsonrpc": "2.0", "method": "net_version", "params": [], "id": 1}).encode()
        req = urllib.request.Request(
            eth_rpc,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "LEATrace-Health/2.0"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            result = json.loads(resp.read())
            checks["ethereum_rpc"] = {
                "status": "healthy",
                "network_id": result.get("result"),
                "url": eth_rpc[:40] + "...",
            }
    except Exception as e:
        checks["ethereum_rpc"] = {"status": "degraded", "error": str(e)[:80]}
        # RPC degraded doesn't block readiness

    status_code = 200 if all_healthy else 503
    body = {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    from fastapi.responses import JSONResponse
    return JSONResponse(content=body, status_code=status_code)


# ─── Full Detail ──────────────────────────────────────────────────────────────

@router.get("/health/detail")
def health_detail(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Full system component status for operational dashboards.
    Includes DB stats, feature flags, and integration status.
    """
    from .. import models
    from ..taxii_client import taxii_client
    from ..feed_scheduler import feed_scheduler

    db_stats: Dict[str, Any] = {}
    try:
        db_stats = {
            "cases": db.query(models.Case).count(),
            "wallets": db.query(models.Wallet).count(),
            "alerts": db.query(models.Alert).count(),
            "audit_logs": db.query(models.AuditLog).count(),
            "sanctions_entries": db.query(models.SanctionsEntry).count(),
            "stix_indicators": db.query(models.StixIndicator).count(),
            "security_incidents": db.query(models.SecurityIncident).count(),
        }
    except Exception as e:
        db_stats = {"error": str(e)[:100]}

    uptime = (datetime.datetime.now(datetime.timezone.utc) - _START_TIME).total_seconds()

    return {
        "application": {
            "name":    "LEATrace",
            "version": "2.0.0",
            "uptime_seconds": round(uptime, 1),
            "started_at": _START_TIME.isoformat(),
        },
        "database": db_stats,
        "integrations": {
            "taxii": taxii_client.health_check(),
            "sanctions": feed_scheduler.get_status(),
            "prometheus": {"enabled": PROMETHEUS_ENABLED},
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


# ─── Metrics ──────────────────────────────────────────────────────────────────

@router.get("/metrics")
def prometheus_metrics() -> Response:
    """
    Prometheus text-format metrics endpoint.
    Returns 503 if prometheus_client is not installed.
    """
    metrics = get_metrics_output()
    if metrics is None:
        return Response(
            content=(
                "# Prometheus metrics unavailable.\n"
                "# Install prometheus_client: pip install prometheus_client\n"
            ),
            status_code=503,
            media_type="text/plain",
        )
    return Response(content=metrics, media_type=get_content_type())
