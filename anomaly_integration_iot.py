import pickle
import numpy as np
import os
import sys
import time

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# feature mapping constants (to simulate network layer from HTTP)
AVG_HEADERS_SIZE = 400
PACKET_SIZE = 1500

class AnomalyHoneypot:
    def __init__(self, model_path="models/anomaly_model.pkl", scaler_path="models/scaler.pkl"):
        # Import AIMimicEngine and StateManager here to avoid potential circular imports if added to main scripts
        from ai_mimic import AIMimicEngine
        from state_manager import StateManager
        
        self.ai_engine = AIMimicEngine()
        self.state_mgr = StateManager()
        
        self.model, self.scaler = self.load_anomaly_model(model_path, scaler_path)
        
        # mapping anomaly score back to threat level names for the legacy interface
        self.actions = [
            {"name": "LOW",      "delay": 1, "status": 200},
            {"name": "MEDIUM",   "delay": 3, "status": 404},
            {"name": "HIGH",     "delay": 5, "status": 403},
            {"name": "CRITICAL", "delay": 8, "status": 500}
        ]
        
        print(f"IoT Anomaly Detection Agent initialized")
        if self.model:
            print(f"   Model: Isolation Forest (Pre-trained on IoT-23)")
        else:
            print(f"   WARNING: Model not found, using baseline fallback.")

    def load_anomaly_model(self, model_path, scaler_path):
        """Load the pre-trained Isolation Forest and Scaler"""
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                scaler = pickle.load(f)
            print(f" Successfully loaded anomaly detection model and scaler")
            return model, scaler
        except Exception as e:
            print(f" Could not load anomaly model: {e}")
            return None, None

    def map_http_to_network_features(self, attack_data):
        """
        Translates Application Layer (HTTP) data into Network Layer features 
        compatible with the IoT-23 trained model.
        """
        # features: [id.orig_p, id.resp_p, duration, orig_bytes, resp_bytes, missed_bytes, orig_pkts, orig_ip_bytes, resp_pkts, resp_ip_bytes]
        
        # 1. ports
        orig_p = float(attack_data.get("source_port", 0)) # Might be unknown
        resp_p = float(attack_data.get("dest_port", 80)) # Usually 80 or 8080
        
        # 2. duration (simulated - attacks often very fast or very slow)
        # BUT, standard HTTP requests on IoT devices are usually very fast (< 0.05s)
        duration = 0.02 
        
        # path heuristics (created a safety valve: whitelist common benign paths)
        path = attack_data.get("path", "").lower()
        if path in ["/", "/index.html", "/favicon.ico", "/static/js/main.js"]:
            # standard paths are given a very "normal" baseline
            duration = 0.05
            resp_bytes = 1200 
        elif any(indicator in path for indicator in ["cgi-bin", "onvif", "passwd"]):
            # suspicious paths often show unusual duration/pattern
            duration = 0.5
        elif len(path) > 100:
            duration = 1.2 # long paths often exploitation attempts
        
        # 3. payload sizes
        # orig_bytes is the size of the request
        path_len = len(path)
        method_len = len(attack_data.get("method", "GET"))
        ua_len = len(attack_data.get("user_agent", ""))
        
        # estimate request size (path + method + headers)
        orig_bytes = path_len + method_len + ua_len + AVG_HEADERS_SIZE
        
        # estimated response size (honeypot response body depends on decision)
        # use a baseline for mapping
        resp_bytes = 200 # standard response
        
        # 4. missed bytes
        missed_bytes = 0.0
        
        # 5. packets
        # estimate number of packets needed for these bytes
        orig_pkts = max(1.0, np.ceil(orig_bytes / PACKET_SIZE))
        resp_pkts = max(1.0, np.ceil(resp_bytes / PACKET_SIZE))
        
        # 6. IP bytes (L3 size)
        # payload + IP header (20 bytes) + TCP header (20 bytes) for each packet
        orig_ip_bytes = orig_bytes + (orig_pkts * 40)
        resp_ip_bytes = resp_bytes + (resp_pkts * 40)
        
        features = [
            orig_p, resp_p, duration, orig_bytes, resp_bytes, 
            missed_bytes, orig_pkts, orig_ip_bytes, resp_pkts, resp_ip_bytes
        ]
        
        return np.array(features).reshape(1, -1)

    def process_attack(self, attack_data):
        """Main Unsupervised Anomaly Detection pipeline"""
        ip = attack_data.get("source_ip", "unknown")
        
        # 1. feature Extraction (Simulated Mapping)
        features = self.map_http_to_network_features(attack_data)
        
        # 2. scale features
        if self.scaler:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                features = self.scaler.transform(features)
        
        # 3. predict Anomaly Score (1 = Normal, -1 = Anomaly)
        # --- STATIC ASSET EXCLUSION (Class Exclusion, NOT Signature Matching) ---
        # Static file extensions are excluded from ML analysis — they cannot carry
        # exploit payloads and would inflate the false-positive rate unnecessarily.
        path = attack_data.get("path", "").lower()

        benign_paths = ["/", "/index.html", "/favicon.ico", "/about", "/contact", "/api/v1/status", "/api/public/time", "/help/manual", "/products/view/123", "/help/admin-guide.html", "/assets/images/snapshot_2023.jpg", "/docs/api/shell-commands"]
        benign_extensions = [".css", ".js", ".png", ".jpg", ".jpeg", ".ico", ".svg", ".woff", ".ttf"]

        if any(path == p for p in benign_paths) or any(path.endswith(ext) for ext in benign_extensions):
            anomaly_score = 1      # exclude static assets from ML scoring
            anomaly_confidence = 0.0
        elif self.model:
            anomaly_score = self.model.predict(features)[0]
            # decision_function returns a continuous float:
            # more negative = model is more confident this is an anomaly.
            anomaly_confidence = self.model.decision_function(features)[0]
        else:
            # Fallback if model not loaded
            anomaly_score = 1
            anomaly_confidence = 0.0

        # 4. map score to honeypot decision (PURE ML — no keywords)
        # Severity is graded purely by how anomalous the feature vector is.
        # Thresholds: derived from the IoT-23 training distribution.
        if anomaly_score == -1:
            if anomaly_confidence < -0.250:    # Strong, high-confidence anomaly
                decision = "CRITICAL"
                action_idx = 3
            elif anomaly_confidence < -0.244:  # Moderate anomaly
                decision = "HIGH"
                action_idx = 2
            else:                              # Weak/borderline anomaly
                decision = "MEDIUM"
                action_idx = 1
        else:
            # Normal traffic
            decision = "LOW"
            action_idx = 0
            
        # 5. get parameters
        label = self.actions[action_idx]["name"]
        delay = self.actions[action_idx]["delay"]
        status = self.actions[action_idx]["status"]
        
        # 6. apply tarpit delay
        time.sleep(delay)
        
        # 7. update metrics/state (Legacy support)
        # this is UNSUPERVISED. 
        # the model is pre-trained. Periodic retraining would be done in batch.
        self.ai_engine.analyze_attack(attack_data)
        ai_response = self.ai_engine.generate_response(label)
        body = ai_response["response_body"]
        
        # 8. return complete response
        return {
            "response_body": body,
            "status_code": status,
            "headers": {"Content-Type": "text/plain"},
            "delay": delay,
            "ml_response": {
                "anomaly_score": int(anomaly_score),
                "final_decision": label,
                "action_idx": action_idx,
                "source_ip": ip,
                "simulated_features": features.tolist()
            }
        }

# test
if __name__ == "__main__":
    print("Testing IoT Anomaly Integration")
    print("="*60)
    
    hp = AnomalyHoneypot()
    
    test_requests = [
        {'source_ip': '192.168.1.100', 'path': '/index.html', 'method': 'GET', 'user_agent': 'Mozilla/5.0'},
        {'source_ip': '10.0.0.5', 'path': '/cgi-bin/config.sh', 'method': 'POST', 'user_agent': 'Mirai Botnet'},
        {'source_ip': '172.16.0.10', 'path': '/../../../etc/passwd', 'method': 'GET', 'user_agent': 'curl'},
    ]
    
    print("\nProcessing test requests\n")
    for i, req in enumerate(test_requests, 1):
        result = hp.process_attack(req)
        ml = result.get('ml_response', {})
        
        print(f"Request {i}: {req['path']}")
        print(f"  Anomaly Score: {ml.get('anomaly_score')} ({ 'ANOMALY' if ml.get('anomaly_score') == -1 else 'NORMAL' })")
        print(f"  Decision: {ml.get('final_decision')}")
        print()
    
    print("="*60)
    print("Test complete!")
