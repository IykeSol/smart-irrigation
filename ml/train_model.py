import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import VotingClassifier, RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

def train_and_save_model():
    print("Loading dataset...")
    # Adjust path if run from root or ml directory
    csv_path = 'dataset/irrigation_dataset.csv'
    if not os.path.exists(csv_path):
        csv_path = '../dataset/irrigation_dataset.csv'
        
    df = pd.read_csv(csv_path)
    
    X = df.drop('Irrigation_Action', axis=1)
    y = df['Irrigation_Action']
    
    # Define categorical and numerical columns
    categorical_cols = ['Crop_Type', 'Growth_Stage']
    numerical_cols = ['Temperature_C', 'Humidity_pct', 'Soil_Moisture_pct', 
                      'Rainfall_24h_mm', 'Forecast_Rainfall_mm', 
                      'Solar_Radiation_MJ', 'Evapotranspiration_mm']
                      
    # Preprocessing pipelines
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numerical_cols),
            ('cat', categorical_transformer, categorical_cols)
        ])
        
    # Hybrid Model: Voting Classifier combining Random Forest and Neural Network (MLP)
    # This provides a unique approach taking advantage of ensemble trees and deep learning
    clf1 = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    clf2 = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42, early_stopping=True)
    
    hybrid_model = VotingClassifier(
        estimators=[('rf', clf1), ('mlp', clf2)],
        voting='soft' # Soft voting allows us to get predict_proba() for confidence levels
    )
    
    # Bundle preprocessing and modeling code in a pipeline
    clf = Pipeline(steps=[('preprocessor', preprocessor),
                          ('classifier', hybrid_model)])
                          
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Training Hybrid Model (Random Forest + Neural Network)...")
    clf.fit(X_train, y_train)
    
    print("Evaluating Model...")
    y_pred = clf.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {acc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Ensure ml directory exists
    os.makedirs('ml', exist_ok=True)
    model_path = 'ml/irrigation_model.pkl'
    
    print(f"Saving model to {model_path}...")
    joblib.dump(clf, model_path)
    print("Model saved successfully.")

if __name__ == "__main__":
    train_and_save_model()
