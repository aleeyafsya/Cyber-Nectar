import pickle
import numpy as np
import random
import os
import sys
import time
from collections import defaultdict

sys.path.append("/app")
from ai_mimic import AIMimicEngine
from state_manager import StateManager

class RLEnhancedHoneypot:
    def __init__(self):
        self.ai_engine = AIMimicEngine()
        self.state_mgr = StateManager()
        self.q_table = self.load_rl_model()
        
        # Explicit mapping: RL action name -> Response Template Level
        self.actions = [
            {"name": "ALLOW",     "mimic_level": "LOW",      "delay": 1, "status": 200},
            {"name": "CHALLENGE", "mimic_level": "MEDIUM",   "delay": 3, "status": 404},
            {"name": "BLOCK",     "mimic_level": "HIGH",     "delay": 5, "status": 403},
            {"name": "ISOLATE",   "mimic_level": "CRITICAL", "delay": 8, "status": 500}
        ]
        
        self.epsilon = 0.10  # Exploration rate
        self.lr = 0.1        # Learning rate
        self.gamma = 0.90    # Discount factor
        self.training_mode = False
        
        print(f"IoT RL Agent initialized")
        print(f"   States: {len(self.q_table)}")
        print(f"   Epsilon: {self.epsilon}, LR: {self.lr}, Gamma: {self.gamma}")

    def load_rl_model(self):
        """Load pre-trained Q-table or create default"""
        try:
            with open("/app/data/rl_models/final_correct_agent.pkl", "rb") as f:
                model = pickle.load(f)
            
            q = defaultdict(lambda: np.zeros(4))
            q.update({k: np.array(v) for k, v in model["q_table"].items()})
            
            print(f"✅ Loaded pre-trained model with {len(q)} states")
            return q
            
        except Exception as e:
            print(f"Could not load model: {e}")
            print(f"   Creating default Q-table...")
            
            # Initialize with heuristics
            q = defaultdict(lambda: np.zeros(4))
            
            threats = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            engagements = ['NEW', 'LOW_ENG', 'HIGH_ENG']
            suspicious = ['CLEAN', 'SUSP']
            containers = ['default']
            
            for threat in threats:
                for eng in engagements:
                    for susp in suspicious:
                        for container in containers:
                            state = f"{threat}_{eng}_{susp}_{container}"
                            
                            # Heuristic initialization
                            if threat == 'CRITICAL':
                                q[state] = np.array([0.0, 0.0, 0.0, 10.0])
                            elif threat == 'HIGH':
                                q[state] = np.array([0.0, 0.0, 10.0, 0.0])
                            elif threat == 'MEDIUM':
                                q[state] = np.array([0.0, 10.0, 0.0, 0.0])
                            else:
                                q[state] = np.array([10.0, 0.0, 0.0, 0.0])
            
            return q

    def process_attack(self, attack_data):
        """Main RL processing pipeline"""
        ip = attack_data.get("source_ip", "unknown")
        
        # 1. Get current state from StateManager
        state = self.state_mgr.get_state(attack_data)
        
        # 2. Choose action (threat level)
        action_idx = self.choose_action(state)
        label = self.actions[action_idx]["name"]
        
        # 3. Always use default container for simple honeypot
        container = "default"
        
        # 4. Get action parameters
        delay = self.actions[action_idx]["delay"]
        status = self.actions[action_idx]["status"]
        
        # 5. Apply tarpit delay (waste attacker time)
        time.sleep(delay)
        
        # 6. Update state (for next request from this IP)
        next_state = self.state_mgr.update(attack_data, label, container, delay)
        
        # 7. Calculate reward (only if ground truth available)
        reward = 0
        if "label" in attack_data:
            reward = self.reward(attack_data["label"], label, delay, container)
        
        # 8. Q-learning update (training mode only)
        if self.training_mode and reward != 0:
            best_next = np.max(self.q_table[next_state])
            td_error = reward + self.gamma * best_next - self.q_table[state][action_idx]
            self.q_table[state][action_idx] += self.lr * td_error
        
        # 9. Generate response using AI engine
        # Pass the attack through analyze_attack so it logs history for the metrics dashboard 
        self.ai_engine.analyze_attack(attack_data)
        mimic_level = self.actions[action_idx]["mimic_level"]
        ai_response = self.ai_engine.generate_response(mimic_level)
        body = ai_response["response_body"]
        
        # 10. Return complete response
        return {
            "response_body": body,
            "status_code": status,
            "headers": {"Content-Type": "text/plain"},
            "delay": delay,
            "rl_response": {
                "state": state,
                "next_state": next_state,
                "final_decision": label,
                "action_idx": action_idx,
                "reward": reward,
                "q_values": self.q_table[state].tolist(),
                "container": container,
                "source_ip": ip
            }
        }

    def choose_action(self, state):
        """Epsilon-greedy action selection or rule-based fallback"""
        # If Q-table has no data for this state (all zeros), fallback to threat level logic
        if np.all(self.q_table[state] == 0) and not self.training_mode:
            threat = state.split('_')[0]
            if threat == 'CRITICAL': return 3 # ISOLATE
            if threat == 'HIGH': return 2 # BLOCK
            if threat == 'MEDIUM': return 1 # CHALLENGE
            return 0 # ALLOW
            
        if random.random() < self.epsilon:
            # Random exploration
            return random.randint(0, 3)
        else:
            # Exploitation (best known action)
            return int(np.argmax(self.q_table[state]))

    def reward(self, true_label, pred_label, delay, container):
        """Reward function - MUST MATCH training script!"""
        labels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        try:
            true_idx = labels.index(true_label)
            pred_idx = labels.index(pred_label)
        except ValueError:
            return -10.0
        
        # Base reward
        if true_label == pred_label:
            base = 10.0
        elif abs(true_idx - pred_idx) == 1:
            base = -2.0
        else:
            base = -10.0
        
        # Delay bonus (encourage tarpitting)
        delay_bonus = min(delay / 10, 5)
        
        # Container crash penalty (future: detect docker crashes)
        crash_penalty = -50 if container == "crashed" else 0
        
        return base + delay_bonus + crash_penalty

    def save_model(self, path="/app/data/rl_models/final_correct_agent.pkl"):
        """Save trained Q-table"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            model_data = {
                'q_table': {k: v.tolist() for k, v in self.q_table.items()},
                'actions': self.actions,
                'epsilon': self.epsilon,
                'lr': self.lr,
                'gamma': self.gamma
            }
            
            with open(path, 'wb') as f:
                pickle.dump(model_data, f)
            
            print(f"Model saved to {path}")
            return True
        except Exception as e:
            print(f"❌ Failed to save model: {e}")
            return False

# Test
if __name__ == "__main__":
    print("Testing IoT RL Integration")
    print("="*60)
    
    hp = RLEnhancedHoneypot()
    
    test_attacks = [
        {'source_ip': '192.168.1.100', 'path': '/snapshot.jpg', 'method': 'GET', 'user_agent': 'Camera_App'},
        {'source_ip': '10.0.0.5', 'path': '/admin', 'method': 'GET', 'user_agent': 'nmap'},
        {'source_ip': '10.0.0.5', 'path': '/cgi-bin/;/bin/sh', 'method': 'GET', 'user_agent': 'Mirai'},
        {'source_ip': '172.16.0.10', 'path': '/../../../etc/passwd', 'method': 'GET', 'user_agent': 'curl'},
    ]
    
    print("\nProcessing test attacks...\n")
    for i, attack in enumerate(test_attacks, 1):
        result = hp.process_attack(attack)
        rl = result.get('rl_response', {})
        
        print(f"Attack {i}: {attack['path']}")
        print(f"  State: {rl.get('state')}")
        print(f"  Decision: {rl.get('final_decision')}")
        print(f"  Container: {rl.get('container')}")
        print(f"  Q-values: {rl.get('q_values')}")
        print()
    
    print("="*60)
    print("Test complete!")