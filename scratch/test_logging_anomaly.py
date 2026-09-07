import requests
import os

base_url = "http://127.0.0.1:8000"

def test_anomaly_system():
    print("--- Testing Compliance Auditing & Anomaly Engine ---")

    # 1. Login with bad credentials 3 times to trigger brute force anomaly
    print("\n[Test 1] Executing 3 consecutive failed login attempts...")
    for i in range(3):
        login_data = {
            "username": "auditor.gupta@cybercrime.gov.in",
            "password": "WrongPasswordX"
        }
        r = requests.post(f"{base_url}/api/auth/login", data=login_data)
        print(f"Failed Attempt {i+1} Status:", r.status_code)

    # 2. Login with correct credentials to perform verification calls
    print("\nLogging in with correct credentials...")
    login_data = {
        "username": "auditor.gupta@cybercrime.gov.in",
        "password": "SecurePass@2026"
    }
    r = requests.post(f"{base_url}/api/auth/login", data=login_data)
    if r.status_code != 200:
        print("Login failed with correct credentials!")
        return
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Verify Alerts endpoint contains the brute-force anomaly
    print("\n[Test 2] Fetching platform alerts...")
    alerts_response = requests.get(f"{base_url}/api/wallets/alerts", headers=headers)
    print("Alerts count:", len(alerts_response.json()))
    brute_force_alerts = [a for a in alerts_response.json() if a.get("type") == "brute_force_attack"]
    print("Brute-force Anomaly alerts found:", len(brute_force_alerts))
    if brute_force_alerts:
        print("Alert Message:", brute_force_alerts[0].get("message"))

    # 4. Verify Audit Logs and Ledger Chain Verification
    print("\n[Test 3] Fetching audit logs...")
    audit_response = requests.get(f"{base_url}/api/audit/logs", headers=headers)
    print("Audit logs count:", len(audit_response.json()))
    
    print("\n[Test 4] Verifying cryptographic ledger chain integrity...")
    verify_response = requests.get(f"{base_url}/api/audit/verify", headers=headers)
    print("Ledger verification status:", verify_response.json())

    # 5. Check SIEM log file
    print("\n[Test 5] Inspecting local SIEM log file...")
    siem_path = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "logs", "LEAtTrace_siem.log")
    if os.path.exists(siem_path):
        print("SIEM Log File Exists. Last 2 entries:")
        with open(siem_path, "r") as f:
            lines = f.readlines()
            for line in lines[-2:]:
                print(line.strip())
    else:
        print("SIEM Log File Not Found at", siem_path)

if __name__ == "__main__":
    test_anomaly_system()
