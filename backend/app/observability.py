"""
LEATrace Observability — Production.

Prometheus metrics, OpenTelemetry traces, and structured logging.
All instrumentation is optional — gracefully degrades if deps not installed.

Metrics exposed at GET /metrics (Prometheus text format).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable, Optional

logger = logging.getLogger("leatrace.observability")

# ─── Prometheus ───────────────────────────────────────────────────────────────

PROMETHEUS_ENABLED = False
_prom: Optional[Any] = None

try:
    import prometheus_client as prom
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

    PROMETHEUS_ENABLED = True
    _prom = prom

    # Custom registry (avoids conflicts in tests)
    REGISTRY = CollectorRegistry(auto_describe=True)

    # ── Counters
    HTTP_REQUESTS_TOTAL = Counter(
        "leatrace_http_requests_total",
        "Total HTTP requests by method, endpoint, and status",
        ["method", "endpoint", "status_code"],
        registry=REGISTRY,
    )
    WALLET_QUERIES_TOTAL = Counter(
        "leatrace_wallet_queries_total",
        "Total blockchain wallet queries by chain",
        ["chain"],
        registry=REGISTRY,
    )
    RPC_ERRORS_TOTAL = Counter(
        "leatrace_rpc_errors_total",
        "Total RPC provider errors by chain and error type",
        ["chain", "error_type"],
        registry=REGISTRY,
    )
    CASES_CREATED_TOTAL = Counter(
        "leatrace_cases_created_total",
        "Total investigation cases created",
        registry=REGISTRY,
    )
    SANCTIONS_CHECKS_TOTAL = Counter(
        "leatrace_sanctions_checks_total",
        "Total sanctions address checks",
        ["result"],  # "hit" or "miss"
        registry=REGISTRY,
    )
    TAXII_SYNC_TOTAL = Counter(
        "leatrace_taxii_sync_total",
        "Total TAXII sync operations",
        ["collection_id", "status"],
        registry=REGISTRY,
    )
    AUTH_FAILURES_TOTAL = Counter(
        "leatrace_auth_failures_total",
        "Total authentication failures",
        ["reason"],
        registry=REGISTRY,
    )

    # ── Histograms
    HTTP_REQUEST_DURATION = Histogram(
        "leatrace_http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "endpoint"],
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
        registry=REGISTRY,
    )
    RPC_CALL_DURATION = Histogram(
        "leatrace_rpc_call_duration_seconds",
        "Blockchain RPC call duration in seconds",
        ["chain", "method"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
        registry=REGISTRY,
    )

    # ── Gauges
    ACTIVE_CASES_GAUGE = Gauge(
        "leatrace_active_cases",
        "Current number of active investigation cases",
        registry=REGISTRY,
    )
    SANCTIONS_ENTRIES_GAUGE = Gauge(
        "leatrace_sanctions_entries_total",
        "Total sanctions entries in local DB",
        registry=REGISTRY,
    )
    STIX_INDICATORS_GAUGE = Gauge(
        "leatrace_stix_indicators_total",
        "Total STIX indicators in local DB",
        registry=REGISTRY,
    )

    # ── Threat Intelligence Metrics ──

    TI_IOCS_TOTAL = Gauge(
        "leatrace_ti_iocs_total",
        "Total IOCs in the database by type and status",
        ["ioc_type", "status"],
        registry=REGISTRY,
    )
    TI_SYNC_TOTAL = Counter(
        "leatrace_ti_sync_total",
        "Total TI sync operations by provider and status",
        ["provider", "status"],
        registry=REGISTRY,
    )
    TI_SYNC_DURATION = Histogram(
        "leatrace_ti_sync_duration_seconds",
        "TI provider sync duration in seconds",
        ["provider"],
        buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
        registry=REGISTRY,
    )
    TI_ENRICHMENT_TOTAL = Counter(
        "leatrace_ti_enrichment_total",
        "Total IOC enrichment operations by type",
        ["enrichment_type", "status"],
        registry=REGISTRY,
    )
    TI_ENRICHMENT_DURATION = Histogram(
        "leatrace_ti_enrichment_duration_seconds",
        "IOC enrichment duration in seconds",
        ["enrichment_type"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
        registry=REGISTRY,
    )
    TI_PROVIDER_HEALTH = Gauge(
        "leatrace_ti_provider_health",
        "TI provider health status (1=healthy, 0=unhealthy)",
        ["provider"],
        registry=REGISTRY,
    )
    TI_CONFIDENCE_DISTRIBUTION = Histogram(
        "leatrace_ti_confidence_distribution",
        "Distribution of IOC confidence scores",
        buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        registry=REGISTRY,
    )
    TI_FEED_PRIORITY = Gauge(
        "leatrace_ti_feed_priority_score",
        "Feed priority composite score by provider",
        ["provider"],
        registry=REGISTRY,
    )
    TI_OBJECTS_INGESTED = Counter(
        "leatrace_ti_objects_ingested_total",
        "Total STIX objects ingested by type and source",
        ["stix_type", "source"],
        registry=REGISTRY,
    )

    logger.info("Prometheus metrics enabled (including TI metrics)")

except ImportError:
    logger.info(
        "prometheus_client not installed. Metrics endpoint will return 503. "
        "Install with: pip install prometheus_client"
    )


# ─── OpenTelemetry ────────────────────────────────────────────────────────────

OTEL_ENABLED = False
_tracer: Optional[Any] = None

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")  # e.g. http://jaeger:4317

    provider = TracerProvider()

    if OTEL_ENDPOINT:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OpenTelemetry OTLP exporter configured: %s", OTEL_ENDPOINT)
        except ImportError:
            logger.info("opentelemetry-exporter-otlp not installed. Using console exporter.")
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        # Console exporter in dev (disabled by default — too noisy)
        if os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true":
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("leatrace", "2.0.0")
    OTEL_ENABLED = True
    logger.info("OpenTelemetry tracing enabled")

except ImportError:
    logger.info(
        "opentelemetry-sdk not installed. Distributed tracing disabled. "
        "Install with: pip install opentelemetry-sdk"
    )


# ─── Public API ──────────────────────────────────────────────────────────────

def record_request(method: str, endpoint: str, status_code: int, duration_s: float) -> None:
    """Records HTTP request metrics (no-op if Prometheus not installed)."""
    if not PROMETHEUS_ENABLED:
        return
    try:
        HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()
        HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration_s)
    except Exception as e:
        logger.debug("Metrics record_request error: %s", e)


def record_wallet_query(chain: str) -> None:
    """Increments wallet query counter by chain."""
    if not PROMETHEUS_ENABLED:
        return
    try:
        WALLET_QUERIES_TOTAL.labels(chain=chain).inc()
    except Exception as e:
        logger.debug("Metrics record_wallet_query error: %s", e)


def record_rpc_error(chain: str, error_type: str) -> None:
    """Increments RPC error counter."""
    if not PROMETHEUS_ENABLED:
        return
    try:
        RPC_ERRORS_TOTAL.labels(chain=chain, error_type=error_type).inc()
    except Exception as e:
        logger.debug("Metrics record_rpc_error error: %s", e)


def record_sanctions_check(hit: bool) -> None:
    """Records a sanctions check result."""
    if not PROMETHEUS_ENABLED:
        return
    try:
        SANCTIONS_CHECKS_TOTAL.labels(result="hit" if hit else "miss").inc()
    except Exception as e:
        logger.debug("Metrics record_sanctions_check error: %s", e)


def record_auth_failure(reason: str) -> None:
    """Records an authentication failure."""
    if not PROMETHEUS_ENABLED:
        return
    try:
        AUTH_FAILURES_TOTAL.labels(reason=reason).inc()
    except Exception as e:
        logger.debug("Metrics record_auth_failure error: %s", e)


def get_metrics_output() -> Optional[bytes]:
    """Returns Prometheus text-format metrics. Returns None if not available."""
    if not PROMETHEUS_ENABLED:
        return None
    try:
        return generate_latest(REGISTRY)
    except Exception as e:
        logger.error("Failed to generate Prometheus metrics: %s", e)
        return None


def get_content_type() -> str:
    """Returns Prometheus content type header."""
    if not PROMETHEUS_ENABLED:
        return "text/plain"
    try:
        return CONTENT_TYPE_LATEST
    except Exception:
        return "text/plain"


def get_tracer() -> Optional[Any]:
    """Returns OpenTelemetry tracer or None if not configured."""
    return _tracer


def span(name: str) -> Any:
    """Context manager for an OTel span. No-op if OTel not configured."""
    if _tracer:
        return _tracer.start_as_current_span(name)

    class _noop:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
    return _noop()
