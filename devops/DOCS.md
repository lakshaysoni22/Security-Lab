# LEAtTrace Enterprise Operations & Infrastructure Manual

Welcome to the LEAtTrace Operations Manual. This guide details cloud provisioning, local deployment profiles, GitHub repository setups, and disaster recovery processes.

---

## 💻 1. Local Development Guide

### Prerequisites
* Docker Desktop (with WSL2 integration enabled on Windows).
* Node.js v20 (with `npm` CLI tool).
* Python 3.11.

### Initialization Commands
1. Run pre-requisite audits and generate loopback certificates:
   ```bash
   make setup
   ```
2. Start the local container services stack:
   ```bash
   make start
   ```
3. Check active services status:
   ```bash
   make status
   ```

---

## 🌐 2. GitHub Migration & Vercel Deployment Guide

### GitHub Onboarding
1. Create a PRIVATE repository named `LEAtTrace` on your GitHub account.
2. Initialize and push files:
   ```bash
   git init -b main
   git add .
   git commit -m "feat: initial enterprise release"
   git remote add origin https://github.com/YOUR_USERNAME/LEAtTrace.git
   git push -u origin main
   ```

### Vercel Deployment
1. Log in to Vercel and link the frontend project:
   ```bash
   npm install -g vercel
   vercel login
   vercel --cwd frontend
   ```
2. Configure environment overrides:
   * `VITE_API_URL`: Points to your backend API gateway (`https://api.LEAtTrace.cybercrime.gov.in`).
   * `VITE_WS_URL`: Points to the WebSocket alert streaming URL (`wss://api.LEAtTrace.cybercrime.gov.in/api/streaming`).

---

## ☁️ 3. Cloud Deployment Guide (Terraform + EKS)

Deploy AWS networking structures, EKS nodes, and multi-AZ databases:
1. Ensure AWS CLI credentials are configured (`aws configure` or environment variables).
2. Trigger the automated provisioning planner:
   ```bash
   make deploy
   ```
3. Validate cloud cluster health:
   ```bash
   powershell -File devops/scripts/validate-cloud.ps1
   ```

---

## 🔒 4. SSL / TLS Certificate Operations

The NGINX reverse proxy automates SSL/TLS based on your domain profiles:
* **Localhost / 127.0.0.1**: The setup script automatically issues self-signed TLS certificates and places them in `devops/nginx/certs/`.
* **Public Domain**: When the `LEAtTrace_DOMAIN` environment variable is defined with a public domain, the setup script executes Certbot challenge runs to verify domain ownership and downloads Let's Encrypt certificates.

---

## ☸️ 5. Kubernetes Helm Guide

Deploy raw manifests to standard clusters:
1. Helm deployment target command:
   ```bash
   helm upgrade --install LEAtTrace-deployment ./devops/kubernetes/helm-chart -n LEAtTrace-prod
   ```
2. Dynamic Horizontal Pod Autoscaling (HPA) rules scale backend pods from 3 to 10 replicas if CPU utilization exceeds 75%.

---

## 💾 6. Disaster Recovery Runbook

### Running Automated Backups
Run the backup sequence to save SQLite data, ClickHouse tables, and Neo4j graphs to `C:\var\backups\LEAtTrace\`:
```bash
make backup
```

### Running Database Restorations
To restore the latest backup in case of server failure:
```bash
make restore
```
