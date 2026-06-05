document.addEventListener('DOMContentLoaded', () => {
    
    const elements = {
        cityInput: document.getElementById('cityInput'),
        fetchWeatherBtn: document.getElementById('fetchWeatherBtn'),
        weatherLoader: document.getElementById('weatherLoader'),
        weatherError: document.getElementById('weatherError'),
        
        temp: document.getElementById('temp'),
        humidity: document.getElementById('humidity'),
        rain24h: document.getElementById('rain24h'),
        forecastRain: document.getElementById('forecastRain'),
        
        soilMoisture: document.getElementById('soilMoisture'),
        soilMoistureVal: document.getElementById('soilMoistureVal'),
        cropType: document.getElementById('cropType'),
        growthStage: document.getElementById('growthStage'),
        
        predictBtn: document.getElementById('predictBtn'),
        
        actionResult: document.getElementById('actionResult'),
        confidenceScore: document.getElementById('confidenceScore'),
        aiSummaryContainer: document.getElementById('aiSummaryContainer'),
        aiSummaryText: document.getElementById('aiSummaryText')
    };

    // Base URL for API (empty string means same origin when deployed, or localhost:5000 for dev)
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:5000/api' 
        : '/api';

    // Update range slider value display
    elements.soilMoisture.addEventListener('input', (e) => {
        elements.soilMoistureVal.textContent = `${e.target.value}%`;
    });

    // Fetch Weather Logic
    elements.fetchWeatherBtn.addEventListener('click', async () => {
        const city = elements.cityInput.value.trim();
        if (!city) return;

        elements.weatherLoader.classList.remove('hidden');
        elements.weatherError.classList.add('hidden');
        elements.fetchWeatherBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE}/weather?city=${encodeURIComponent(city)}`);
            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Failed to fetch weather');

            elements.temp.value = data.Temperature_C.toFixed(1);
            elements.humidity.value = data.Humidity_pct.toFixed(1);
            elements.rain24h.value = data.Rainfall_24h_mm.toFixed(1);
            elements.forecastRain.value = data.Forecast_Rainfall_mm.toFixed(1);

        } catch (error) {
            elements.weatherError.textContent = error.message;
            elements.weatherError.classList.remove('hidden');
        } finally {
            elements.weatherLoader.classList.add('hidden');
            elements.fetchWeatherBtn.disabled = false;
        }
    });

    // Prediction Logic
    elements.predictBtn.addEventListener('click', async () => {
        const payload = {
            Temperature_C: parseFloat(elements.temp.value),
            Humidity_pct: parseFloat(elements.humidity.value),
            Rainfall_24h_mm: parseFloat(elements.rain24h.value),
            Forecast_Rainfall_mm: parseFloat(elements.forecastRain.value),
            Soil_Moisture_pct: parseFloat(elements.soilMoisture.value),
            Crop_Type: elements.cropType.value,
            Growth_Stage: elements.growthStage.value
        };

        const originalBtnText = elements.predictBtn.textContent;
        elements.predictBtn.textContent = 'Analyzing Data...';
        elements.predictBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || 'Failed to predict');

            updateResultUI(data);

        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            elements.predictBtn.textContent = originalBtnText;
            elements.predictBtn.disabled = false;
        }
    });

    function updateResultUI(data) {
        // Update Action Text
        elements.actionResult.textContent = data.action;
        
        // Update Color based on action
        const actionColors = ['var(--action-0)', 'var(--action-1)', 'var(--action-2)'];
        elements.actionResult.style.color = actionColors[data.action_code];
        
        // Update Confidence
        elements.confidenceScore.textContent = `${data.confidence.toFixed(1)}%`;
        
        // Update AI Summary
        if (data.ai_summary) {
            elements.aiSummaryText.textContent = data.ai_summary;
            elements.aiSummaryContainer.classList.remove('hidden');
        } else {
            elements.aiSummaryContainer.classList.add('hidden');
        }
        
        // Update Probabilities Bars
        const mappings = [
            { id: 0, key: "No Irrigation Required" },
            { id: 1, key: "Light Irrigation Required" },
            { id: 2, key: "Heavy Irrigation Required" }
        ];

        mappings.forEach(m => {
            const val = data.probabilities[m.key] || 0;
            document.getElementById(`prob-${m.id}`).style.width = `${val}%`;
            document.getElementById(`prob-val-${m.id}`).textContent = `${val.toFixed(1)}%`;
        });
    }
});
