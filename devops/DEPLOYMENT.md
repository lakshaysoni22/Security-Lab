# LEAtTrace Enterprise Deployment & Operations Manual

This guide outlines deployment steps, disaster recovery plans, and monitoring operations for the LEAtTrace platform in a production cloud environment.

---

## 🏛️ Deployment Architecture Overview

LEAtTrace uses a highly available microservices model:
* **Frontend**: React + Vite SPA, served via NGINX with TLS 1.3.
* **Backend**: FastAPI Web Gateway, running inside EKS/GKE.
* **Graph Engine**: Neo4j Community (Bolt port 7687) with in-memory NetworkX fallback.
* **Warehouse**: ClickHouse Columnar Database for index logs with SQLite fallback.
* **Orchestration**: Managed Kubernetes pods with Horizontal Autoscalers.

---

## 🚀 Step 1: Provisioning Infrastructure via IaC

Deploy AWS network subnets, EKS Kubernetes nodes, RDS, and ElastiCache:
```bash
cd devops/terraform
terraform init
terraform plan -out=tfplan.out
terraform apply tfplan.out
```

---

## 🔒 Step 2: SSL/TLS Let's Encrypt Certbot Automation

1. Install Certbot on the NGINX host:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx -y
   ```
2. Request wildcard SSL certificate:
   ```bash
   sudo certbot certonly --webroot -w /var/www/certbot \
     -d LEAtTrace.cybercrime.gov.in \
     --email admin@cybercrime.gov.in --agree-tos --no-eff-email
   ```
3. NGINX will automatically read the certificates from `/etc/letsencrypt/live/`. To schedule automatic renewal twice daily, verify the systemd cron job:
   ```bash
   sudo systemctl status certbot.timer
   ```

---

## 🟢 Step 3: Zero-Downtime Blue-Green Switchover

When deploying a new version (e.g. updating image tag via CI/CD):
1. Apply the new manifest (e.g. target `green` pods):
   ```bash
   kubectl apply -f devops/kubernetes/k8s-deployment.yaml
   ```
2. Wait for liveness/readiness probes to pass:
   ```bash
   kubectl rollout status deployment/LEAtTrace-backend-green -n LEAtTrace-prod
   ```
3. Once green pods are healthy, patch the Active Service Selector to switch traffic:
   ```bash
   kubectl patch service LEAtTrace-backend-service -n LEAtTrace-prod -p '{"spec":{"selector":{"version":"green"}}}'
   ```
4. If smoke tests fail, immediately rollback to blue:
   ```bash
   kubectl patch service LEAtTrace-backend-service -n LEAtTrace-prod -p '{"spec":{"selector":{"version":"blue"}}}'
   ```

---

## 💾 Step 4: Disaster Recovery & Backup Restoration

### Recovery Metrics Targets
* **Recovery Point Objective (RPO)**: 1 Hour (Maximum data loss since last backup).
* **Recovery Time Objective (RTO)**: 15 Minutes (Maximum time to restore full service).

### Running Manual Backups
Run the disaster recovery script directly on the database node:
```bash
chmod +x devops/backups/disaster_recovery.sh
./devops/backups/disaster_recovery.sh
```

### Database Restoration Runbook
In case of server failure:
1. Extract the backup archive:
   ```bash
   tar -xzf LEAtTrace_backup_YYYYMMDD_HHMMSS.tar.gz
   ```
2. Restore PostgreSQL schemas:
   ```bash
   pg_restore -h localhost -U LEAtTrace_admin -d LEAtTrace -c postgres_YYYYMMDD_HHMMSS.dump
   ```
3. Restore Neo4j Database:
   ```bash
   docker exec -t LEAtTrace-neo4j neo4j-admin database load neo4j --from-path=./neo4j_YYYYMMDD_HHMMSS.dump --overwrite-destination=true
   ```
4. Restore ClickHouse analytical indexes:
   ```bash
   clickhouse-client --query="RESTORE TABLE indexed_transactions FROM File('./clickhouse_YYYYMMDD_HHMMSS.zip')"
   ```
