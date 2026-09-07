# LEAtTrace Enterprise Automation Makefile
# Targets run PowerShell commands natively on Windows platforms

.PHONY: setup start deploy deploy-aws deploy-gcp deploy-azure update rollback backup restore destroy validate status prepare verify

prepare:
	@echo "==> Configuring Git safety rules and hooks..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/prepare-github.ps1

validate:
	@echo "==> Running prerequisite diagnostics validation audits..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/validate-all.ps1
	powershell -ExecutionPolicy Bypass -File devops/scripts/validate-cloud.ps1

deploy:
	@echo "==> Initializing Terraform IaC modules and cloud provisioning..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/deploy-cloud.ps1
	powershell -ExecutionPolicy Bypass -File devops/scripts/helm-deploy.ps1

deploy-aws:
	@echo "==> Starting AWS bootstrap deployment wizard..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/deploy-aws.ps1

deploy-gcp:
	@echo "==> Starting GCP bootstrap deployment wizard..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/deploy-gcp.ps1

deploy-azure:
	@echo "==> Starting Azure bootstrap deployment wizard..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/deploy-azure.ps1

verify:
	@echo "==> Running pre-push security audits on workspaces..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/verify-github.ps1

update:
	@echo "==> Pulling updates and applying rolling releases..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/update.ps1

rollback:
	@echo "==> Rolling back deployments to last stable release..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/rollback-cloud.ps1

backup:
	@echo "==> Generating database backups and state snapshots..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/backup.ps1

start:
	@echo "==> Starting backend, frontend and opening browser simultaneously..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/start-all.ps1

restart:
	@echo "==> Starting backend, frontend and opening browser simultaneously..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/start-all.ps1

restore:
	@echo "==> Restoring database states from backup files..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/restore.ps1

destroy:
	@echo "==> Stopping services and tearing down infrastructure..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/destroy.ps1

status:
	@echo "==> Opening diagnostics operations status dashboard..."
	powershell -ExecutionPolicy Bypass -File devops/scripts/status.ps1
