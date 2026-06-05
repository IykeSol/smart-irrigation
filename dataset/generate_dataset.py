import pandas as pd
import numpy as np
import random
import os

def generate_synthetic_data(num_samples=10000):
    np.random.seed(42)
    random.seed(42)
    
    # 1. Base environmental variables
    temperatures = np.random.normal(25, 7, num_samples) # Mean 25, Std 7
    temperatures = np.clip(temperatures, 5, 45) # Range 5 to 45 Celsius
    
    humidities = np.random.normal(60, 15, num_samples) # Mean 60, Std 15
    humidities = np.clip(humidities, 20, 100)
    
    soil_moistures = np.random.normal(50, 20, num_samples)
    soil_moistures = np.clip(soil_moistures, 5, 95)
    
    # Inverse correlation between temp and humidity/moisture somewhat
    # Adjust moisture based on temp and humidity
    soil_moistures = soil_moistures - (temperatures - 25) * 0.5 + (humidities - 60) * 0.2
    soil_moistures = np.clip(soil_moistures, 0, 100)
    
    rainfall_24h = np.random.exponential(scale=2.0, size=num_samples) # Skewed towards 0
    rainfall_24h[np.random.rand(num_samples) > 0.3] = 0 # 70% chance of no rain
    
    forecast_rain = np.random.exponential(scale=2.5, size=num_samples)
    forecast_rain[np.random.rand(num_samples) > 0.3] = 0
    
    # Categorical features
    crop_types = ['Wheat', 'Corn', 'Rice', 'Soybean', 'Tomato']
    crops = np.random.choice(crop_types, num_samples)
    
    growth_stages = ['Seedling', 'Vegetative', 'Flowering', 'Fruiting']
    stages = np.random.choice(growth_stages, num_samples)
    
    # Solar radiation and ET0 (Evapotranspiration approximation)
    solar_rad = np.random.normal(15, 5, num_samples)
    solar_rad = np.clip(solar_rad, 2, 30) # MJ/m2/day
    
    # Simple ET0 approximation (simplified Hargreaves/Penman-Monteith)
    et0 = 0.0023 * solar_rad * (temperatures + 17.8) * np.sqrt(np.abs(temperatures - (temperatures - (100 - humidities)/5)))
    et0 = np.clip(et0, 0.5, 12.0)
    
    # 2. Logic to determine target variable: Irrigation Action
    # 0: No Irrigation
    # 1: Light Irrigation
    # 2: Heavy Irrigation
    
    actions = []
    for i in range(num_samples):
        moisture = soil_moistures[i]
        forecast = forecast_rain[i]
        et = et0[i]
        crop = crops[i]
        
        # Add a bit of natural variance to the threshold per farm
        base_threshold = {'Rice': 60, 'Tomato': 50, 'Corn': 40, 'Soybean': 40, 'Wheat': 30}.get(crop, 40)
        threshold = np.random.normal(base_threshold, 5) # 5% variance in soil capacity
        
        # Introduce "farmer decision noise" - human factor
        human_error = np.random.random()
            
        # Logic block with fuzzy boundaries
        if moisture > threshold + 8 or forecast > 12.0:
            action = 0
        elif moisture > threshold - 5:
            if et > 5.5 and forecast < 3.0:
                action = 1
            else:
                action = 0
        elif moisture > threshold - 15:
            if forecast > 6.0:
                action = 0
            elif et > 4.0:
                action = 1
            else:
                action = 1
        else:
            if forecast > 15.0:
                action = 1
            else:
                action = 2

        # Inject ~12% pure random noise to simulate unmeasured variables (broken pipes, pest stress, manual overrides)
        if human_error < 0.12:
            action = np.random.choice([0, 1, 2])
            
        actions.append(action)

    # 3. Compile to DataFrame
    df = pd.DataFrame({
        'Temperature_C': np.round(temperatures, 2),
        'Humidity_pct': np.round(humidities, 2),
        'Soil_Moisture_pct': np.round(soil_moistures, 2),
        'Rainfall_24h_mm': np.round(rainfall_24h, 2),
        'Forecast_Rainfall_mm': np.round(forecast_rain, 2),
        'Crop_Type': crops,
        'Growth_Stage': stages,
        'Solar_Radiation_MJ': np.round(solar_rad, 2),
        'Evapotranspiration_mm': np.round(et0, 2),
        'Irrigation_Action': actions
    })
    
    return df

if __name__ == "__main__":
    print("Generating synthetic dataset...")
    df = generate_synthetic_data(15000) # 15k rows for good training
    
    # Ensure directory exists
    os.makedirs('dataset', exist_ok=True)
    
    # Save to CSV
    csv_path = 'dataset/irrigation_dataset.csv'
    df.to_csv(csv_path, index=False)
    
    print(f"Dataset generated successfully at {csv_path} with {len(df)} samples.")
    print("\nDataset Sample:")
    print(df.head())
    print("\nClass Distribution:")
    print(df['Irrigation_Action'].value_counts(normalize=True) * 100)
