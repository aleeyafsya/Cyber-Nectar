import requests
import time

BASE_URL = "http://localhost:8080"

def test_rapid_requests():
    print("\n--- Testing Tarpit Stability (Rapid Requests) ---")
    start_time = time.time()
    for i in range(10):
        try:
            resp = requests.get(BASE_URL + "/fast-scan")
            print(f"Request {i+1}: {resp.status_code} (Took {resp.elapsed.total_seconds():.2f}s)")
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
    end_time = time.time()
    print(f"Total time for 10 requests: {end_time - start_time:.2f}s")

def test_malformed_requests():
    print("\n--- Testing Malformed Requests (Fuzzing) ---")
    # Sending weird headers, methods, and payloads
    fuzz_cases = [
        {"method": "TRACE", "path": "/"},
        {"method": "GET", "path": "/%00/etc/passwd"},
        {"method": "POST", "path": "/", "headers": {"User-Agent": "() { :;}; /bin/bash -c 'echo vulnerable'"}}, # Shellshock pattern
        {"method": "GET", "path": "/?" + "a"*1000} # Long query param
    ]
    
    for case in fuzz_cases:
        try:
            resp = requests.request(case["method"], BASE_URL + case["path"], headers=case.get("headers"))
            print(f"{case['method']} {case['path']}: {resp.status_code}")
        except Exception as e:
            print(f"Fuzz case failed: {e}")

if __name__ == "__main__":
    test_rapid_requests()
    test_malformed_requests()
