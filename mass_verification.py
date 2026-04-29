import requests
import random
import time
import json
import os

PROXY_URL = "http://127.0.0.1:8080"

# CONFIGURATION 
TOTAL_REQUESTS = 30
BENIGN_RATIO = 0.3  # set 30% benign, 70% malicious

# PAYLOADS
BENIGN_PATHS = [
    "/", "/index.html", "/about", "/contact", "/api/v1/status", 
    "/static/style.css", "/assets/logo.png", "/favicon.ico",
    "/help/manual", "/products/view/123", "/api/public/time"
]

ATTACK_PATHS = [
    # SQL injection
    "/login?user=admin' OR '1'='1",
    "/api/users?id=1; DROP TABLE users",
    "/search?category=electronics' UNION SELECT username,password FROM users--",
    # XSS
    "/comment?text=<script>alert('pwned')</script>",
    "/profile/update?bio=<img src=x onerror=alert(1)>",
    "/forum/post?title=<svg/onload=alert(1)>",
    # path traversal
    "/../../etc/passwd",
    "/download?file=../../../../boot.ini",
    "/view_log?file=../../../../var/log/syslog",
    # sensitive file access
    "/.git/config",
    "/.env",
    "/phpmyadmin/index.php",
    "/wp-admin.php",
    # API scans / unauthenticated endpoints
    "/api/admin/config",
    "/api/debug/dump",
    "/v1/internal/secrets"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "python-requests/2.31.0",
    "sqlmap/1.7.5#stable",
    "Nikto/2.1.6",
    "Nmap Scripting Engine",
    "curl/7.81.0"
]

def run_simulation():
    print("="*60)
    print("- STARTING MASS VERIFICATION SIMULATION -")
    print(f"Targeting: {PROXY_URL}")
    print(f"Total Requests: {TOTAL_REQUESTS}")
    print("="*60)

    success_count = 0
    start_time = time.time()

    for i in range(1, TOTAL_REQUESTS + 1):
        # decide if this request is benign or an attack
        is_benign = random.random() < BENIGN_RATIO
        
        if is_benign:
            path = random.choice(BENIGN_PATHS)
            category = "BENIGN"
        else:
            path = random.choice(ATTACK_PATHS)
            category = "ATTACK"

        headers = {"User-Agent": random.choice(USER_AGENTS)}

        try:
            # short timeout to keep it fast
            response = requests.get(f"{PROXY_URL}{path}", headers=headers, timeout=5)
            status = response.status_code
            success_count += 1
        except Exception as e:
            status = "FAILED"
            print(f"  [{i:03}] Error: {e}")

        if i % 10 == 0:
            print(f"  [{i:03}/{TOTAL_REQUESTS}] Progress... {category} -> {path[:40]}... Status: {status}")
        
        # a tiny delay to keep from saturating the single-threaded Flask too hard, 
        # but fast enough to finish within ~30-60s
        time.sleep(0.1)

    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print(" SIMULATION COMPLETE")
    print(f"  Successful Requests: {success_count}/{TOTAL_REQUESTS}")
    print(f"  Elapsed Time:        {elapsed:.2f}s")
    print("="*60)
    print("\nNEXT STEPS:")
    print("Run 'python monitor_performance.py' for the final chart.")
    print("="*60)

if __name__ == "__main__":
    run_simulation()
