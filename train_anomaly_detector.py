import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix
import pickle
import os

# paths
INPUT_DIR = "processed_data"
MODELS_DIR = "models"
MODEL_PATH = os.path.join(MODELS_DIR, 'anomaly_model.pkl')

def train():
    print("Loading preprocessed data...")
    try:
        X_train = np.load(os.path.join(INPUT_DIR, 'X_train_benign.npy'))
        X_test = np.load(os.path.join(INPUT_DIR, 'X_test.npy'))
        y_test = np.load(os.path.join(INPUT_DIR, 'y_test.npy'))
    except FileNotFoundError:
        print("Error: Preprocessed data files not found. Please run preprocess_iot23.py first.")
        return

    print(f"Training data shape: {X_train.shape}")
    print(f"Testing data shape: {X_test.shape}")

    # 1. 
    # initialise Isolation Forest
    print("Training Isolation Forest (this may take a few minutes)...")
    model = IsolationForest(
        n_estimators=200, 
        max_samples='auto', 
        contamination=0.005, # stricter outlier detection to reduce false positives
        random_state=42,
        verbose=1
    )

    # 2. 
    # fit the model on benign traffic ONLY (Unsupervised)
    model.fit(X_train)

    # 3. 
    # evaluate the model on a BALANCED subset for a fair report
    print("Evaluating model on balanced subset...")
    
    # separate normal and anomaly indices
    normal_idx = np.where(y_test == 1)[0]
    anomaly_idx = np.where(y_test == -1)[0]
    
    # take an equal number from both (limited by the smaller class)
    n_samples = min(len(normal_idx), len(anomaly_idx))
    balanced_idx = np.concatenate([
        np.random.choice(normal_idx, n_samples, replace=False),
        np.random.choice(anomaly_idx, n_samples, replace=False)
    ])
    
    X_test_balanced = X_test[balanced_idx]
    y_test_balanced = y_test[balanced_idx]
    
    y_pred = model.predict(X_test_balanced)
    
    print("\nBalanced Model Evaluation Report (50/50 Split):")
    print("=" * 60)
    print(classification_report(y_test_balanced, y_pred, target_names=['Anomaly', 'Normal']))
    print("=" * 60)
    
    print("\nConfusion Matrix (Balanced):")
    print(confusion_matrix(y_test_balanced, y_pred))

    # 4. 
    # save the model
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"\nModel saved to {MODEL_PATH}")

if __name__ == "__main__":
    train()
