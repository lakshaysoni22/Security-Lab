import requests

base_url = "http://127.0.0.1:8000"

print("--- Testing Connected AI Investigation Engine ---")

# 1. Test CPOS process with high-risk input (should trigger auto-case generation)
cpos_payload = {
    "input": "ALERT: Fraudulent mixer interaction on suspect address 0x71c20e241775e5332f143715df332f143789a71b transferring ransomware gains",
    "mode": "deep"
}
r = requests.post(f"{base_url}/cpos/process", json=cpos_payload)
print("CPOS Process Status Code:", r.status_code)
cpos_res = r.json()
print("CPOS Process Result:", cpos_res)

# Extract generated case ID
case_id = cpos_res.get("auto_case_id")
print(f"Auto-generated Case ID from CPOS: {case_id}")

# 2. Test Fraud detection (should trigger auto-case generation since score >= 0.8)
fraud_payload = {
    "transaction_id": "tx_fa7b9c0d1e2f3a4b5",
    "amount": 1420.5,
    "mixer_used": True,
    "rapid_transactions": True
}
r = requests.post(f"{base_url}/investigation/detect-fraud", json=fraud_payload)
print("\nFraud Check Status Code:", r.status_code)
fraud_res = r.json()
print("Fraud Check Result:", fraud_res)

# 3. Test AI Reasoning Chain
r = requests.get(f"{base_url}/investigation/reasoning-chain/{case_id}")
print("\nAI Reasoning Chain Status Code:", r.status_code)
print("AI Reasoning Chain JSON keys:", r.json().keys())
print("Verdict:", r.json()["verdict"])

# 4. Test Cross-Case Pattern Recognition
r = requests.get(f"{base_url}/investigation/pattern-recognition")
print("\nCross-Case Pattern Recognition Status Code:", r.status_code)
print("Patterns Detected:", r.json()["cross_case_patterns_detected"])
print("Repeat Offenders Mapped:", len(r.json()["repeat_offenders"]))
