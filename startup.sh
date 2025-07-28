#!/bin/bash

echo "--- STARTUP SCRIPT STARTED ---"

# Update and install system dependencies with logging
echo "--- Updating apt-get... ---"
apt-get update -y
echo "--- Installing Tesseract and libpq-dev... ---"
apt-get install -y tesseract-ocr tesseract-ocr-eng libpq-dev
echo "--- System dependencies installation complete. ---"

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:/home/site/wwwroot"
export FLASK_ENV=production
echo "--- Environment variables set. ---"

# Create logs directory
mkdir -p /home/site/wwwroot/logs
echo "--- Logs directory created. ---"

# Install Python dependencies with logging
echo "--- Installing Python packages from requirements.txt... ---"
pip install -r requirements.txt
echo "--- Python packages installation complete. ---"

# Final check before starting Gunicorn
echo "--- All initialization complete. ---"
echo "--- Starting Gunicorn now... ---"

# Start with Gunicorn - logging is directed to stdout/stderr
exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --access-logfile '-' --error-logfile '-' app:app
