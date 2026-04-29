from flask import Flask, request, Response, jsonify, make_response
from flask_cors import CORS
from functools import wraps
import os, requests, json, datetime, sys, time

sys.path.append('/app/data')

try:
    from unified_honeypot_engine import UnifiedHoneypotEngine
    enhanced_honeypot = UnifiedHoneypotEngine()
    ML_AVAILABLE = True
except Exception as e:
    print(f"ERROR: Could not load Unified Hybrid Engine: {e}")
    ML_AVAILABLE = False
    enhanced_honeypot = None

app = Flask(__name__)
CORS(app) # CORS for flutter web
ESP32_IP = os.environ.get('ESP32_IP', '192.168.1.100') # default fallback IP

# security config 
API_SECRET_KEY = "fyp_secret_2026" # API key
VALID_USERNAME = "admin" # username
VALID_PASSWORD = "fyp26" # password

@app.after_request
def add_security_headers(response):
    """Adds OWASP recommended security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

def trigger_esp32_alarm(threat_level):
    """Sends a ping to the ESP32 physical alarm system for severe threats"""
    if threat_level in ["HIGH", "CRITICAL"]:
        try:
            # assumes ESP32 hosts a simple web server with an /alarm endpoint
            requests.get(f"http://{ESP32_IP}/alarm", params={"level": threat_level}, timeout=1.5)
            print(f"ALARM: ESP32 Triggered for {threat_level} threat!")
        except Exception as e:
            print(f"WARNING: Failed to reach ESP32 alarm at {ESP32_IP}: {e}")

def log_attack(req):
    attack_data = {
        'timestamp': datetime.datetime.now().isoformat(),
        'source_ip': req.remote_addr,
        'method': req.method,
        'path': req.path,
        'user_agent': req.headers.get('User-Agent'),
        'headers': dict(req.headers),
        'data': req.get_data().decode() if req.get_data() else None,
        'query_params': dict(request.args)
    }
    
    print(f"ATTACK LOGGED: {attack_data['source_ip']} -> {attack_data['method']} {attack_data['path']}")
    
    with open('attack_logs.json', 'a') as f:
        f.write(json.dumps(attack_data) + '\n')
        f.flush()
        os.fsync(f.fileno())
    
    return attack_data

def get_recent_attacks(n=20):
    try:
        with open('hybrid_decisions.json', 'r') as f:
            lines = f.readlines()
            recent = [json.loads(line) for line in lines[-n:]]
            return recent
    except:
        return []

# API SECURITY & ROUTES (for flutter dashboard)

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # always allow OPTIONS requests for CORS preflight
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
            
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_SECRET_KEY:
            print(f"SECURITY ALERT: Unauthorised API Access Attempt from {request.remote_addr}")
            return jsonify({"error": "Unauthorised. Missing or Invalid API Key."}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def api_login():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No credentials provided"}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        print(f"AUTH SUCCESS: User '{username}' logged in.")
        return jsonify({"success": True, "api_key": API_SECRET_KEY})
        
    print(f"AUTH FAILED: Invalid login attempt for '{username}'.")
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

@app.route('/api/metrics')
@require_api_key
def api_metrics():
    stats = {
        "total_attacks": 0,
        "agent_accuracy": 0,
        "threat_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
        "protocol_distribution": {},
        "avg_delay": 0.0,
        "last_attack_time": "None",
        "last_threat_level": "LOW"
    }
    
    try:
        if os.path.exists('hybrid_decisions.json'):
            with open('hybrid_decisions.json', 'r') as f:
                decisions = [json.loads(line) for line in f if line.strip()]
                
            if decisions:
                stats["total_attacks"] = len(decisions)
                
                # agreement map (action vs threat)
                mapping = {"LOW": "ALLOW", "MEDIUM": "CHALLENGE", "HIGH": "BLOCK", "CRITICAL": "ISOLATE"}
                correct = 0
                total_delays = 0
                
                # new breakdown trackers
                action_counts = {"BLOCK": 0, "ISOLATE": 0, "CHALLENGE": 0, "ALLOW": 0}
                delay_sums = {"LOW": 0.0, "MEDIUM": 0.0, "HIGH": 0.0, "CRITICAL": 0.0}
                threat_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
                
                for d in decisions:
                    threat = d.get("threat_level", "LOW")
                    action = d.get("rl_action", "ALLOW")
                    protocol = d.get("attack_type", "Unknown Protocol")
                    
                    # distribution stats
                    stats["threat_distribution"][threat] = stats["threat_distribution"].get(threat, 0) + 1
                    
                    # only include verified protocols in distribution (filter out legacy/unknown)
                    if protocol != "Unknown Protocol" and protocol != "Unknown":
                        stats["protocol_distribution"][protocol] = stats["protocol_distribution"].get(protocol, 0) + 1
                    
                    # action breakdown
                    if action in action_counts:
                        action_counts[action] += 1
                    
                    # accuracy calculation
                    if action == mapping.get(threat) or action == threat:
                        correct += 1
                    
                    # delay stats
                    entry_delay = 0
                    if "delay" in d:
                        entry_delay = float(d["delay"])
                    else:
                        delay_map = {"ALLOW": 1, "CHALLENGE": 3, "BLOCK": 5, "ISOLATE": 8,
                                    "LOW": 1, "MEDIUM": 3, "HIGH": 5, "CRITICAL": 8}
                        entry_delay = delay_map.get(action, 0)
                    
                    total_delays += entry_delay
                    delay_sums[threat] += entry_delay
                    threat_counts[threat] += 1

                stats["agent_accuracy"] = (correct / len(decisions)) * 100
                stats["avg_delay"] = total_delays / len(decisions)
                
                # calculate avg delay per threat level
                stats["delay_by_threat"] = {
                    level: (delay_sums[level] / threat_counts[level] if threat_counts[level] > 0 else 0.0)
                    for level in delay_sums
                }
                stats["action_distribution"] = action_counts
                
                stats["last_attack_time"] = decisions[-1].get("timestamp")
                stats["last_threat_level"] = decisions[-1].get("threat_level")

        return jsonify(stats)
    except Exception as e:
        print(f"API ERROR: {e}")
        return jsonify(stats)

@app.route('/api/live_attacks')
@require_api_key
def api_live_attacks():
    attacks = get_recent_attacks(50) # increased to 50 for the log page
    return jsonify(attacks)

# ==========================================
# HONEYPOT CATCH-ALL (Excludes API paths)
# ==========================================
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'])
@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'])
def honeypot_catch_all(path=''):
    # block API and internal healthchecks from the honeypot engine
    # if not, dia log the healthchecks dalam log (tak penting pun)
    if '/api' in request.path or '/stats' in request.path:
        return jsonify({"error": "Internal endpoint - use specific routes"}), 404
    
    attack_data = log_attack(request)
    
    if ML_AVAILABLE and enhanced_honeypot:
        # HERES THE CORE
        # the hybrid engine handles detection, RL action, and response generation
        response = enhanced_honeypot.process_attack(attack_data)
        meta = response.get('engine_metadata', {})
        threat_level = meta.get('threat_level', 'LOW')
        rl_action = meta.get('rl_action', 'ALLOW')
        
        print(f"Hybrid Engine Decision: {threat_level} -> {rl_action}")
        
        # trigger physical alarm for severe threats
        # (Now handled internally by the UnifiedHoneypotEngine serial bridge)
        # trigger_esp32_alarm(threat_level)
        
        # log hybrid decision for dashboard
        with open('hybrid_decisions.json', 'a') as f:
            f.write(json.dumps({
                'timestamp': datetime.datetime.now().isoformat(),
                'attack_data': attack_data,
                'threat_level': threat_level,
                'rl_action': rl_action,
                'attack_type': meta.get('attack_type', 'Unknown'),
                'delay': response.get('delay', 0),
                'ul_score': meta.get('detector_score')
            }) + '\n')
            f.flush()
            os.fsync(f.fileno())
            
        return Response(
            response.get('response_body', ''),
            status=response.get('status_code', 200),
            headers=response.get('headers', {})
        )
    return "RL Honeypot Active", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("="*60)
    print("Cyber Nectar")
    print(f"Port: {port}")
    print(f"Flutter APIs: /api/metrics, /api/live_attacks")
    print(f"ML Available: {ML_AVAILABLE}")
    print(f"ESP32 IP Target: {ESP32_IP}")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
