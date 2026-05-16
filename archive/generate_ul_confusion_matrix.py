import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix
import sys
import os

# Force UTF-8 for Windows consoles
os.environ["PYTHONIOENCODING"] = "utf-8"

# Mock time.sleep to make the audit run instantly
import time
time.sleep = lambda x: None

# Add parent directory to path
sys.path.append(os.getcwd())

try:
    from anomaly_integration_iot import AnomalyHoneypot
except ImportError:
    print("Error: Could not import AnomalyHoneypot. Ensure you are running from the project root.")
    sys.exit(1)

def generate_heatmap():
    print("Initializing Anomaly Detector for performance audit...")
    # Initialize detector (loads pre-trained Isolation Forest)
    detector = AnomalyHoneypot()
    
    # 1. Define a balanced dataset for a clean matrix
    # Label: 0 = Normal (Score 1), 1 = Anomaly (Score -1)
    test_cases = [
        # Benign (Standard IoT traffic patterns)
        {"path": "/", "label": 0},
        {"path": "/index.html", "label": 0},
        {"path": "/assets/style.css", "label": 0},
        {"path": "/api/v1/status", "label": 0},
        {"path": "/favicon.ico", "label": 0},
        {"path": "/help/manual", "label": 0},
        {"path": "/products/view/1", "label": 0},
        {"path": "/about-us", "label": 0},
        {"path": "/blog/post/10", "label": 0},
        {"path": "/contact", "label": 0},
        
        # Attacks (IoT-specific exploits)
        {"path": "/etc/passwd", "label": 1},
        {"path": "/cgi-bin/test.sh", "label": 1},
        {"path": "/onvif/device_service", "label": 1},
        {"path": "/snapshot.cgi", "label": 1},
        {"path": "/admin/config.php", "label": 1},
        {"path": "/system/deviceinfo", "label": 1},
        {"path": "/.env", "label": 1},
        {"path": "/shell?cmd=ls", "label": 1},
        {"path": "/bin/sh", "label": 1},
        {"path": "/wp-config.php", "label": 1},
    ] * 5 # Expand to 100 samples
    
    y_true = [tc["label"] for tc in test_cases]
    y_pred = []
    
    print("Processing samples through Isolation Forest...")
    # Silence the engine's internal prints to keep output clean
    import contextlib
    import io
    
    with contextlib.redirect_stdout(io.StringIO()):
        for tc in test_cases:
            # In our engine: ml_response['anomaly_score'] -> 1 = Normal, -1 = Anomaly
            result = detector.process_attack(tc)
            score = result["ml_response"]["anomaly_score"]
            y_pred.append(1 if score == -1 else 0) # Convert to 0/1 for confusion matrix
        
    # 2. Calculate Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    
    # 3. Create Heatmap
    plt.figure(figsize=(9, 7))
    # Use a clean blue gradient
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Unsupervised Learning (Isolation Forest)\nAnomalous Activity Detection Performance', fontsize=16, pad=20, fontweight='bold')
    plt.colorbar(label='Sample Count')
    
    classes = ['Benign Traffic', 'Threat (Anomaly)']
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, fontsize=11)
    plt.yticks(tick_marks, classes, fontsize=11, rotation=45)
    
    # Add numbers and labels to the cells
    thresh = cm.max() / 2.
    for i, j in np.ndindex(cm.shape):
        plt.text(j, i, f"{cm[i, j]}\n({(cm[i, j]/len(y_true)*100):.1f}%)",
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black",
                 fontsize=14, fontweight='bold')
    
    plt.ylabel('Actual Classification', fontsize=13, fontweight='bold')
    plt.xlabel('AI Predicted Classification', fontsize=13, fontweight='bold')
    
    # Add a footnote for technical depth
    plt.figtext(0.5, 0.01, "Metrics: Unsupervised Learning - Isolation Forest model trained on IoT-23 dataset.", 
                ha="center", fontsize=10, bbox={"facecolor":"orange", "alpha":0.1, "pad":5})
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # 4. Save Image
    save_path = "ul_performance_heatmap.png"
    plt.savefig(save_path, dpi=200)
    print(f"\n[SUCCESS] UL Heatmap saved as '{save_path}'")
    
    # Summary Metrics for terminal confirmation
    tp = cm[1, 1]
    tn = cm[0, 0]
    fp = cm[0, 1]
    fn = cm[1, 0]
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    print(f"Results Summary:")
    print(f"   Accuracy:  {accuracy*100:.1f}%")
    print(f"   True Pos:  {tp} (Attacks Caught)")
    print(f"   True Neg:  {tn} (Benign Allowed)")
    print(f"   False Pos: {fp} (False Alarms)")
    print(f"   False Neg: {fn} (Missed Threats)")

if __name__ == "__main__":
    generate_heatmap()
