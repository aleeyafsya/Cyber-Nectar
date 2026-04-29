from collections import defaultdict

class StateManager:
    def __init__(self):
        self.ips = defaultdict(lambda: {
            "req_count": 0,
            "uniq_paths": set(),
            "consecutive_403": 0,
            "container_id": None,
            "time_in_container": 0
        })
    
    def get_state(self, attack_data, threat_level=None):
        """Generate state from attack features"""
        ip = attack_data.get("source_ip", "unknown")
        session = self.ips[ip]
        
        # update session tracking
        session["req_count"] += 1
        session["uniq_paths"].add(attack_data.get("path", "/"))
        
        path = attack_data.get("path", "/").lower()
        
        # === THREAT LEVEL (UL-first approach) ===
        if threat_level:
            threat = threat_level
        else:
            # fallback to rule-based logic (Legacy/Baseline)
            # CRITICAL: Path traversal or known high-severity camera exploits
            if any(indicator in path for indicator in [
                "..", "../", "../../", 
                "device.rsp", "system/deviceinfo",
                "current_config/passwd"
            ]):
                threat = "CRITICAL"
            
            # HIGH: Camera configuration and command interfaces
            elif any(indicator in path for indicator in [
                "onvif", "goform", "hi3510",
                "snapshot.cgi", "video.cgi",
                "cgi-bin", "camera", "stream",
                "admin", "login", "setup"
            ]):
                threat = "HIGH"
            
            # MEDIUM: Reconnaissance, scanning for generic router/IoT
            elif any(indicator in path for indicator in [
                "boaform", "test", "debug",
                ".env", "api/", "status.json"
            ]):
                threat = "MEDIUM"
            
            # LOW: Everything else
            else:
                threat = "LOW"
        
        # === ENGAGEMENT LEVEL ===
        if session["req_count"] == 1:
            engagement = "NEW"
        elif session["req_count"] < 5:
            engagement = "LOW_ENG"
        else:
            engagement = "HIGH_ENG"
        
        # === SUSPICIOUS LEVEL ===
        suspicious = "SUSP" if len(session["uniq_paths"]) >= 3 else "CLEAN"
        
        # === CONTAINER (simplified) ===
        container = session.get("container_id") or "default"
        
        # Return state (4 components: threat_engagement_suspicious_container)
        return f"{threat}_{engagement}_{suspicious}_{container}"
    
    def update(self, attack_data, label, container, delay):
        """Update session state after action"""
        ip = attack_data["source_ip"]
        session = self.ips[ip]
        
        session["last_label"] = label
        session["consecutive_403"] += 1 if label == "HIGH" else 0
        session["container_id"] = container
        session["time_in_container"] += delay
        
        # Return next state
        return self.get_state(attack_data)

# Test the state manager
if __name__ == "__main__":
    print("Testing State Manager")
    print("="*60)
    
    sm = StateManager()
    
    test_attacks = [
        {'source_ip': '10.0.0.1', 'path': '/'},
        {'source_ip': '10.0.0.1', 'path': '/snapshot.cgi'},
        {'source_ip': '10.0.0.1', 'path': '/onvif/device_service'},
        {'source_ip': '10.0.0.2', 'path': '/../../../etc/passwd'},
        {'source_ip': '10.0.0.3', 'path': '/current_config/passwd'},
    ]
    
    for attack in test_attacks:
        state = sm.get_state(attack)
        print(f"Path: {attack['path']:<30} -> State: {state}")
    
    print("="*60)
    print("Test complete!")