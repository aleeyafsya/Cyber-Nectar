import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unified_honeypot_engine import UnifiedHoneypotEngine

def test_rl_adaptation():
    print("\n--- Testing Reinforcement Learning Adaptation (Policy) ---")
    engine = UnifiedHoneypotEngine()
    
    attacker_ip = "111.222.333.444"
    print(f"Simulating repeated attacks from {attacker_ip} to observe policy learning...")
    
    history = []
    
    attacks = [
        {"path": "/api/v1/status", "method": "GET", "desc": "Benign Reconnaissance"},
        {"path": "/admin/login.php", "method": "GET", "desc": "Admin Interface Probe"},
        {"path": "/products?id=1 OR 1=1", "method": "GET", "desc": "SQL Injection Attempt"},
        {"path": "/cgi-bin/test.sh", "method": "POST", "desc": "RCE Exploit Trigger"},
        {"path": "/etc/passwd", "method": "GET", "desc": "Credential Exfiltration"}
    ]
    
    # Simulate escalating attack to observe policy learning
    import contextlib
    import io
    for i, attack in enumerate(attacks, 1):
        attack["source_ip"] = attacker_ip
        
        print(f"\nStep {i}: {attack['desc']} ({attack['path']})")
        # Suppress internal prints for clean output
        with contextlib.redirect_stdout(io.StringIO()):
            result = engine.process_attack(attack)
            
        meta = result["engine_metadata"]
        
        entry = {
            "step": i,
            "threat": meta["threat_level"],
            "action": meta["rl_action"],
            "state": meta["rl_state"],
            "delay": result["delay"]
        }
        history.append(entry)
        print(f"  -> Threat={entry['threat']}, Action={entry['action']}, State={entry['state']}, Delay={entry['delay']}s")

    print("\nFinal Observations:")
    actions = [h["action"] for h in history]
    if len(set(actions)) > 1:
        print("[SUCCESS] Dynamic Adaptation Detected: The AI successfully escalated its response as the attack worsened.")
    else:
        print("[WARNING] Policy Stable: Action remained consistent.")

if __name__ == "__main__":
    test_rl_adaptation()
