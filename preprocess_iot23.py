import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import os
import pickle

# paths to the dataset
DATA_PATH = r"c:\Users\aleey\OneDrive\Desktop\uni\sem 5\FYP1\AI Training\iot23-processor\data\iot23_combined_new.csv"
OUTPUT_DIR = "processed_data"
MODELS_DIR = "models"

def preprocess():
    print("Loading dataset")

    cols_to_use = [
        'id.orig_p', 'id.resp_p', 'duration', 'orig_bytes', 'resp_bytes', 
        'missed_bytes', 'orig_pkts', 'orig_ip_bytes', 'resp_pkts', 'resp_ip_bytes', 'label'
    ]
    
    # read the data
    df = pd.read_csv(DATA_PATH, usecols=cols_to_use, low_memory=False)
    
    print(f"Original dataset shape: {df.shape}")

    # 1. 
    # clean missing values and '-' (empty ones)
    print("Cleaning data...")
    df = df.replace('-', '0')
    
    # convert numeric columns to float
    numeric_cols = [col for col in cols_to_use if col != 'label']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 2. 
    # separate Benign and Malicious for Unsupervised Learning plan
    # Unsupervised learning on Benign only, then test on mix.
    # Note: 'Benign' is the label for normal traffic in IoT-23
    benign_df = df[df['label'] == 'Benign'].copy()
    malicious_df = df[df['label'] != 'Benign'].copy()
    
    print(f"Benign samples: {len(benign_df)}")
    print(f"Malicious samples: {len(malicious_df)}")

    # 3. 
    # label encoding for evaluation 
    # Benign=1, Anomaly=-1 to match Isolation Forest convention
    df['binary_label'] = df['label'].apply(lambda x: 1 if x == 'Benign' else -1)
    
    # 4. 
    # feature scaling
    print("Scaling features...")
    scaler = StandardScaler()
    X = df[numeric_cols]
    X_scaled = scaler.fit_transform(X)
    
    # save the scaler for live inference
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(os.path.join(MODELS_DIR, 'scaler.pkl'), 'wb') as f:
        pickle.dump(scaler, f)
    
    # 5. 
    # split and save
    # save a cleaned version for the trainer
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # TRAINING SET: 80% of Benign data
    train_benign = benign_df.sample(frac=0.8, random_state=42)
    X_train = train_benign[numeric_cols]
    scaler_train = StandardScaler()
    X_train_scaled = scaler_train.fit_transform(X_train)
    
    with open(os.path.join(MODELS_DIR, 'scaler.pkl'), 'wb') as f:
        pickle.dump(scaler_train, f)
        
    # save processed data
    print("Saving processed data...")
    np.save(os.path.join(OUTPUT_DIR, 'X_train_benign.npy'), X_train_scaled)
    
    # TESTING SET: remaining 20% Benign + ALL Malicious 
    test_benign = benign_df.drop(train_benign.index)
    test_malicious = malicious_df # keeping all malicious for a robust test
    
    test_df = pd.concat([test_benign, test_malicious])
    X_test = test_df[numeric_cols]
    y_test = test_df['label'].apply(lambda x: 1 if x == 'Benign' else -1).values
    
    X_test_scaled = scaler_train.transform(X_test)
    
    np.save(os.path.join(OUTPUT_DIR, 'X_test.npy'), X_test_scaled)
    np.save(os.path.join(OUTPUT_DIR, 'y_test.npy'), y_test)
    
    print("Preprocessing complete!")
    print(f"Training set size (Benign only): {X_train_scaled.shape}")
    print(f"Testing set size (Mixed): {X_test_scaled.shape}")

if __name__ == "__main__":
    preprocess()
