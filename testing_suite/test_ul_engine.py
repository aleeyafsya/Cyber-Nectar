import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unified_honeypot_engine import UnifiedHoneypotEngine

def test_ul_classification():
    print("\n--- Testing Unsupervised Learning Classification ---")
    engine = UnifiedHoneypotEngine()
    
    scenarios = [
        {"name": "Normal Traffic", "data": {"source_ip": "192.168.1.5", "path": "/index.html", "method": "GET"}},
        {"name": "Admin Probe", "data": {"source_ip": "1.2.3.4", "path": "/admin/login.php", "method": "GET"}},
        {"name": "SQL Injection", "data": {"source_ip": "5.6.7.8", "path": "/products?id=1' OR 1=1", "method": "GET"}},
        {"name": "RCE Attempt", "data": {"source_ip": "9.10.11.12", "path": "/cgi-bin/test.sh", "method": "POST"}},
        {"name": "Credential Access", "data": {"source_ip": "13.14.15.16", "path": "/etc/passwd", "method": "GET"}},
    ]
    
    print(f"{'Scenario':<20} | {'Threat Level':<12} | {'Action':<10}")
    print("-" * 50)
    
    for s in scenarios:
        result = engine.process_attack(s["data"])
        meta = result["engine_metadata"]
        print(f"{s['name']:<20} | {meta['threat_level']:<12} | {meta['rl_action']:<10}")

if __name__ == "__main__":
    test_ul_classification()
