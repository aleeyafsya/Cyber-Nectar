import json
import os
from collections import Counter

LOG_FILE = "hybrid_decisions.json"

def analyze_logs():
    if not os.path.exists(LOG_FILE):
        print(f"Error: {LOG_FILE} not found. Have you run any attacks yet?")
        return

    decisions = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                decisions.append(json.loads(line))
            except:
                continue

    total = len(decisions)
    if total == 0:
        print("No logs recorded yet.")
        return

    print("\n" + "="*60)
    print(f" CYBER NECTAR PERFORMANCE MONITOR (Total Requests: {total})")
    print("="*60)

    # calculate Agreement / Accuracy
    # expected mapping:
    # LOW -> ALLOW, MEDIUM -> CHALLENGE, HIGH -> BLOCK, CRITICAL -> ISOLATE
    expected_mapping = {
        "LOW": "ALLOW",
        "MEDIUM": "CHALLENGE",
        "HIGH": "BLOCK",
        "CRITICAL": "ISOLATE"
    }

    correct_decisions = 0
    threats = []
    actions = []
    
    for d in decisions:
        threat = d.get("threat_level", "LOW")
        action = d.get("rl_action", "ALLOW")
        threats.append(threat)
        actions.append(action)

        if action == expected_mapping.get(threat) or action == threat:
            correct_decisions += 1

    accuracy = (correct_decisions / total) * 100
    print(f"\n[ System Accuracy (RL/UL Agreement Rate) ]")
    print(f"  Accuracy: {accuracy:.2f}% ({correct_decisions}/{total} optimal decisions)")
    
    # to keep track of minimum 80% accuracy
    if accuracy < 80:
        print("  🔴 Accuracy is below 80%. Consider retraining the RL Agent or adding more diverse data.")
    else:
        print("  🟢 Accuracy is solid.")

    # distribution
    threat_counts = Counter(threats)
    action_counts = Counter(actions)
    
    print("\n[ Threat Level Distribution ]")
    for level, count in threat_counts.items():
        print(f"  {level:10}: {count} ({(count/total)*100:.1f}%)")
        
    print("\n[ RL Action Distribution ]")
    for action, count in action_counts.items():
        print(f"  {action:10}: {count} ({(count/total)*100:.1f}%)")

    # ML anomaly score
    scores = [d.get("ul_score") for d in decisions]
    score_counts = Counter(scores)
    print("\n[ AI Detector (UL) Stats ]")
    print(f"  Normal behavior (1) : {score_counts.get(1, 0)}")
    print(f"  Anomalies detected (-1): {score_counts.get(-1, 0)}")

    # untuk generate Chart
    try:
        import matplotlib.pyplot as plt
        
        # prepare data for plotting
        labels = ['LOW/ALLOW', 'MED/CHAL', 'HIGH/BLOCK', 'CRIT/ISO']
        threat_vals = [threat_counts.get("LOW", 0), threat_counts.get("MEDIUM", 0), 
                      threat_counts.get("HIGH", 0), threat_counts.get("CRITICAL", 0)]
        action_vals = [action_counts.get("ALLOW", action_counts.get("LOW", 0)), 
                       action_counts.get("CHALLENGE", action_counts.get("MEDIUM", 0)), 
                       action_counts.get("BLOCK", action_counts.get("HIGH", 0)), 
                       action_counts.get("ISOLATE", action_counts.get("CRITICAL", 0))]

        x = range(len(labels))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 6))
        rects1 = ax.bar([i - width/2 for i in x], threat_vals, width, label='Threats Detected (UL)', color='coral')
        rects2 = ax.bar([i + width/2 for i in x], action_vals, width, label='Actions Taken (RL)', color='dodgerblue')

        ax.set_ylabel('Events')
        ax.set_title(f'Honeypot AI Performance Tracker (Accuracy: {accuracy:.1f}%)')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        
        # labels on top of bars
        for rect in rects1 + rects2:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{height}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig("performance_chart.jpg", dpi=300)
        print("\nChart saved as 'performance_chart.jpg'")
        
    except ImportError:
        print("\n  Could not generate chart. Please run: pip install matplotlib")

if __name__ == "__main__":
    analyze_logs()
