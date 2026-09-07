import requests

base_url = "http://127.0.0.1:8000"

print("--- Testing Advanced Blockchain Intelligence Endpoints ---")

# 1. Login to get token
login_data = {
    "username": "auditor.gupta@cybercrime.gov.in",
    "password": "SecurePass@2026"
}
r = requests.post(f"{base_url}/api/auth/login", data=login_data)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

test_address = "0x71c20e241775e5332f143715df332f143789a71b"

# 2. Check RPC status
r = requests.get(f"{base_url}/api/wallets/rpc-status", headers=headers)
print("RPC Status Code:", r.status_code)
print("RPC Status JSON:", r.json())

# 3. Check Wallet Clustering
r = requests.get(f"{base_url}/api/wallets/cluster/{test_address}", headers=headers)
print("\nClustering Status Code:", r.status_code)
print("Clustering JSON:", r.json())

# 4. Check Mixer Exposure
r = requests.get(f"{base_url}/api/wallets/mixer-check/{test_address}", headers=headers)
print("\nMixer Check Status Code:", r.status_code)
print("Mixer Check JSON:", r.json())

# 5. Check Cross-Chain Bridge Trace
r = requests.get(f"{base_url}/api/wallets/cross-chain-trace/{test_address}", headers=headers)
print("\nCross-Chain Trace Status Code:", r.status_code)
print("Cross-Chain Trace JSON:", r.json())

# 6. Decode Event Log
decode_payload = {
    "topics": [
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        "0x00000000000000000000000071c20e241775e5332f143715df332f143789a71b",
        "0x000000000000000000000000ab5801a7d398351b8be11c439e05c5b3259aec9b"
    ],
    "data": "0x0000000000000000000000000000000000000000000000000de0b6b3a7640000" # 1 ETH
}
r = requests.post(f"{base_url}/api/wallets/decode-log", json=decode_payload, headers=headers)
print("\nLog Decode Status Code:", r.status_code)
print("Log Decode JSON:", r.json())
