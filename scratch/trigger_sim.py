import requests

base_url = "http://127.0.0.1:8000"

login_data = {
    "username": "auditor.gupta@cybercrime.gov.in",
    "password": "SecurePass@2026"
}
r = requests.post(f"{base_url}/api/auth/login", data=login_data)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("Triggering simulate POST request...")
sim_response = requests.post(f"{base_url}/api/wallets/simulate", headers=headers)
print("Status Code:", sim_response.status_code)
print("Response JSON:", sim_response.json())
