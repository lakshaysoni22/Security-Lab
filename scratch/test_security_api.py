import requests

base_url = "http://127.0.0.1:8000"

print("--- Testing Auditor Verification ---")

# 1. Login as Auditor
login_data = {
    "username": "auditor.gupta@cybercrime.gov.in",
    "password": "SecurePass@2026"
}
r = requests.post(f"{base_url}/api/auth/login", data=login_data)
print("Auditor login status:", r.status_code)
login_res = r.json()

# Auditor has mfa_enabled = False by default, so we get direct token
token = login_res["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Verify audit log chain
r = requests.get(f"{base_url}/api/audit/verify", headers=headers)
print("Auditor Ledger verification status:", r.status_code)
print("Auditor Ledger verification result:", r.json())
