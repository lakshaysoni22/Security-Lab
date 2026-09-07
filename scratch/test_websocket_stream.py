import asyncio
import websockets
import requests
import json

base_url = "http://127.0.0.1:8000"
ws_url = "ws://127.0.0.1:8000"

async def test_stream():
    print("--- Testing Real-Time Event Streaming System ---")

    # 1. Login to get JWT Token
    login_data = {
        "username": "auditor.gupta@cybercrime.gov.in",
        "password": "SecurePass@2026"
    }
    r = requests.post(f"{base_url}/api/auth/login", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Connect to WebSocket
    uri = f"{ws_url}/api/streaming/alerts?token={token}"
    print(f"Connecting to WebSocket: {uri}")
    
    # Increase open_timeout to 30 seconds to prevent handshake timeouts on slower systems
    async with websockets.connect(uri, open_timeout=30.0) as websocket:
        print("WebSocket connection established successfully!")
        
        # Trigger block simulation to generate events in background
        print("Triggering block simulation to publish transaction & alert events...")
        sim_response = requests.post(f"{base_url}/api/wallets/simulate", headers=headers)
        print("Simulation POST status:", sim_response.status_code)
        
        # Wait to receive streamed event
        try:
            print("Listening for streamed events...")
            # We set a timeout of 10 seconds to receive the event
            response_text = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            event_data = json.loads(response_text)
            print("\nSUCCESS: Streamed Event Received!")
            print("Event Details:", event_data)
        except asyncio.TimeoutError:
            print("\nERROR: Timeout reached before event was received over WebSocket stream.")
            exit(1)

if __name__ == "__main__":
    asyncio.run(test_stream())
