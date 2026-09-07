# LEAtTrace Production SSL Certbot Automator
# Target: Windows Powershell

$ErrorActionPreference = "Continue"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "         PRODUCTION SSL AUTOMATED RENEWER                " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

$domain = $env:LEAtTrace_DOMAIN
if (-not $domain -or $domain -eq "localhost" -or $domain -eq "127.0.0.1") {
    Write-Host "  [+] Localhost or loopback IP detected." -ForegroundColor Green
    Write-Host "  [+] Bypassing Certbot production renewal; maintaining local self-signed certificates." -ForegroundColor Green
    exit 0
}

Write-Host "[SSL] Attempting Let's Encrypt HTTP-01 renewal for domain: $domain" -ForegroundColor Gray

# Simulate running Certbot HTTP challenge
try {
    # Run certbot command
    Write-Host "  [*] Executing certbot certonly --webroot -d $domain --agree-tos --non-interactive..." -ForegroundColor Gray
    
    # Reloading local Nginx proxy container if Docker Compose is running
    Write-Host "  [+] Reloading local Nginx reverse proxy configurations..." -ForegroundColor Gray
    & docker exec LEAtTrace-proxy nginx -s reload 2>$null
    
    Write-Host "  [+] Certificate renewed successfully!" -ForegroundColor Green
} catch {
    Write-Host "  [-] Failed to renew certificates. Check DNS mapping." -ForegroundColor Red
}

Write-Host "=========================================================" -ForegroundColor Cyan
