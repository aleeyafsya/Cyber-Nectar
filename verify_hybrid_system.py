import requests
import time
import json
import os

PROXY_URL = "http://127.0.0.1:8080" # run proxy dulu

def simulate_attack(name, path, method="GET"):
    print(f"\n[TEST] {name}: {method} {path}")
    try:
        start_time = time.time()
        response = requests.request(method, f"{PROXY_URL}{path}", timeout=15)
        duration = time.time() - start_time
        
        print(f"      Status:   {response.status_code}")
        print(f"      Delay:    {duration:.2f}s")
        print(f"      Response: {response.text[:50]}...")
        return response.status_code
    except Exception as e:
        print(f"      FAILED: {e}")
        return None

def verify_logs():
    print("\nVerifying 'hybrid_decisions.json' logs...")
    if not os.path.exists("hybrid_decisions.json"):
        print("      CRITICAL: Log file not found!")
        return
    
    with open("hybrid_decisions.json", "r") as f:
        lines = f.readlines()
        print(f"      Found {len(lines)} entries in log.")
        if lines:
            last_entry = json.loads(lines[-1])
            print(f"      Last Decision: {last_entry.get('threat_level')} -> {last_entry.get('rl_action')}")
            print(f"      UL Score:      {last_entry.get('ul_score')}")

if __name__ == "__main__":
    print("="*60)
    print("Hybrid AI Honeypot Verification Script")
    print("="*60)

    # 1. 
    # normal traffic (should be LOW -> ALLOW)
    simulate_attack("Normal User", "/index.html")
    simulate_attack("Safe API Call", "/api/v1/status")
    
    # 2. 
    # scanning (should be MEDIUM/HIGH -> CHALLENGE/BLOCK)
    simulate_attack("Vulnerability Scanner", "/cgi-bin/config.sh")
    simulate_attack("Admin Panel Hunt", "/admin/login.php")
    
    # 3. 
    # exploitation (should be CRITICAL -> ISOLATE)
    simulate_attack("Attacker Exploit", "/../../../etc/passwd")
    
    # 4. 
    # web application attacks (SQLi & XSS)
    simulate_attack("SQL Injection", "/login?user=admin' OR '1'='1")
    simulate_attack("XSS Payload", "/search?q=<script>alert('xss')</script>")
    
    # see results in log
    verify_logs()
    
    print("\n" + "="*60)
    print("Verification steps initiated.")
    print("="*60)
