import requests
import time
import os

class HardwareBridge:
    def __init__(self, enabled=True):
        self.enabled = enabled
        # default to localhost for Windows. Docker will override this via Env Var if needed.
        self.relay_url = os.environ.get("RELAY_URL", "http://localhost:5000")
        
        if self.enabled:
            self._check_relay()

    def _check_relay(self):
        try:
            print(f"Connecting to Host Relay at {self.relay_url}...")
            response = requests.get(f"{self.relay_url}/alert", params={"level": "NORMAL"}, timeout=2)
            if response.status_code == 200:
                print("Hardware Bridge (Relay Mode) active.")
            else:
                print(f"Warning: Host Relay returned status {response.status_code}")
        except Exception as e:
            print(f"Notice: Host Relay not reachable. Make sure 'hardware_relay.py' is running on Windows.")

    def send_alert(self, threat_level):
        """
        Sends the alert command to the Host Relay.
        threat_level: CRITICAL, MEDIUM, or NORMAL
        """
        if not self.enabled:
            return

        try:
            params = {"level": threat_level}
            target = f"{self.relay_url}/alert"
            print(f"DEBUG: HardwareBridge sending {threat_level} to {target}")
            requests.get(target, params=params, timeout=1.5)
            print(f"Sent {threat_level} alert signal to Host Relay.")
        except Exception as e:
            print(f"Failed to reach Host Relay at {self.relay_url}: {e}")

    def close(self):
        pass

# example usage
if __name__ == "__main__":
    # Test block
    bridge = HardwareBridge(enabled=True) 
    if bridge.enabled:
        bridge.send_alert("CRITICAL")
        time.sleep(2)
        bridge.send_alert("NORMAL")
