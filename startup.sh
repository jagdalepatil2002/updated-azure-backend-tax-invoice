#!/bin/bash

echo "--- STARTUP SCRIPT STARTED ---"

# Update and install system dependencies
echo "--- Updating apt-get ---"
apt-get update -y

echo "--- Installing Tesseract and dependencies ---"
apt-get install -y tesseract-ocr tesseract-ocr-eng libpq-dev poppler-utils

echo "--- Setting environment variables ---"
export PYTHONPATH="${PYTHONPATH}:/home/site/wwwroot"
export FLASK_ENV=production

echo "--- Creating logs directory ---"
mkdir -p /home/site/wwwroot/logs

echo "--- Installing Python packages ---"
pip install -r requirements.txt

echo "--- Initialization complete ---"
echo "--- Starting Gunicorn ---"

exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --access-logfile '-' --error-logfile '-' app:app
