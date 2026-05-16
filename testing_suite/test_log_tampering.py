import requests
import os

BASE_URL = "http://localhost:8080"

def test_log_injection():
    print("\n--- Testing Log Injection Attempt ---")
    # Trying to inject newline characters or JSON fragments into logs
    malicious_payload = "test\n{\"timestamp\": \"2099-01-01T00:00:00\", \"threat_level\": \"LOW\"}"
    resp = requests.post(BASE_URL + "/contact", data=malicious_payload)
    print(f"Injection request status: {resp.status_code}")
    print("Check attack_logs.json to see if the injection broke the JSON structure.")

def test_log_file_permissions():
    print("\n--- Testing Log File Integrity ---")
    log_files = ["attack_logs.json", "hybrid_decisions.json"]
    for log in log_files:
        path = os.path.join("..", log) # Assuming running from testing_suite/
        if os.path.exists(path):
            size_before = os.path.getsize(path)
            print(f"Log file {log} exists. Size: {size_before} bytes.")
            # In a real environment, we'd check if a non-root user can delete it.
        else:
            print(f"Log file {log} not found at {path}")

if __name__ == "__main__":
    test_log_injection()
    test_log_file_permissions()
