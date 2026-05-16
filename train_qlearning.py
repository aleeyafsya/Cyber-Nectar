
import numpy as np
import json
import os
from pathlib import Path

class QLearningTrainer:
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.alpha = alpha      # learning rate
        self.gamma = gamma      # discount factor
        self.epsilon = epsilon  # exploration rate
        
        # actions available
        self.actions = ["ALLOW", "CHALLENGE", "BLOCK", "ISOLATE"]
        
        # initialise Q-table
        self.q_table = {}
        
    def get_state_key(self, threat_level, engagement, suspicious, container_name):
        return f"{threat_level}_{engagement}_{suspicious}_{container_name}"
    
    def initialize_q_table(self):
        """Initialise Q-table with all possible states"""
        threat_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        engagements = ["NEW", "LOW_ENG", "HIGH_ENG"]
        suspicious_flags = ["CLEAN", "SUSP"]
        containers = ["default"]
        
        print("Initialising Q-table...")
        
        for threat in threat_levels:
            for engaged in engagements:
                for susp in suspicious_flags:
                    for container in containers:
                        state = self.get_state_key(threat, engaged, susp, container)
                        # initialise with small random values
                        self.q_table[state] = np.random.randn(len(self.actions)) * 0.01
        
        print(f"Initialised {len(self.q_table)} states")
        print(f"   States per threat level: {len(self.q_table) // 4}")
        
    def get_reward(self, threat_level, action, engagement, suspicious):
        """
        Define reward function based on IP Camera security best practices
        """
        is_suspicious = (suspicious == "SUSP")
        is_engaged = (engagement in ["LOW_ENG", "HIGH_ENG"])

        if threat_level == "LOW" and not is_suspicious and action != "ALLOW":
            return -6
        
        rewards = {
            # LOW threat
            "LOW": {
                "ALLOW": +20,     
                "CHALLENGE": -5,  
                "BLOCK": -15,     
                "ISOLATE": -25    
            },
            # MEDIUM threat
            "MEDIUM": {
                "ALLOW": -10,      
                "CHALLENGE": +20, # strictly prefer challenge
                "BLOCK": +5,      
                "ISOLATE": -10    
            },
            # HIGH threat
            "HIGH": {
                "ALLOW": -20,     
                "CHALLENGE": +0,  
                "BLOCK": +20,     # strictly prefer block
                "ISOLATE": +5    
            },
            # CRITICAL threat 
            "CRITICAL": {
                "ALLOW": -30,     
                "CHALLENGE": -10,  
                "BLOCK": +5,     
                "ISOLATE": +20    # strictly prefer isolate
            }
        }
        
        base_reward = rewards[threat_level][action]
        action_cost = {
            "ALLOW": 0,
            "CHALLENGE": -0.5,
            "BLOCK": -1,
            "ISOLATE": -2
        }

        base_reward += action_cost[action]
        
        # Modifiers
        if is_suspicious and action in ["BLOCK", "ISOLATE"]:
            base_reward += 5  # bonus for taking decisive action on highly suspicious activity
        
        if is_engaged and action == "BLOCK":
            base_reward -= 3  # penalty for blocking an engaged user (could be a legitimate video stream viewer)
        
        if not is_engaged and threat_level in ["HIGH", "CRITICAL"] and action == "ISOLATE":
            base_reward += 3  # bonus for immediately isolating hit-and-run critical threats
        
        return base_reward
    
    def choose_action(self, state):
        """Epsilon-greedy action selection"""
        if state not in self.q_table:
            # state not in table, initialise it
            self.q_table[state] = np.random.randn(len(self.actions)) * 0.01
        
        #CORE OF Q LEARNING
        # exploration vs exploitation
        if np.random.random() < self.epsilon:
            # explore: random action
            return np.random.randint(len(self.actions))
        else:
            # exploit: best known action
            return np.argmax(self.q_table[state])
    
    def update_q_value(self, state, action_idx, reward, next_state):
        """Update Q-value using Q-learning update rule"""
        if state not in self.q_table:
            self.q_table[state] = np.random.randn(len(self.actions)) * 0.01
        if next_state not in self.q_table:
            self.q_table[next_state] = np.random.randn(len(self.actions)) * 0.01
        
        # Q-learning update: Q(s,a) = Q(s,a) + α[r + γ max(Q(s',a')) - Q(s,a)]
        current_q = self.q_table[state][action_idx]
        max_next_q = np.max(self.q_table[next_state])
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state][action_idx] = new_q
    
    def generate_episode(self):
        """Generate a training episode (sequence of state transitions)"""
        # random starting state
        threat_level = np.random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        engagement = np.random.choice(["NEW", "LOW_ENG", "HIGH_ENG"])
        suspicious = np.random.choice(["CLEAN", "SUSP"])
        container = "default"
        
        state = self.get_state_key(threat_level, engagement, suspicious, container)
        
        # choose action
        action_idx = self.choose_action(state)
        action = self.actions[action_idx]
        
        # the get reward
        reward = self.get_reward(threat_level, action, engagement, suspicious)
        
        # simulate next state (with some randomness)
        next_threat = threat_level
        if action == "ALLOW":
            if suspicious == "SUSP" and np.random.random() > 0.8:
                threat_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                current_idx = threat_order.index(threat_level)
                if current_idx < len(threat_order) - 1:
                    next_threat = threat_order[current_idx + 1]

        elif action in ["BLOCK", "ISOLATE"]:
            # blocking/isolating reduces future threat
            next_threat = "LOW"
        
        next_engagement = engagement
        next_suspicious = "CLEAN" if action in ["BLOCK", "ISOLATE"] else suspicious
        
        next_state = self.get_state_key(next_threat, next_engagement, next_suspicious, container)
        
        # update Q-value
        self.update_q_value(state, action_idx, reward, next_state)
        
        return reward
    
    def train(self, episodes=10000):
        """Train the Q-learning agent"""
        print(f"\nTraining for {episodes} episodes...")
        print(f"   Learning rate (α): {self.alpha}")
        print(f"   Discount factor (γ): {self.gamma}")
        print(f"   Exploration rate (ε): {self.epsilon}\n")
        
        rewards_history = []
        
        for episode in range(episodes):
            self.epsilon = max(0.01, self.epsilon * 0.9995)
            reward = self.generate_episode()
            rewards_history.append(reward)
            
            # report progress
            if (episode + 1) % 1000 == 0:
                avg_reward = np.mean(rewards_history[-1000:])
                print(f"Episode {episode + 1}/{episodes} - Avg Reward: {avg_reward:.2f}")
        
        print("\nTraining complete!")
        print(f"   Final 1000 episodes avg reward: {np.mean(rewards_history[-1000:]):.2f}")
    
    def save_q_table(self, filepath="models/q_table.json", pkl_filepath="final_correct_agent.pkl"):
        """Save Q-table to JSON and Pickle files"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # convert numpy arrays to lists for JSON serialisation
        q_table_serializable = {
            state: values.tolist() 
            for state, values in self.q_table.items()
        }
        
        with open(filepath, 'w') as f:
            json.dump(q_table_serializable, f, indent=2)
            
        import pickle
        model_data = {
            'q_table': q_table_serializable,
            'actions': [{"name": "ALLOW", "delay": 0}, {"name": "CHALLENGE", "delay": 2}, {"name": "BLOCK", "delay": 5}, {"name": "ISOLATE", "delay": 10}],
            'epsilon': self.epsilon,
            'lr': self.alpha,
            'gamma': self.gamma
        }
        with open(pkl_filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"\nQ-table saved to {filepath} and {pkl_filepath}")
    
    def print_policy(self):
        """Print the learned policy (best action for each state)"""
        print("\nLearned Policy:")
        print("=" * 60)
        
        for state in sorted(self.q_table.keys()):
            best_action_idx = np.argmax(self.q_table[state])
            best_action = self.actions[best_action_idx]
            q_values = self.q_table[state]
            
            print(f"{state:40} → {best_action:10} {q_values}")
        
        print("=" * 60)
    
    def analyze_q_table(self):
        """Analyse Q-table statistics"""
        print("\nQ-Table Analysis:")
        print("=" * 60)
        
        # Count states by threat level
        threat_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for state in self.q_table.keys():
            threat = state.split('_')[0]
            if threat in threat_counts:
                threat_counts[threat] += 1
        
        print("States by threat level:")
        for threat, count in threat_counts.items():
            print(f"  {threat:10}: {count:3} states")
        
        print(f"\nTotal states: {len(self.q_table)}")
        
        # sample state format check
        sample_state = list(self.q_table.keys())[0]
        components = sample_state.split('_')
        print(f"\nSTATE FORMAT CHECK:")
        print(f"  Sample state: {sample_state}")
        print(f"  Components: {len(components)} parts")
        print(f"  Format: {' + '.join(components)}")
        print(f"  Expected: threat_engagement_suspicious_container")
        
        if len(components) == 4:
            print(f"  CORRECT: 4 components as expected")
        else:
            print(f"  WRONG: Expected 4 components, got {len(components)}")


def main():
    print("=" * 60)
    print("Q-Learning Training - Fixed State Format")
    print("=" * 60)
    
    # create trainer
    trainer = QLearningTrainer(
        alpha=0.1,   # learning rate
        gamma=0.9,   # discount factor
        epsilon=0.1  # exploration rate
    )
    
    # initialise Q-table
    trainer.initialize_q_table()
    
    # train
    trainer.train(episodes=50000)
    
    # show results
    trainer.print_policy()
    trainer.analyze_q_table()
    
    # save Q-table
    trainer.save_q_table("models/q_table.json")
    
    print("\n" + "=" * 60)
    print("Training complete! Q-table ready for deployment.")
    print("=" * 60)


if __name__ == "__main__":
    main()