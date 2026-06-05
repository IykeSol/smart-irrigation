import requests
import joblib
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore') # Ignore sklearn warnings for cleaner CLI

API_KEY = "a6de1b185e04e9dd876a3c77587f996f"

def get_weather_data(city):
    """Fetch current weather and forecast from OpenWeatherMap"""
    try:
        # Current Weather
        current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(current_url)
        response.raise_for_status()
        data = response.json()
        
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        
        # Rainfall in last 1h (extrapolating to 24h roughly for this simple test if 24h is missing)
        rain_1h = data.get('rain', {}).get('1h', 0)
        rainfall_24h = rain_1h * 24 if rain_1h > 0 else 0
        
        # Forecast (approximate next 24h rainfall)
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        f_res = requests.get(forecast_url)
        f_res.raise_for_status()
        f_data = f_res.json()
        
        forecast_rain = 0
        # Sum rain for the next 8 intervals (3 hours each = 24 hours)
        for item in f_data['list'][:8]:
            forecast_rain += item.get('rain', {}).get('3h', 0)
            
        return {
            'Temperature_C': temp,
            'Humidity_pct': humidity,
            'Rainfall_24h_mm': rainfall_24h,
            'Forecast_Rainfall_mm': forecast_rain
        }
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching weather: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def main():
    print("="*50)
    print("🌾 SMART IRRIGATION SCHEDULER (CLI TESTER) 🌾")
    print("="*50)
    
    try:
        model = joblib.load('ml/irrigation_model.pkl')
    except FileNotFoundError:
        print("Error: Model file 'ml/irrigation_model.pkl' not found.")
        print("Please run 'python ml/train_model.py' first.")
        return
        
    city = input("Enter City name to fetch weather data: ")
    print(f"Fetching weather data for {city}...")
    
    weather = get_weather_data(city)
    if not weather:
        print("Falling back to manual input for weather...")
        weather = {
            'Temperature_C': float(input("Temperature (C): ")),
            'Humidity_pct': float(input("Humidity (%): ")),
            'Rainfall_24h_mm': float(input("Rainfall Last 24h (mm): ")),
            'Forecast_Rainfall_mm': float(input("Forecast Rainfall (mm): "))
        }
        
    print("\n[Fetched Weather Data]")
    for k, v in weather.items():
        print(f" - {k}: {v:.2f}")
        
    print("\n[Farm/Soil Data Input]")
    soil_moisture = float(input("Current Soil Moisture (0-100%): "))
    crop_type = input("Crop Type (Wheat, Corn, Rice, Soybean, Tomato): ")
    growth_stage = input("Growth Stage (Seedling, Vegetative, Flowering, Fruiting): ")
    
    # Calculate approximate ET0 and Solar Radiation
    solar_rad = 15.0 # default average
    et0 = 0.0023 * solar_rad * (weather['Temperature_C'] + 17.8) * np.sqrt(abs(weather['Temperature_C'] - (weather['Temperature_C'] - (100 - weather['Humidity_pct'])/5)))
    
    # Prepare input dataframe
    input_data = {
        'Temperature_C': weather['Temperature_C'],
        'Humidity_pct': weather['Humidity_pct'],
        'Soil_Moisture_pct': soil_moisture,
        'Rainfall_24h_mm': weather['Rainfall_24h_mm'],
        'Forecast_Rainfall_mm': weather['Forecast_Rainfall_mm'],
        'Crop_Type': crop_type.capitalize(),
        'Growth_Stage': growth_stage.capitalize(),
        'Solar_Radiation_MJ': solar_rad,
        'Evapotranspiration_mm': et0
    }
    
    df_input = pd.DataFrame([input_data])
    
    # Prediction
    prediction = model.predict(df_input)[0]
    probabilities = model.predict_proba(df_input)[0]
    confidence = max(probabilities) * 100
    
    action_map = {
        0: "NO IRRIGATION REQUIRED",
        1: "LIGHT IRRIGATION REQUIRED",
        2: "HEAVY IRRIGATION REQUIRED"
    }
    
    print("\n" + "="*50)
    print("🤖 MODEL PREDICTION")
    print("="*50)
    print(f"Action: {action_map[prediction]}")
    print(f"Confidence Level: {confidence:.2f}%")
    print("="*50)
    print("Probabilities Breakdown:")
    for i, action in action_map.items():
        print(f" - {action}: {probabilities[i]*100:.2f}%")

if __name__ == "__main__":
    main()
