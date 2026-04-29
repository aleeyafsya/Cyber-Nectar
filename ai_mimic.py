# ai_mimic.py - Enhanced AI-powered honeypot response engine with ML
import json
import re
import time
import random
from datetime import datetime
import pickle
from collections import Counter

class SimpleMLClassifier:
    def __init__(self):
        self.attack_patterns = {}  # Learn from attacks
        
    def learn_from_attack(self, attack_data):
        """Simple frequency response learning"""
        path = attack_data.get('path', '')
        if path:
            self.attack_patterns[path] = self.attack_patterns.get(path, 0) + 1
        
    def predict_threat(self, path):
        """Predict threat based on frequency of path seen"""
        if not path:
            return 'LOW'
            
        freq = self.attack_patterns.get(path, 0)
        if freq > 5: 
            return 'HIGH'
        elif freq > 2: 
            return 'MEDIUM'
        else: 
            return 'LOW'

class AIMimicEngine:
    def __init__(self):
        self.attack_patterns = self.load_attack_patterns()
        self.response_templates = self.load_response_templates()
        self.attack_history = []
        self.ml_classifier = SimpleMLClassifier()  # Initialize ML classifier
        
    def load_attack_patterns(self):
        """Define common IoT IP Camera attack patterns"""
        return {
            'camera_critical_exploit': {
                'patterns': [r'device\.rsp', r'system/deviceinfo', r'current_config/passwd', r'\.\./', r'\.\.\\'],
                'threat_level': 'CRITICAL',
                'attack_type': 'Camera Config Disclosure'
            },
            'onvif_scanning': {
                'patterns': [r'onvif', r'device_service', r'media_service', r'ws-discovery'],
                'threat_level': 'HIGH',
                'attack_type': 'ONVIF Protocol Scan'
            },
            'camera_stream_hunting': {
                'patterns': [r'snapshot\.cgi', r'video\.cgi', r'stream', r'camera\.cgi', r'mjpeg'],
                'threat_level': 'HIGH',
                'attack_type': 'Stream/Snapshot Hunting'
            },
            'generic_router_cgi': {
                'patterns': [r'cgi-bin', r'\.cgi', r'goform', r'boaform', r'hi3510'],
                'threat_level': 'MEDIUM',
                'attack_type': 'Legacy CGI Scan'
            },
            'admin_bruteforce': {
                'patterns': [r'/admin', r'/login', r'/setup', r'/system'],
                'threat_level': 'MEDIUM',
                'attack_type': 'Admin Interface Scan'
            }
        }
    
    def load_response_templates(self):
        """Define realistic IP Camera device responses with strategic delays"""
        return {
            'CRITICAL': {
                'delay': 8,  # Maximum delay to waste attacker time
                'responses': [
                    "HTTP/1.0 401 Unauthorized\r\nWWW-Authenticate: Digest realm=\"Login to device\", qop=\"auth\"\r\n",
                    "<SOAP-ENV:Fault><faultcode>SOAP-ENV:Client</faultcode><faultstring>HTTP GET method not implemented</faultstring></SOAP-ENV:Fault>",
                    "Firmware: Checksum verification failed. Recovery mode activated.",
                    "Device Error: RTSP stream unavailable."
                ],
                'status_code': 500
            },
            'HIGH': {
                'delay': 5,
                'responses': [
                    "403 Forbidden - Access Denied by Access Control List",
                    "Session Expired: Re-authenticate to access video stream.",
                    "Maximum simultaneous streaming sessions reached.",
                    "<error>Invalid ONVIF profile</error>"
                ],
                'status_code': 403
            },
            'MEDIUM': {
                'delay': 3,
                'responses': [
                    "404 Not Found - The requested camera interface is not present.",
                    "Service Unavailable: Device undergoing maintenance.",
                    "400 Bad Request: Invalid endpoint.",
                ],
                'status_code': 404
            },
            'LOW': {
                'delay': 1,
                'responses': [
                    "IP Camera Web Interface v2.0",
                    "Status: Video Service Online",
                    "Welcome to Smart Camera Management",
                ],
                'status_code': 200
            }
        }
    
    def _combine_predictions(self, rule_threat, ml_threat):
        """Combine rule-based and ML predictions - take higher threat level"""
        threat_levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        
        rule_score = threat_levels.get(rule_threat, 1)
        ml_score = threat_levels.get(ml_threat, 1)
        
        # Take the higher (more conservative) threat level
        final_score = max(rule_score, ml_score)
        
        # Convert score back to threat level
        for threat, score in threat_levels.items():
            if final_score == score:
                return threat
        return 'MEDIUM'  # Default fallback
    
    def analyze_attack(self, attack_data):
        """Analyze the attack using both rule-based and ML approaches"""
        path = attack_data.get('path', '')
        user_agent = attack_data.get('user_agent', '')
        method = attack_data.get('method', '')
        data = attack_data.get('data', '')
        
        # Combine all text for pattern matching
        full_text = f"{path} {user_agent} {data}".lower()
        
        # Default response
        response = {
            'threat_level': 'LOW',
            'attack_type': 'Normal Traffic',
            'confidence': 0.0,
            'recommended_response': 'Normal',
            'delay': 1,
            'matched_patterns': [],
            'rule_prediction': 'LOW',
            'ml_prediction': 'LOW'
        }
        
        # RULE-BASED response
        max_confidence = 0
        rule_threat = 'LOW'
        for pattern_name, pattern_data in self.attack_patterns.items():
            for regex_pattern in pattern_data['patterns']:
                if (re.search(regex_pattern, path, re.IGNORECASE) or 
                    re.search(regex_pattern, user_agent, re.IGNORECASE) or
                    re.search(regex_pattern, str(data), re.IGNORECASE)):
                    
                    confidence = len(regex_pattern) / 10  # Simple confidence scoring
                    if confidence > max_confidence:
                        max_confidence = confidence
                        rule_threat = pattern_data['threat_level']
                        response.update({
                            'attack_type': pattern_data['attack_type'],
                            'confidence': min(confidence, 1.0),
                            'recommended_response': 'Deceive',
                            'matched_patterns': response['matched_patterns'] + [pattern_name]
                        })
        
        response['rule_prediction'] = rule_threat
        
        # ML PREDICTION
        ml_threat = self.ml_classifier.predict_threat(path)
        response['ml_prediction'] = ml_threat
        
        # COMBINE PREDICTIONS
        final_threat = self._combine_predictions(rule_threat, ml_threat)
        response['threat_level'] = final_threat
        
        # ML LEARNS FROM THIS ATTACK
        self.ml_classifier.learn_from_attack(attack_data)
        
        # Add delay based on FINAL threat level
        response_template = self.response_templates[response['threat_level']]
        response['delay'] = response_template['delay']
        
        # Store in history for learning
        self.attack_history.append({
            'timestamp': datetime.now().isoformat(),
            'response': response,
            'attack_data': attack_data
        })
        
        # Keep only recent history
        if len(self.attack_history) > 50:
            self.attack_history = self.attack_history[-50:]
            
        return response
    
    def generate_response(self, threat_level, original_response=""):
        """Generate a deceptive response with strategic delays"""
        template = self.response_templates[threat_level]
        
        # Strategic delays based on threat level
        delay_msg = f"AI: Delaying response by {template['delay']}s to waste attacker time..."
        print(delay_msg)
        time.sleep(template['delay'])
        
        # Choose deceptive response
        deceptive_response = random.choice(template['responses'])
        
        # Enhanced logging
        mimic_msg = f"AI: Sending deceptive response: '{deceptive_response}'"
        print(mimic_msg)
        
        return {
            'response_body': deceptive_response,
            'status_code': template['status_code'],
            'headers': {'Content-Type': 'text/plain'},
            'ai_response': {
                'response_type': 'deceptive',
                'threat_level': threat_level,
                'delay_applied': template['delay'],
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def get_attack_stats(self):
        """Get statistics about detected attacks"""
        if not self.attack_history:
            return {"total_attacks": 0}
        
        threat_levels = [a['response']['threat_level'] for a in self.attack_history]
        attack_types = [a['response']['attack_type'] for a in self.attack_history]
        
        # Count ML vs Rule disagreements
        ml_rule_disagreements = 0
        for a in self.attack_history:
            if a['response']['rule_prediction'] != a['response']['ml_prediction']:
                ml_rule_disagreements += 1
        
        return {
            "total_attacks": len(self.attack_history),
            "threat_distribution": {
                "CRITICAL": threat_levels.count("CRITICAL"),
                "HIGH": threat_levels.count("HIGH"),
                "MEDIUM": threat_levels.count("MEDIUM"),
                "LOW": threat_levels.count("LOW")
            },
            "common_attack_types": max(set(attack_types), key=attack_types.count) if attack_types else "None",
            "ml_rule_disagreements": ml_rule_disagreements,
            "ml_learned_patterns": len(self.ml_classifier.attack_patterns)
        }

# Test the enhanced AI engine
if __name__ == '__main__':
    ai = AIMimicEngine()
    
    # Pre-train ML with some repeated attacks
    print("Pre-training ML classifier with sample attacks...")
    training_paths = ['/admin', '/admin', '/admin', '/test', '/test', '/cgi-bin', '/login']
    for path in training_paths:
        ai.ml_classifier.learn_from_attack({'path': path})
    
    # Test cases
    test_attacks = [
        {'path': '/', 'user_agent': 'curl/7.68.0', 'method': 'GET', 'data': ''},
        {'path': '/admin', 'user_agent': 'nmap scanner', 'method': 'GET', 'data': ''},
        {'path': '/snapshot.cgi', 'user_agent': 'python-requests', 'method': 'GET', 'data': ''},
        {'path': '/onvif/device_service', 'user_agent': 'Mozilla/5.0', 'method': 'POST', 'data': ''},
        {'path': '/device.rsp', 'user_agent': 'scanner', 'method': 'GET', 'data': ''},
        {'path': '/test', 'user_agent': 'scanner', 'method': 'GET', 'data': ''},  # ML should detect repeated
    ]
    
    print("\n" + "=" * 70)
    print("ENHANCED AI MIMIC ENGINE TEST RESULTS (RULE + ML HYBRID)")
    print("=" * 70)
    
    for i, attack in enumerate(test_attacks, 1):
        print(f"\nTest {i}: {attack['path']}")
        print(f"   {'User Agent:':<20} {attack['user_agent']}")
        
        response = ai.analyze_attack(attack)
        
        print(f"   {'Rule-based:':<20} {response['rule_prediction']}")
        print(f"   {'ML Prediction:':<20} {response['ml_prediction']}")
        print(f"   {'Final Threat:':<20} {response['threat_level']}")
        print(f"   {'Attack Type:':<20} {response['attack_type']}")
        print(f"   {'Confidence:':<20} {response['confidence']:.2f}")
        print(f"   {'Delay Applied:':<20} {response['delay']}s")
        
        if response['matched_patterns']:
            print(f"   {'Matched Patterns:':<20} {', '.join(response['matched_patterns'])}")
    
    print("\n" + "=" * 70)
    stats = ai.get_attack_stats()
    print(" FINAL STATISTICS:")
    print(f"   Total Attacks: {stats['total_attacks']}")
    print(f"   Threat Distribution: {stats['threat_distribution']}")
    print(f"   Most Common Attack: {stats['common_attack_types']}")
    print(f"   ML vs Rule Disagreements: {stats['ml_rule_disagreements']}")
    print(f"   ML Learned Patterns: {stats['ml_learned_patterns']}")
    print("=" * 70)
    
    # Show ML's learned patterns
    print("\nML CLASSIFIER LEARNED PATTERNS:")
    for path, count in ai.ml_classifier.attack_patterns.items():
        print(f"   {path:<30} -> Seen {count} times")