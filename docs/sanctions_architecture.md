# LEATrace Sanctions Intelligence Platform — Architecture

## Overview

The Sanctions Intelligence Platform provides enterprise-grade real-time screening of blockchain wallet addresses, entity names, and transactions against multiple international sanctions lists. All data is sourced from live government feeds — no hardcoded sanctions data exists anywhere in the system.

## Architecture Diagram

```mermaid
graph TB
    subgraph "External Sanctions Feeds"
        OFAC["U.S. OFAC SDN List"]
        EU["EU Consolidated Sanctions"]
        UN["UN SC Consolidated List"]
    end

    subgraph "Provider Layer"
        PB["SanctionsProvider Base"]
        OP["OFACSDNProvider"]
        EP["EUConsolidatedProvider"]
        UP["UNConsolidatedProvider"]
        PM["SanctionsProviderManager"]
        PR["ProviderRegistry"]
    end

    subgraph "Ingestion Pipeline"
        FS["FeedScheduler"]
        BS["BackgroundScheduler"]
        IV["IntegrityValidator"]
    end

    subgraph "Normalized Database"
        PC["ProviderConfig"]
        LE["SanctionsListEntity"]
        LW["SanctionsListWallet"]
        AL["SanctionsAlias"]
        CO["SanctionsEntityCountry"]
        VH["VersionHistory"]
        CH["ChangeHistory"]
        IR["IntegrityReport"]
    end

    subgraph "Screening Engine"
        SE["SanctionsScreeningEngine"]
        WS["WalletScreening"]
        ES["EntityScreening"]
        TS["TransactionScreening"]
        BTS["BatchScreening"]
        SL["ScreeningAuditLog"]
        RC["RedisCache"]
    end

    subgraph "API Layer"
        SR["SanctionsRouter"]
        BC["BlockchainService"]
    end

    subgraph "Observability"
        PM2["Prometheus Metrics"]
        OT["OpenTelemetry Traces"]
    end

    OFAC --> OP
    EU --> EP
    UN --> UP
    OP & EP & UP --> PB
    PB --> PM
    PM --> PR
    PM --> FS
    FS --> BS
    PM --> IV
    IV --> IR

    FS --> LE & LW & AL & CO
    FS --> VH & CH
    PC --> PM

    LE --> SE
    LW --> SE
    AL --> SE
    SE --> WS & ES & TS & BTS
    SE --> SL
    SE --> RC

    SR --> SE
    BC --> SE
    SE --> PM2
    SE --> OT
```

## Component Reference

### 1. Provider Layer

| File | Class | Purpose |
|------|-------|---------|
| `providers/sanctions_provider_base.py` | `SanctionsProvider` | Abstract base with retry, rate limiting, health tracking |
| `providers/ofac_sdn_provider.py` | `OFACSDNProvider` | Downloads and parses U.S. OFAC SDN XML |
| `providers/eu_consolidated_provider.py` | `EUConsolidatedSanctionsProvider` | Downloads and parses EU Consolidated XML |
| `providers/un_sanctions_provider.py` | `UNConsolidatedSanctionsProvider` | Downloads and parses UN SC Consolidated XML |
| `providers/sanctions_provider_manager.py` | `SanctionsProviderManager` | Registry, sync orchestration, failover |

**Retry Behavior:**
- Exponential backoff: `initial_backoff * backoff_factor^(attempt-1)`
- Default: 3 retries, 2s initial, 2x factor, 60s max
- Rate limiting: sliding window per-minute enforcement
- Health tracking: ACTIVE → DEGRADED (1-2 failures) → FAILED (3+ failures)

### 2. Database Schema

```mermaid
erDiagram
    SanctionsProviderConfig ||--o{ SanctionsVersionHistory : "has versions"
    SanctionsListEntity ||--o{ SanctionsListWallet : "has wallets"
    SanctionsListEntity ||--o{ SanctionsAlias : "has aliases"
    SanctionsListEntity ||--o{ SanctionsEntityCountry : "has countries"
    SanctionsListEntity ||--o{ SanctionsEntityAddress : "has addresses"

    SanctionsProviderConfig {
        string provider_id PK
        string name
        boolean enabled
        int priority
        string feed_url
        datetime last_sync_at
    }

    SanctionsListEntity {
        string id PK
        string entity_uid
        string provider_id
        string name
        string entity_type
        string program
        string status
        boolean is_deleted
        datetime expires_at
    }

    SanctionsListWallet {
        string id PK
        string entity_id FK
        string address
        string normalized_address
        string currency
        boolean is_deleted
    }

    SanctionsAlias {
        string id PK
        string entity_id FK
        string alias_name
        string alias_type
    }

    SanctionsVersionHistory {
        string id PK
        string provider_id FK
        int version
        string checksum
        int delta_added
        int delta_updated
        int delta_removed
    }

    SanctionsScreeningLog {
        string id PK
        string query_type
        string query_value
        boolean matched
        float match_score
        string checked_by
        float response_time_ms
    }
```

