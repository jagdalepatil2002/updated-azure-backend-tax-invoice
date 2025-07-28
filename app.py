# File: app.py
import os
import logging
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Read database URL from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")

# Initialize DB connection and create table

def initialize_database():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        ''')
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

# Call database init during import
initialize_database()

# Register API
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        name = data['name']
        email = data['email']
        password = data['password']

        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, password))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        logger.error(f"Error in /register: {e}")
        return jsonify({"error": "Registration failed"}), 500

# Login API
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data['email']
        password = data['password']

        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            return jsonify({"message": "Login successful"})
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        logger.error(f"Error in /login: {e}")
        return jsonify({"error": "Login failed"}), 500

# Health check
@app.route('/', methods=['GET'])
def home():
    return "Tax Invoice Backend is up!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)


# File: startup.sh
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


# File: requirements.txt
flask
flask-cors
psycopg2-binary
gunicorn
python-dotenv
werkzeug
