import subprocess
import time
import os

def run_script(script_name):
    print(f"\n" + "="*50)
    print(f"RUNNING: {script_name}")
    print("="*50)
    try:
        # Using sys.executable to ensure we use the same python environment
        import sys
        result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("ERRORS:")
            print(result.stderr)
    except Exception as e:
        print(f"Failed to run {script_name}: {e}")

def main():
    print("CYBER NECTAR - ADVERSARIAL TESTING WORKFLOW")
    print("This workflow follows Phases A-D of the testing plan.")
    
    # Phase A & B: Security & Misuse
    # (These require the honeypot_proxy to be running)
    print("\n[PHASE A & B] SECURITY & MISUSE TESTING")
    print("Note: Ensure honeypot_proxy.py is running on http://localhost:8080")
    
    scripts_ab = [
        "test_unauthorized.py",
        "test_log_tampering.py",
        "test_bypass.py"
    ]
    
    for s in scripts_ab:
        run_script(s)
    
    # Phase C: ML Validation
    # (These test the engine directly)
    print("\n[PHASE C] ML VALIDATION")
    scripts_c = [
        "test_ul_engine.py",
        "test_rl_policy.py"
    ]
    
    for s in scripts_c:
        run_script(s)

    # Phase D: Stress Testing
    print("\n[PHASE D] STRESS TESTING")
    print("Running rapid request test as stress baseline...")
    run_script("test_bypass.py") # Re-running bypass which includes rapid requests

if __name__ == "__main__":
    main()
