import requests

base_url = "http://127.0.0.1:8000"

def test_incident_system():
    print("--- Testing NIA-Level Incident Response System ---")

    # 1. Login to get JWT Token
    login_data = {
        "username": "auditor.gupta@cybercrime.gov.in",
        "password": "SecurePass@2026"
    }
    r = requests.post(f"{base_url}/api/auth/login", data=login_data)
    if r.status_code != 200:
        print("Login failed!")
        return
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test GET /api/incident/threats
    print("\n[Test 1] Fetching live threats dashboard stats...")
    threats_response = requests.get(f"{base_url}/api/incident/threats", headers=headers)
    print("Threats GET status:", threats_response.status_code)
    print("Threats level:", threats_response.json().get("active_threat_level"))
    print("Locked addresses count:", threats_response.json().get("lockdown_count"))
    print("Prioritized cases count:", len(threats_response.json().get("prioritized_cases", [])))

    # 3. Test POST /api/incident/prioritize-cases
    print("\n[Test 2] Triggering severity-based case prioritization recalibration...")
    pri_response = requests.post(f"{base_url}/api/incident/prioritize-cases", headers=headers)
    print("Prioritizer POST status:", pri_response.status_code)
    print("Prioritizer result:", pri_response.json())

    # 4. Test POST /api/incident/emergency-lockdown
    print("\n[Test 3] Triggering emergency lockdown on suspicous address...")
    lockdown_data = {
        "address": "1AMPLockdownProtocolTargetAddressX",
        "chain": "BTC",
        "notes": "Ransomware receiver suspect linked to co-spending group."
    }
    lock_response = requests.post(f"{base_url}/api/incident/emergency-lockdown", json=lockdown_data, headers=headers)
    print("Lockdown POST status:", lock_response.status_code)
    print("Lockdown result:", lock_response.json())

    # 5. Test POST /api/incident/escalate
    print("\n[Test 4] Triggering unread critical alert SLA escalations...")
    esc_response = requests.post(f"{base_url}/api/incident/escalate", headers=headers)
    print("Escalation POST status:", esc_response.status_code)
    print("Escalated alerts count:", esc_response.json().get("escalated_count"))
    print("Escalation notifications issued:", esc_response.json().get("escalation_messages"))

    # 6. Verify GET threats updates
    print("\n[Test 5] Fetching threats dashboard after lockdown & escalation...")
    threats_updated = requests.get(f"{base_url}/api/incident/threats", headers=headers)
    print("Updated lockdown count:", threats_updated.json().get("lockdown_count"))
    print("Locked list detail:", threats_updated.json().get("locked_addresses"))

if __name__ == "__main__":
    test_incident_system()
