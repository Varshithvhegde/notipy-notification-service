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

def test_notifications():
    print(f"\n--- Testing Step 3: Notifications ---")
    user_id = "user_123"

    # 1. Send Notification
    payload = {
        "user_id": user_id,
        "channel": "email",
        "priority": "high",
        "message_body": "Hello {{name}}, your order has shipped!",
        "template_vars": {"name": "Varshith"},
        "idempotency_key": f"key_{int(time.time())}"
    }
    print(f"[*] Dispatching Notification: {payload}")
    noti_id = None
    try:
        response = requests.post(f"{BASE_URL}/notifications/", json=payload)
        response.raise_for_status()
        data = response.json()
        noti_id = data["id"]
        print(f"[+] Success! Notification created with status: {data['status']}, ID: {noti_id}")
    except requests.exceptions.RequestException as e:
        print(f"[-] Failed to create notification: {e}")

    if noti_id:
        # 2. Get Notification Status by ID
        print(f"[*] Fetching status for Notification ID: {noti_id}")
        try:
            response = requests.get(f"{BASE_URL}/notifications/{noti_id}")
            response.raise_for_status()
            print(f"[+] Status: {response.json()['status']}")
        except requests.exceptions.RequestException as e:
            print(f"[-] Failed to fetch notification status: {e}")

    # 3. Get User Notification History
    print(f"[*] Fetching User Notification History for {user_id}")
    try:
        response = requests.get(f"{BASE_URL}/notifications/user/{user_id}")
        response.raise_for_status()
        print(f"[+] Found {len(response.json())} notifications in history.")
    except requests.exceptions.RequestException as e:
        print(f"[-] Failed to fetch history: {e}")

def test_background_worker():
    print(f"\n--- Testing Step 4 & 5: Background Queue & Priority ---")
    user_id = "user_123"

    payload = {
        "user_id": user_id,
        "channel": "email",
        "priority": "critical",
        "message_body": "Priority dispatch test via Worker!",
        "idempotency_key": f"key_worker_{int(time.time())}"
    }

    try:
        res = requests.post(f"{BASE_URL}/notifications/", json=payload)
        res.raise_for_status()
        noti_id = res.json()["id"]
        print(f"[*] Dispatching to worker... created ID: {noti_id} (Status: pending)")
        
        print("[*] Waiting 1 second for worker to process...")
        time.sleep(1)
        
        chk = requests.get(f"{BASE_URL}/notifications/{noti_id}")
        print(f"[+] Post-worker status verification: {chk.json()['status']}")
    except requests.exceptions.RequestException as e:
        print(f"[-] Failed background test: {e}")

def test_idempotency_and_retries():
    print(f"\n--- Testing Step 7: Idempotency & Retries ---")
    user_id = "user_123"
    idempotency_key = f"idem_key_{int(time.time())}"

    payload = {
        "user_id": user_id,
        "channel": "push",
        "priority": "normal",
        "message_body": "Checking idempotency...",
        "idempotency_key": idempotency_key
    }

    try:
        print(f"[*] Request 1 with key '{idempotency_key}'...")
        res1 = requests.post(f"{BASE_URL}/notifications/", json=payload).json()
        print(f"[+] Created ID: {res1['id']}")

        print(f"[*] Request 2 with identical key...")
        res2 = requests.post(f"{BASE_URL}/notifications/", json=payload).json()
        print(f"[+] Returned ID: {res2['id']}")
        
        if res1["id"] == res2["id"]:
            print("[+] SUCCESS: Idempotency logic intercepted the duplicate request!")
        else:
            print("[-] FAILURE: Idempotency check did not catch duplicate.")
            
        print("[*] Let's check tracking schema features (delaying 2s explicitly to allow workers/retries)...")
        time.sleep(2)
        chk = requests.get(f"{BASE_URL}/notifications/{res1['id']}").json()
        print(f"[+] Delivery Status: {chk['status']}")
        print(f"[+] Number of Retries Executed: {chk.get('retry_count', 0)}")
        if chk.get('error_message'):
            print(f"[+] Caught Simulated Error: {chk['error_message']}")

    except requests.exceptions.RequestException as e:
        print(f"[-] Failed test: {e}")

def test_rate_limiter():
    print(f"\n--- Testing Step 8: Rate Limiting ---")
    user_id = "spam_user_99"
    payload = {
        "user_id": user_id,
        "channel": "push",
        "priority": "low",
        "message_body": "Spam message overload...",
        "idempotency_key": None
    }
    
    print(f"[*] Firing 101 requests for {user_id} in a tight loop...")
    caught_429 = False
    for i in range(101):
        try:
            res = requests.post(f"{BASE_URL}/notifications/", json=payload)
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            if res.status_code == 429:
                caught_429 = True
                print(f"[+] SUCCESS: Rate Limiter is ALIVE! Request {i+1} crashed with 429 Too Many Requests.")
                break
        except Exception:
            pass
            
    if not caught_429:
         print(f"[-] FAILURE: Rate Limiter failed to block exactly at 101st request.")

if __name__ == "__main__":
    print("Executing Live API Tests (Ensure server is running on port 8000)")
    try:
        req = requests.get(f"{BASE_URL}/ping")
        print(f"Server health: {req.json()}")
        test_user_preferences()
        test_notifications()
        test_background_worker()
        test_idempotency_and_retries()
        test_rate_limiter()
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Server is not running! Please run: uvicorn app.main:app --reload")
