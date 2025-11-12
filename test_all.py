import requests
import json
import time

BASE_URL = "http://localhost:8000/llm"

def print_response(resp):
    print(f"\n➡️  {resp.request.method} {resp.url}")
    print(f"Status: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)

def main():
    username = "test_user"
    password = "test_pass123"

    print("=== Health Check ===")
    try:
        r = requests.get("http://localhost:8000/")
        print_response(r)
    except Exception as e:
        print("❌ Could not reach server:", e)
        return

    # Register user (ignore 400 = already exists)
    print("\n=== Register User ===")
    data = {"username": username, "password": password}
    r = requests.post(f"{BASE_URL}/register", data=data)
    print_response(r)

    # Login to get token
    print("\n=== Login ===")
    r = requests.post(f"{BASE_URL}/token", data=data)
    print_response(r)
    if r.status_code != 200:
        print("❌ Login failed, aborting tests.")
        return
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update password
    print("\n=== Update Password ===")
    body = {"old_password": password, "new_password": "newpass1234"}
    r = requests.post(f"{BASE_URL}/update-password", headers=headers, json=body)
    print_response(r)

    # Manual password update (no token)
    print("\n=== Manual Password Update ===")
    r = requests.post(f"{BASE_URL}/manual-update-password",
                      json={"username": username, "old_password": "newpass1234", "new_password": password})
    print_response(r)

    # Re-login after password reset
    print("\n=== Re-Login ===")
    r = requests.post(f"{BASE_URL}/token", data=data)
    print_response(r)
    if r.status_code == 200:
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

    # Start new chat
    print("\n=== Chat (new conversation) ===")
    body = {"message": "Hello chatbot!", "new_chat": True}
    r = requests.post(f"{BASE_URL}/chat", headers=headers, json=body, stream=True)
    print(f"Status: {r.status_code}")
    conversation_id = None
    try:
        for line in r.iter_lines():
            if line:
                print(line.decode())
        if "X-Conversation-ID" in r.headers:
            conversation_id = r.headers["X-Conversation-ID"]
    except Exception as e:
        print("⚠️ Chat stream error:", e)

    # Conversion endpoint
    print("\n=== Conversion/Explain Endpoint ===")
    r = requests.post(f"{BASE_URL}/conversion", json={"message": "Explain Newton's second law"})
    print_response(r)

    # List conversations
    print("\n=== List Conversations ===")
    r = requests.get(f"{BASE_URL}/conversations", headers=headers)
    print_response(r)

    # Fetch single conversation (if exists)
    if conversation_id:
        print("\n=== Get Conversation ===")
        r = requests.get(f"{BASE_URL}/conversations/{conversation_id}", headers=headers)
        print_response(r)

        print("\n=== Debug Memory ===")
        r = requests.get(f"{BASE_URL}/debug/memory", headers=headers, params={"conversation_id": conversation_id})
        print_response(r)

        print("\n=== Delete Conversation ===")
        r = requests.delete(f"{BASE_URL}/conversations/{conversation_id}", headers=headers)
        print_response(r)
    else:
        print("⚠️ No conversation_id available; skipping conversation tests.")

    print("\n✅ All endpoint tests finished.")

if __name__ == "__main__":
    main()
