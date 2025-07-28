from flask import Flask, jsonify, request
import psycopg2
import os

app = Flask(__name__)

# PostgreSQL credentials from environment variables (RECOMMENDED)
DB_HOST = os.environ.get("DB_HOST", "tax-analyzer-db.postgres.database.azure.com")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "deploytejasai@outlook.com")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "your_password_here")
DB_PORT = os.environ.get("DB_PORT", "5432")

def get_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            sslmode="require"
        )
        return conn
    except Exception as e:
        print("❌ Database connection failed:", e)
        return None

@app.route("/api/test-db", methods=["GET"])
def test_db():
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database connection error."}), 500
    try:
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"message": "Database connected", "version": db_version})
    except Exception as e:
        return jsonify({"error": f"Query failed: {e}"}), 500

@app.route("/", methods=["GET"])
def home():
    return "✅ Backend running!"

if __name__ == "__main__":
    app.run(debug=True)
