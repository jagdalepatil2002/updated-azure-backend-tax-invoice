# app.py - Main Flask Application
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import json
from dotenv import load_dotenv
import logging
from pdf_extractor import extract_text_from_pdf_enhanced
from gemini_api import call_gemini_api

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["*"])

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")

def get_db_connection():
    """Establishes a secure connection to the PostgreSQL database."""
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable is not set.")
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        return None

def initialize_database():
    """Creates or alters the users table to include new fields."""
    conn = get_db_connection()
    if not conn:
        logger.error("Could not initialize database, connection failed.")
        return False

    try:
        with conn.cursor() as cur:
            # Create users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    dob DATE,
                    mobile_number VARCHAR(25)
                );
            """)
            
            # Create analysis history table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    notice_type VARCHAR(50),
                    amount_due VARCHAR(50),
                    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    summary_data JSONB
                );
            """)
            
            conn.commit()
            logger.info("Database schema initialized successfully.")
            return True
    except psycopg2.Error as e:
        logger.error(f"Database schema error: {e}")
        return False
    finally:
        if conn:
            conn.close()

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Tax Analyzer Backend",
        "version": "2.0"
    }), 200

@app.route('/register', methods=['POST'])
def register_user():
    """Register a new user."""
    try:
        data = request.get_json()
        required_fields = ['firstName', 'lastName', 'email', 'password', 'dob', 'mobileNumber']
        
        if not data or not all(k in data for k in required_fields):
            return jsonify({
                "success": False, 
                "message": "Missing required fields"
            }), 400

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return jsonify({"success": False, "message": "Invalid email format."}), 400

        # Validate password strength
        if len(data['password']) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters long."}), 400

        password_hash = generate_password_hash(data['password'])
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection error."}), 500

        try:
            with conn.cursor() as cur:
                # Check if email already exists
                cur.execute("SELECT id FROM users WHERE email = %s;", (data['email'],))
                if cur.fetchone():
                    return jsonify({"success": False, "message": "Email already registered."}), 409

                # Insert new user
                sql = """
                    INSERT INTO users (first_name, last_name, email, password_hash, dob, mobile_number)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, first_name, last_name, email;
                """
                cur.execute(sql, (
                    data['firstName'], 
                    data['lastName'], 
                    data['email'], 
                    password_hash, 
                    data['dob'], 
                    data['mobileNumber']
                ))
                new_user = cur.fetchone()
                conn.commit()
                
                logger.info(f"New user registered: {data['email']}")
                return jsonify({
                    "success": True, 
                    "message": "User registered successfully",
                    "user": {
                        "id": new_user['id'],
                        "firstName": new_user['first_name'],
                        "lastName": new_user['last_name'],
                        "email": new_user['email']
                    }
                }), 201
                
        except psycopg2.Error as e:
            logger.error(f"Registration database error: {e}")
            return jsonify({"success": False, "message": "Registration failed."}), 500
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"success": False, "message": "An unexpected error occurred."}), 500

@app.route('/login', methods=['POST'])
def login_user():
    """Authenticate user login."""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['email', 'password']):
            return jsonify({"success": False, "message": "Email and password required."}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection error."}), 500

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email = %s;", (data['email'],))
                user = cur.fetchone()
                
                if user and check_password_hash(user['password_hash'], data['password']):
                    user_data = {
                        "id": user['id'],
                        "firstName": user['first_name'],
                        "lastName": user['last_name'],
                        "email": user['email']
                    }
                    logger.info(f"User logged in: {data['email']}")
                    return jsonify({"success": True, "user": user_data}), 200
                else:
                    return jsonify({"success": False, "message": "Invalid credentials."}), 401
                    
        except psycopg2.Error as e:
            logger.error(f"Login database error: {e}")
            return jsonify({"success": False, "message": "Login failed."}), 500
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"success": False, "message": "An unexpected error occurred."}), 500

@app.route('/summarize', methods=['POST'])
def summarize_notice():
    """Analyze and summarize tax notice PDF."""
    try:
        if 'notice_pdf' not in request.files:
            return jsonify({"success": False, "message": "No PDF file provided."}), 400

        file = request.files['notice_pdf']
        if file.filename == '':
            return jsonify({"success": False, "message": "No file selected."}), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"success": False, "message": "Only PDF files allowed."}), 400

        # Check file size (10MB limit)
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 10 * 1024 * 1024:
            return jsonify({"success": False, "message": "File too large. Max 10MB."}), 400

        logger.info(f"Processing PDF: {file.filename}, Size: {file_size} bytes")

        # Extract text from PDF
        pdf_bytes = file.read()
        raw_text = extract_text_from_pdf_enhanced(pdf_bytes)
        
        if not raw_text or len(raw_text.strip()) < 50:
            return jsonify({
                "success": False, 
                "message": "Could not extract meaningful text from PDF."
            }), 500

        logger.info(f"Extracted {len(raw_text)} characters from PDF")

        # Get AI summary
        summary_json = call_gemini_api(raw_text)
        if not summary_json:
            return jsonify({
                "success": False, 
                "message": "Failed to analyze document."
            }), 500

        try:
            summary_data = json.loads(summary_json)
            
            # Save to history if user_id provided
            user_id = request.form.get('user_id')
            if user_id:
                save_analysis_history(user_id, summary_data)
            
            logger.info("PDF analysis completed successfully")
            return jsonify({"success": True, "summary": summary_data}), 200
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from AI: {e}")
            return jsonify({"success": False, "message": "Invalid AI response."}), 500
            
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return jsonify({"success": False, "message": "Processing error occurred."}), 500

def save_analysis_history(user_id, summary_data):
    """Save analysis to database history."""
    try:
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO analysis_history (user_id, notice_type, amount_due, summary_data)
                    VALUES (%s, %s, %s, %s)
                """, (
                    user_id,
                    summary_data.get('noticeType', ''),
                    summary_data.get('amountDue', ''),
                    json.dumps(summary_data)
                ))
                conn.commit()
            conn.close()
    except Exception as e:
        logger.error(f"Failed to save history: {e}")

@app.route('/history/<int:user_id>', methods=['GET'])
def get_user_history(user_id):
    """Get user's analysis history."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database error."}), 500

        with conn.cursor() as cur:
            cur.execute("""
                SELECT notice_type, amount_due, analyzed_at, summary_data
                FROM analysis_history 
                WHERE user_id = %s 
                ORDER BY analyzed_at DESC 
                LIMIT 10
            """, (user_id,))
            
            history = cur.fetchall()
            
        conn.close()
        return jsonify({"success": True, "history": history}), 200
        
    except Exception as e:
        logger.error(f"History error: {e}")
        return jsonify({"success": False, "message": "Failed to get history."}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "message": "Internal server error"}), 500

if __name__ == '__main__':
    initialize_database()
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting Tax Analyzer Backend on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
