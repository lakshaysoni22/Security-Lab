# LEAtTrace Standard Operating Procedures (SOP)

This guide defines step-by-step procedures for routine administration tasks.

---

## 🔐 1. SOP: User Provisioning & MFA Setup
1. **Create Account**: Insert email and password in registration panel.
2. **Assign Role**: Assign RBAC role (e.g. `investigator`) and clearance level.
3. **MFA enrollment**: Generate TOTP secret hash. Present QR code in console.
4. **Validation**: Test token code via `/api/auth/mfa/verify`.

---

## 🌐 2. SOP: Production SSL Certificate Renewal
1. **Trigger Check**: run renewal verification script.
   ```powershell
   powershell -ExecutionPolicy Bypass -File devops/scripts/certbot-renew.ps1
   ```
2. **Challenge HTTP**: Certbot runs HTTP-01 challenge under `webroot`.
3. **Nginx reload**: Automatically executes reload:
   ```bash
   docker exec LEAtTrace-proxy nginx -s reload
   ```
