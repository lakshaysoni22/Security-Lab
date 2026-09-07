# LEAtTrace Architecture Decision Records (ADR)

This document maps structural decisions, alternatives considered, and trade-offs.

---

## ⚡ ADR 001: FastAPI for Backend Services
* **Status**: Accepted
* **Context**: Need high-throughput async processing for block indexers and SIEM WebSocket log streams.
* **Decision**: Selected FastAPI (Python 3).
* **Alternatives Considered**: Django REST Framework (blocked by heavy synchronous DB bindings).
* **Consequences**: Fast JSON validation via Pydantic, automatic Swagger docs, and excellent async speed.

---

## 🕸️ ADR 002: Neo4j Community Edition with NetworkX Fallback
* **Status**: Accepted
* **Context**: Wallet transaction tracking requires recursive path tracing (peel chains, co-spending).
* **Decision**: Selected Neo4j for query optimizations, using NetworkX as a local zero-install fallback.
* **Consequences**: High-performance Cypher queries for relational maps; works seamlessly on laptops without database configuration.

---

## 🔐 ADR 003: OAuth2 & OpenID Connect (OIDC) Server Architecture
* **Status**: Accepted
* **Context**: Need Zero-Trust authentication and compliance with identity federation standards.
* **Decision**: Implemented an OpenID Connect compliant endpoints server using PKCE flow and token rotation.
* **Consequences**: Secure investigator login; federates with external government OIDC portals.
