import requests
import json

BASE_URL = "http://localhost:8080"
API_KEY = "fallback_secret_key" # Change this if you have a real one in .env

def test_admin_access():
    print("\n--- Testing Unauthorized Admin Access ---")
    # Attempting to access dashboard APIs without key
    endpoints = ["/api/metrics", "/api/live_attacks"]
    for ep in endpoints:
        resp = requests.get(f"{BASE_URL}{ep}")
        print(f"GET {ep} (No Key): {resp.status_code} - Expected: 401")
        
        resp = requests.get(f"{BASE_URL}{ep}", headers={"X-API-Key": "wrong_key"})
        print(f"GET {ep} (Wrong Key): {resp.status_code} - Expected: 401")

def test_honeypot_protected_paths():
    print("\n--- Testing Honeypot Protected Paths ---")
    paths = ["/admin", "/config.php", "/.env", "/setup"]
    for path in paths:
        resp = requests.get(f"{BASE_URL}{path}")
        print(f"GET {path}: {resp.status_code} - Action: Check logs for detection")

def test_login_bruteforce():
    print("\n--- Testing Login Brute Force ---")
    url = f"{BASE_URL}/api/login"
    payloads = [
        {"username": "admin", "password": "wrongpassword"},
        {"username": "hacker", "password": "password123"},
        {"username": "admin", "password": "password123"} # Correct one
    ]
    for payload in payloads:
        resp = requests.post(url, json=payload)
        print(f"Login attempt {payload['username']}:{payload['password']} - Status: {resp.status_code}")

if __name__ == "__main__":
    try:
        test_admin_access()
        test_honeypot_protected_paths()
        test_login_bruteforce()
    except Exception as e:
        print(f"Error connecting to server: {e}. Is the honeypot running?")
