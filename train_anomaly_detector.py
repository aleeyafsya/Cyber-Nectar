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
    # evaluate the model
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    
    # Isolation Forest labels: 1 = normal, -1 = anomaly
    # y_test labels: 1 = Benign, -1 = Malicious
    
    print("\nModel Evaluation Report:")
    print("=" * 60)
    print(classification_report(y_test, y_pred, target_names=['Anomaly', 'Normal']))
    print("=" * 60)
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # 4. 
    # save the model
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"\nModel saved to {MODEL_PATH}")

if __name__ == "__main__":
    train()
