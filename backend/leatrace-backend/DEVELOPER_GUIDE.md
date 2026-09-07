# LEAtTrace Developer Ecosystem & SDK Onboarding Guide

Welcome to the **LEAtTrace Developer Ecosystem**. This document outlines the API endpoints, SDK usage guides (Python & JavaScript), onboarding instructions, and local environment setups.

---

## 🌐 1. API Documentation (Swagger / OpenAPI)

The LEAtTrace Microservices Cluster exposes a centralized OpenAPI Gateway.

* **Base URL**: `https://api.LEAtTrace.io/v1/` (Production) or `http://localhost:8000/` (Local Development)
* **Interactive Documentation (Swagger)**: `/docs` (e.g. `http://localhost:8000/docs`)
* **Redoc Summary**: `/redoc`

### Core Microservice Mappings:
* **Auth Service** (Port 8001): `/auth/login`, `/auth/register`
* **CPOS Engine Service** (Port 8002): `/cpos/process`
* **RIIL Engine Service** (Port 8003): `/riil/ingest`, `/riil/state`
* **NGEL Governance Service** (Port 8004): `/ngel/evaluate`
* **QCAL Resolver Service** (Port 8005): `/qcal/resolve`
* **ARNS Loop Service** (Port 8006): `/arns/health`
* **Blockchain Tracing Service** (Port 8007): `/blockchain/trace`
* **AI Investigation Service** (Port 8008): `/investigation/cases/create`, `/investigation/detect-fraud`, `/investigation/forensic-report`

---

## 🐍 2. Python SDK Usage

Install the SDK via pip:
```bash
pip install LEAtTrace-sdk
```

Initialize the client and run a transaction analysis:
```python
from LEAtTrace import Client

# Initialize client using your API key or JWT Token
client = Client(api_key="YOUR_LEAtTrace_API_KEY")

# 1. Process Core Intelligence Decision (CPOS)
cpos_response = client.cpos.analyze(
    input="Analyze suspected routing address 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28",
    mode="deep"
)
print("CPOS Decision:", cpos_response.decision)
print("Confidence Score:", cpos_response.confidence)

# 2. Trace Suspected Mixer Hops
trace = client.blockchain.trace_wallet(
    address="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28",
    depth=3
)
print("Trace Graph Connections:", trace.connections)
print("Resolved Wallet Risk:", trace.risk_score)
```

---

## 🌐 3. JavaScript / TypeScript SDK Usage

Install the SDK via npm:
```bash
npm install LEAtTrace-sdk
```

Integrate wallet behavioral analytics into your app:
```javascript
import { LEAtTrace } from "LEAtTrace-sdk";

const client = new LEAtTrace("YOUR_LEAtTrace_API_KEY");

async function runAudit() {
  // Check governance constraints prior to transaction execution
  const policy = await client.ngel.evaluate({
    action: "execute_transfer",
    risk_level: "high"
  });

  if (policy.allowed) {
    const result = await client.cpos.process({
      input: "Execute automated fraud validation check"
    });
    console.log("Trace Resolved:", result.trace_id);
  } else {
    console.error("Governance Blocked:", policy.reason);
  }
}

runAudit();
```

---

## 🎓 4. Onboarding Checklist for Developers

1. **Register**: Register an investigator account to get a JWT token.
2. **Setup Credentials**: Include the token in the Headers of all your requests:
   ```text
   Authorization: Bearer <YOUR_JWT_TOKEN>
   ```
3. **Download Code**: Clone the repository and boot using Docker:
   ```bash
   git clone https://github.com/LEAtTrace/core.git
   cd LEAtTrace-backend
   docker-compose up --build
   ```
4. **Deploy Contracts**: Compile and deploy smart contracts on your testnet nodes.

---

## 🐳 5. Docker Compose & Local Run Config

To launch the entire microservice ecosystem, use:
```bash
# Docker Compose Run
docker-compose -f docker/docker-compose.yml up --build
```
Alternatively, for local debugging without Docker, use the parallel runner:
```bash
# Local Python Multi-process runner
python main.py
```

### Environment variables configuration (`.env`):
```text
DATABASE_URL=sqlite:///./LEAtTrace_micro.db
JWT_SECRET=super-secret-key-12345-cpos-singularity
MONGO_URL=mongodb://localhost:27017
REDIS_HOST=localhost
REDIS_PORT=6379
```
