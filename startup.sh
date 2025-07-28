#!/bin/bash

echo "--- STARTUP SCRIPT STARTED ---"

# Ensure system is up to date
apt-get update -y

# Install system dependencies
apt-get install -y \
  tesseract-ocr \
  tesseract-ocr-eng \
  libpq-dev \
  poppler-utils

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:/home/site/wwwroot"
export FLASK_ENV=production

# Move to working directory
cd /home/site/wwwroot

# Log directory
mkdir -p logs

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# Start Gunicorn
echo "--- Starting Gunicorn ---"
exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --access-logfile - --error-logfile - app:app
