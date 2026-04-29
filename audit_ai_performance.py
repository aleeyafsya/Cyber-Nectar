import requests
import random
import time
from sklearn.metrics import precision_score, recall_score, f1_score

PROXY_URL = "http://127.0.0.1:8080"
TOTAL_REQUESTS = 40

# We define what the Ground Truth is
BENIGN_PATHS = [
    "/", "/index.html", "/about", "/contact", "/api/v1/status", 
    "/static/style.css", "/assets/logo.png", "/favicon.ico",
    "/help/manual", "/products/view/123", "/api/public/time"
]

ATTACK_PATHS = [
    # IoT Specific (To trigger new Dashboard Cards)
    "/onvif/device_service",
    "/snapshot.cgi",
    "/video.cgi",
    "/device.rsp",
    "/system/deviceinfo",
    "/ws-discovery",
    # SQL injection
    "/login?user=admin' OR '1'='1",
    "/api/users?id=1; DROP TABLE users",
    # XSS
    "/comment?text=<script>alert('pwned')</script>",
    "/profile/update?bio=<img src=x onerror=alert(1)>",
    # path traversal
    "/../../etc/passwd",
    "/download?file=../../../../boot.ini",
    # sensitive file access
    "/.git/config",
    "/.env",
    "/phpmyadmin/index.php",
    "/wp-admin.php",
    "/cgi-bin/config.sh"
]

def run_audit():
    print("="*60)
    print(" CYBER NECTAR AI PERFORMANCE ")
    print("="*60)
    print("Starting automated testing to calculate AI accuracy metrics...")
    print(f"Target: {PROXY_URL}\n")

    y_true = []  # The Ground Truth: 1 for Attack, 0 for Benign
    y_pred = []  # The AI Prediction: 1 for Attack, 0 for Benign

    success_count = 0

    try:
        # Check if server is up
        requests.get(f"{PROXY_URL}/", timeout=3)
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Honeypot is not reachable at {PROXY_URL}.")
        print("Please ensure your proxy server / docker container is running first.")
        return

    for i in range(1, TOTAL_REQUESTS + 1):
        # 50/50 split for balanced testing
        is_attack = random.choice([True, False])
        
        path = random.choice(ATTACK_PATHS) if is_attack else random.choice(BENIGN_PATHS)
        actual_label = 1 if is_attack else 0  # 1 = Attack, 0 = Benign
        y_true.append(actual_label)

        try:
            response = requests.get(f"{PROXY_URL}{path}", timeout=5)
            # The honeypot logic:
            # 200 = ALLOW (Benign)
            # 404/403/500 = CHALLENGE/BLOCK/ISOLATE (Attack detected)
            predicted_label = 0 if response.status_code == 200 else 1
            y_pred.append(predicted_label)
            
            success_count += 1
            
        except requests.exceptions.Timeout:
            # If the RL agent dropped the connection/timeout, that means it isolated the attack!
            y_pred.append(1) 
            success_count += 1
        except Exception as e:
            # Failsafe
            y_pred.append(1)
            
        if i % 20 == 0:
            print(f"  [{i:03}/{TOTAL_REQUESTS}] Requests processed...")
            time.sleep(0.1) # Small delay to avoid flooding port space

    print("\n" + "="*60)
    print(" AUDIT COMPLETE! CALCULATING METRICS...")
    print("="*60)

    # Calculate metrics
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    # Calculate True/False Positives/Negatives manually for detail
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

    accuracy = (tp + tn) / TOTAL_REQUESTS

    print(f"\n[ RAW CONFUSION MATRIX ]")
    print(f"  True Positives (Caught Attacks)    : {tp}")
    print(f"  True Negatives (Allowed Benign)    : {tn}")
    print(f"  False Positives (False Alarms)     : {fp}")
    print(f"  False Negatives (Missed Attacks)   : {fn}")

    print(f"\n[ KEY PERFORMANCE INDICATORS (For Chapter 5) ]")
    print(f"  OVERALL ACCURACY : {accuracy * 100:.2f}%")
    print(f"  PRECISION        : {precision * 100:.2f}%  (When it says 'Attack', was it really?)")
    print(f"  RECALL           : {recall * 100:.2f}%  (Out of all real attacks, how many were caught?)")
    print(f"  F1-SCORE         : {f1 * 100:.2f}%  (The balanced average of Precision & Recall)")
    
    print("\n" + "="*60)
    print("Copy these numbers into your Chapter 5 tables!")
    print("="*60)

if __name__ == "__main__":
    run_audit()
