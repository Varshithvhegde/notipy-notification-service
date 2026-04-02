import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_user_preferences():
    print(f"--- Testing Step 2: User Preferences ---")
    user_id = "user_123"

    # 1. Set Preference (Opt-out of SMS)
    payload = {"channel": "sms", "is_opted_in": False}
    print(f"[*] Setting preference for {user_id}: {payload}")
    try:
        response = requests.post(f"{BASE_URL}/users/{user_id}/preferences", json=payload)
        response.raise_for_status()
        print(f"[+] Success! Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[-] Failed to set preference: {e}")

    # 2. Set Preference (Opt-in to Email)
    payload2 = {"channel": "email", "is_opted_in": True}
    print(f"[*] Setting preference for {user_id}: {payload2}")
    try:
        response = requests.post(f"{BASE_URL}/users/{user_id}/preferences", json=payload2)
        response.raise_for_status()
        print(f"[+] Success! Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[-] Failed to set preference: {e}")

    # 3. Get Preferences
    print(f"[*] Fetching preferences for {user_id}...")
    try:
        response = requests.get(f"{BASE_URL}/users/{user_id}/preferences")
        response.raise_for_status()
        print(f"[+] Success! Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[-] Failed to fetch preferences: {e}")

if __name__ == "__main__":
    print("Executing Live API Tests (Ensure server is running on port 8000)")
    # Check if server is up
    try:
        req = requests.get(f"{BASE_URL}/ping")
        print(f"Server health: {req.json()}")
        test_user_preferences()
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Server is not running! Please run: uvicorn app.main:app --reload")

