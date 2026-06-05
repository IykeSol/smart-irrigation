from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import requests
import os
import google.generativeai as genai

app = Flask(__name__, static_folder='../frontend')
CORS(app) # Enable CORS if frontend is served separately during dev

# Configure Gemini API
genai.configure(api_key="AIzaSyD4i1mQjc6n-GlrWDeSmbe3_Dtcce4f-3A")
gemini_model = genai.GenerativeModel('gemini-flash-latest')

# OpenWeatherMap API Key
API_KEY = "a6de1b185e04e9dd876a3c77587f996f"

# Load the trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../ml/irrigation_model.pkl')
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    print(f"Warning: Model not found at {MODEL_PATH}. Prediction endpoint will fail.")
    model = None

def fetch_weather(city):
    """Helper to fetch weather from OWM"""
    try:
        current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(current_url)
        response.raise_for_status()
        data = response.json()
        
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        rain_1h = data.get('rain', {}).get('1h', 0)
        rainfall_24h = rain_1h * 24 if rain_1h > 0 else 0
        
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        f_res = requests.get(forecast_url)
        f_res.raise_for_status()
        f_data = f_res.json()
        
        forecast_rain = sum([item.get('rain', {}).get('3h', 0) for item in f_data['list'][:8]])
            
        return {
            'Temperature_C': temp,
            'Humidity_pct': humidity,
            'Rainfall_24h_mm': rainfall_24h,
            'Forecast_Rainfall_mm': forecast_rain
        }
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City parameter is required"}), 400
    weather = fetch_weather(city)
    if "error" in weather:
        return jsonify(weather), 500
    return jsonify(weather)

@app.route('/api/predict', methods=['POST'])
def predict():
    if not model:
        return jsonify({"error": "Model not loaded on server."}), 500
        
    data = request.json
    try:
        # Expected fields
        temp = float(data['Temperature_C'])
        humidity = float(data['Humidity_pct'])
        soil_moisture = float(data['Soil_Moisture_pct'])
        rain_24h = float(data['Rainfall_24h_mm'])
        forecast_rain = float(data['Forecast_Rainfall_mm'])
        crop_type = data['Crop_Type']
        growth_stage = data['Growth_Stage']
        
        # Derived fields
        solar_rad = 15.0 # Default assumption
        et0 = 0.0023 * solar_rad * (temp + 17.8) * np.sqrt(abs(temp - (temp - (100 - humidity)/5)))
        
        input_dict = {
            'Temperature_C': temp,
            'Humidity_pct': humidity,
            'Soil_Moisture_pct': soil_moisture,
            'Rainfall_24h_mm': rain_24h,
            'Forecast_Rainfall_mm': forecast_rain,
            'Crop_Type': crop_type,
            'Growth_Stage': growth_stage,
            'Solar_Radiation_MJ': solar_rad,
            'Evapotranspiration_mm': et0
        }
        
        df = pd.DataFrame([input_dict])
        
        # Predict
        pred = int(model.predict(df)[0])
        probs = model.predict_proba(df)[0]
        confidence = float(max(probs)) * 100
        
        action_map = {
            0: "No Irrigation Required",
            1: "Light Irrigation Required",
            2: "Heavy Irrigation Required"
        }
        action_str = action_map[pred]
        
        # Generate summary using Gemini
        prompt = f"""
        You are an expert agronomist AI helping a farmer.
        Based on the following data, write a short, simple, and friendly summary (max 3 sentences) explaining why the system recommended "{action_str}".
        Avoid technical jargon where possible.
        
        Farm Data:
        - Crop: {crop_type} at {growth_stage} stage
        - Temperature: {temp}°C
        - Humidity: {humidity}%
        - Soil Moisture: {soil_moisture}%
        - Rainfall last 24h: {rain_24h}mm
        - Forecast Rain: {forecast_rain}mm
        """
        
        try:
            response = gemini_model.generate_content(prompt)
            ai_summary = response.text.strip()
        except Exception as e:
            ai_summary = "AI summary temporarily unavailable."
        
        return jsonify({
            "action": action_str,
            "action_code": pred,
            "confidence": confidence,
            "probabilities": {action_map[i]: float(probs[i]*100) for i in range(3)},
            "ai_summary": ai_summary
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
