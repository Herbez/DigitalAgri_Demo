import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def train_model():
    print("Loading dataset...")
    data_path = 'ahs_dataset_nisr.csv'
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    df = pd.read_csv(data_path)

    # Features and target
    features = [
        'nitrogen', 'phosphorus', 'potassium', 'soil_ph', 
        'altitude_m', 'annual_rainfall_mm', 'avg_temperature_C', 'avg_humidity_pct'
    ]
    target = 'recommended_crop'

    # Filter data to only include relevant columns and drop rows with missing values
    df_clean = df[features + [target]].dropna()

    X = df_clean[features]
    y = df_clean[target]

    print(f"Training on {len(df_clean)} samples...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Calculate accuracy
    accuracy = model.score(X_test, y_test)
    print(f"Model accuracy: {accuracy:.4f}")

    # Save the model
    model_name = 'best_model.pkl'
    joblib.dump(model, model_name)
    print(f"Model saved as {model_name}")

if __name__ == "__main__":
    train_model()
