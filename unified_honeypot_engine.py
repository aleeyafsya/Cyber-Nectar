import os
import sys
import time
import numpy as np
import pickle
from collections import defaultdict

# local directory to path for imports
sys.path.append(os.getcwd())

from anomaly_integration_iot import AnomalyHoneypot
from rl_integration_iot import RLEnhancedHoneypot
from state_manager import StateManager
from ai_mimic import AIMimicEngine
from hardware_bridge import HardwareBridge


class UnifiedHoneypotEngine:
    def __init__(self, mode="HYBRID"):
        print(f"Initialising Cyber Nectar (Mode: {mode})")
        
        # 1. 
        # detection layer (Unsupervised)
        self.detector = AnomalyHoneypot()
        
        # 2. 
        # state & history Management
        self.state_mgr = StateManager()
        
        # 3. 
        # adaptation Layer (RL)
        # use the logic from RLEnhancedHoneypot but handle initialisation ourselves
        self.rl_agent = RLEnhancedHoneypot()
        
        # 4. 
        # content Generation
        self.ai_mimic = AIMimicEngine()
        
        # 5.
        # hardware Alerting (Physical Response)
        self.hardware = HardwareBridge(enabled=True)
        
        self.actions = self.rl_agent.actions
        
        print(f"Unified Engine Ready")


    def process_attack(self, attack_data):
        """
        The core hybrid logic:
        1. UL Detector identifies the threat level.
        2. State Manager combines threat + history into a state.
        3. RL Agent selects an adaptive action.
        """
        # PHASE 1: DETECTION (UL)
        # anomaly_score: 1 = Normal, -1 = Anomaly
        features = self.detector.map_http_to_network_features(attack_data)
        if self.detector.scaler:
            features = self.detector.scaler.transform(features)
        
        if self.detector.model:
            anomaly_score = self.detector.model.predict(features)[0]
        else:
            anomaly_score = 1 # fallback
            
        # --- ENHANCED WHITELIST ---
        path = attack_data.get("path", "").lower()
        benign_paths = ["/", "/index.html", "/favicon.ico", "/about", "/contact", "/api/v1/status", "/api/public/time", "/help/manual", "/products/view/123"]
        benign_extensions = [".css", ".js", ".png", ".jpg", ".jpeg", ".ico", ".svg", ".woff", ".ttf"]
        
        if any(path == p for p in benign_paths) or any(path.endswith(ext) for ext in benign_extensions):
            anomaly_score = 1  # force anomaly score to normal
        
        # determine base threat level from anomaly score + path heuristics
        if anomaly_score == -1:
            if any(x in path for x in ["passwd", "bin/sh", "onvif"]):
                threat_level = "CRITICAL"
            elif any(x in path for x in ["cgi-bin", ".aspx", "sql", "exploit"]):
                threat_level = "HIGH"
            elif any(x in path for x in ["admin", ".php", "login", "setup"]):
                threat_level = "MEDIUM"
            else:
                threat_level = "MEDIUM"
        else:
            threat_level = "LOW"

        # PHASE 2: STATE AGGREGATION 
        # combine the UL detection with the session history
        state = self.state_mgr.get_state(attack_data, threat_level=threat_level)
        
        # PHASE 3: ADAPTATION (RL) 
        # use RL to pick the best action for this state
        action_idx = self.rl_agent.choose_action(state)
        label = self.actions[action_idx]["name"]
        delay = self.actions[action_idx]["delay"]
        status = self.actions[action_idx]["status"]
        
        # PHASE 4: EXECUTION & RESPONSE 
        # update state manager for next transition
        next_state = self.state_mgr.update(attack_data, label, "default", delay)
        
        # generate response body
        mimic_analysis = self.ai_mimic.analyze_attack(attack_data)
        attack_type = mimic_analysis.get('attack_type', 'Unknown Protocol')
        mimic_level = self.actions[action_idx]["mimic_level"]
        ai_response = self.ai_mimic.generate_response(mimic_level)
        
        # PHASE 5: PHYSICAL ALERT
        # Trigger ESP32 alerts based on the ADAPTIVE RL ACTION (label)
        # This makes the hardware "AI-Driven" instead of "Rule-Driven"

        if label in ["BLOCK", "ISOLATE"]:
            self.hardware.send_alert("CRITICAL")  # Red LED + Alarm
        elif label == "CHALLENGE":
            self.hardware.send_alert("MEDIUM")    # Yellow LED + Beep
        else:
            self.hardware.send_alert("NORMAL")    # Green LED

        return {
            "response_body": ai_response["response_body"],
            "status_code": status,
            "headers": {"Content-Type": "text/plain"},
            "delay": delay,
            "engine_metadata": {
                "detector_score": int(anomaly_score),
                "threat_level": threat_level,
                "rl_state": state,
                "rl_action": label,
                "attack_type": attack_type,
                "next_state": next_state
            }
        }


if __name__ == "__main__":
    print("Testing Unified Hybrid Engine")
    print("="*60)
    
    engine = UnifiedHoneypotEngine()
    
    test_scenarios = [
        {"source_ip": "1.1.1.1", "path": "/index.html", "method": "GET"},
        {"source_ip": "1.1.1.1", "path": "/admin/config.php", "method": "POST"},
        {"source_ip": "2.2.2.2", "path": "/etc/passwd", "method": "GET"},
    ]
    
    for i, attack in enumerate(test_scenarios, 1):
        print(f"\nScenario {i}: {attack['path']} from {attack['source_ip']}")
        result = engine.process_attack(attack)
        meta = result["engine_metadata"]
        print(f"  UL Detection: {meta['threat_level']} (Score: {meta['detector_score']})")
        print(f"  RL Action:    {meta['rl_action']}")
        print(f"  Final State:  {meta['next_state']}")
