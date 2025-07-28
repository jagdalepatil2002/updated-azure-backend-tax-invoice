#!/bin/bash

echo "Starting Tax Analyzer Backend initialization..."

# Update system packages
apt-get update

# Install Tesseract OCR
echo "Installing Tesseract OCR..."
apt-get install -y tesseract-ocr tesseract-ocr-eng

# Install system dependencies
apt-get install -y libpq-dev

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:/home/site/wwwroot"
export FLASK_ENV=production

# Create logs directory
mkdir -p /home/site/wwwroot/logs

# Install Python dependencies
pip install -r requirements.txt

echo "Initialization complete. Starting application..."

# Start with Gunicorn
exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --access-logfile '-' --error-logfile '-' app:app
