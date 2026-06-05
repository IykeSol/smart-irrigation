# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install all dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Generate dataset and train model at build time
# This ensures the model .pkl is baked into the container
RUN python dataset/generate_dataset.py
RUN python ml/train_model.py

# Expose port 7860 (mandatory for HuggingFace Spaces)
EXPOSE 7860

# Run the Flask app on port 7860
CMD ["python", "backend/app.py"]
