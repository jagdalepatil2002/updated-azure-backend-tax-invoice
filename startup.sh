#!/bin/bash

echo "--- STARTUP SCRIPT STARTED ---"

# Avoid permission errors by not trying to use restricted folders
echo "--- Updating apt-get... ---"
apt-get update -y

echo "--- Installing Tesseract and libpq-dev... ---"
apt-get install -y tesseract-ocr tesseract-ocr-eng libpq-dev

echo "--- System dependencies installation complete. ---"

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:/home/site/wwwroot"
export FLASK_ENV=production

# Default port fallback for local testing
export PORT=${PORT:-8000}

echo "--- Environment variables set. PORT=${PORT} ---"

# Create logs directory if it doesn't exist (in writable folder)
mkdir -p /home/site/wwwroot/logs
echo "--- Logs directory created at /home/site/wwwroot/logs ---"

# Change to app directory to avoid file path issues
cd /home/site/wwwroot

# Install Python dependencies
echo "--- Installing Python packages from requirements.txt... ---"
pip install -r requirements.txt

echo "--- Python packages installation complete. ---"

# Final check before starting Gunicorn
echo "--- All initialization complete. Starting Gunicorn now... ---"

# Start Gunicorn
exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 \
  --access-logfile /home/site/wwwroot/logs/access.log \
  --error-logfile /home/site/wwwroot/logs/error.log app:app