### 3. Screening Engine

The `SanctionsScreeningEngine` supports four screening modes:

| Mode | Endpoint | Description |
|------|----------|-------------|
| Wallet | `POST /api/sanctions/screen/wallet` | Exact + normalized address match |
| Entity | `POST /api/sanctions/screen/entity` | Exact → alias → fuzzy name match |
| Transaction | `POST /api/sanctions/screen/transaction` | Screens both sender and receiver |
| Batch | `POST /api/sanctions/screen/batch` | Bulk wallet screening (up to 1000) |

**Fuzzy Matching Algorithm:**
- Jaccard similarity over word tokens
- Configurable threshold (default 0.8)
- Checks primary name, then aliases, then partial matches

**Caching:**
- Redis-backed with 5-minute TTL
- Graceful degradation if Redis unavailable
- Cache key: `sanctions_screen:{query_type}:{normalized_value}`

### 4. API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/sanctions/status` | User | Full status with screening stats |
| GET | `/api/sanctions/providers` | User | List all providers |
| GET | `/api/sanctions/providers/health` | User | Live health check |
| POST | `/api/sanctions/providers/{id}/toggle` | Admin | Enable/disable provider |
| POST | `/api/sanctions/sync` | Admin | Sync all providers |
| POST | `/api/sanctions/sync/{provider_id}` | Admin | Sync specific provider |
| GET | `/api/sanctions/scheduler` | User | Background scheduler status |
| GET | `/api/sanctions/check/{address}` | User | Quick wallet check |
| POST | `/api/sanctions/screen/wallet` | User | Full wallet screening |
| POST | `/api/sanctions/screen/entity` | User | Entity name screening |
| POST | `/api/sanctions/screen/transaction` | User | Transaction screening |
| POST | `/api/sanctions/screen/batch` | User | Batch wallet screening |
| GET | `/api/sanctions/entries` | User | Paginated entities |
| GET | `/api/sanctions/versions` | User | Version history |
| GET | `/api/sanctions/changes` | User | Change history |
| GET | `/api/sanctions/integrity-reports` | User | Integrity reports |
| GET | `/api/sanctions/screening-logs` | User | Screening audit logs |
| GET | `/api/sanctions/sync-logs` | User | Legacy sync logs |

### 5. Background Scheduler

Configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SANCTIONS_SYNC_INTERVAL_HOURS` | `24` | Hours between automatic syncs |
| `SANCTIONS_AUTO_SYNC_ON_STARTUP` | `false` | Sync immediately on app start |
| `SANCTIONS_HEALTH_CHECK_INTERVAL_MINUTES` | `60` | Minutes between health checks |

### 6. Security Considerations

- **Audit Trail**: Every screening event is logged immutably in `SanctionsScreeningLog`
- **RBAC**: Sync and provider management require supervisor/admin role
- **No Fabrication**: Empty databases return structured guidance, never fake data
- **Soft Delete**: Revoked entities are marked `status=revoked`, never hard-deleted
- **Rate Limiting**: Provider downloads are rate-limited to prevent endpoint abuse
- **Checksums**: SHA-256 validation on every downloaded feed

### 7. Deployment

```bash
# Required
export DATABASE_URL="postgresql://user:pass@host:5432/leatrace"

# Optional (enhances performance)
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

# Sanctions configuration
export SANCTIONS_SYNC_INTERVAL_HOURS="24"
export SANCTIONS_AUTO_SYNC_ON_STARTUP="true"

# Run
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 8. Testing

```bash
cd backend
# Provider tests
python -m pytest tests/test_sanctions_providers.py -v

# Screening engine tests
python -m pytest tests/test_sanctions_screening.py -v

# Full sanctions suite
python -m pytest tests/test_sanctions.py tests/test_sanctions_screening.py tests/test_sanctions_providers.py -v
```
