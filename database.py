import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Establishes fresh pool connection parameters targeting the Neon instance."""
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        sslmode="require",
        connect_timeout=10,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5
    )

# ---------------- INITIALIZE DATABASE TABLES ----------------
def init_db():
    """Generates schema collections natively if missing from cluster layout."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # 1. Accounts Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """)
        
        # 2. Raw Logs Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                metric TEXT NOT NULL,
                count INTEGER NOT NULL
            );
        """)
        
        # 3. History Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result TEXT NOT NULL
            );
        """)
        
        conn.commit()
        cur.close()
    finally:
        conn.close()

# ---------------- USER AUTHENTICATION HANDLERS ----------------
def create_user(username, password):
    """Encrypts raw passwords via hash generation and inserts profile securely."""
    from werkzeug.security import generate_password_hash
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, generate_password_hash(password))
        )
        conn.commit()
        cur.close()
        return True
    except psycopg2.IntegrityError:
        return False  
    finally:
        conn.close()

def get_user(username):
    """Fetches user entry dynamically for match queries during form submittal."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT username, password FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        
        if row:
            return {"username": row[0], "password": row[1]}
        return None
    finally:
        conn.close()

# ---------------- MAPREDUCE DATA MANAGERS ----------------
def save_results(data):
    """Stores execution metrics directly inside the log schema tables."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        for key, value in data.items():
            cur.execute(
                "INSERT INTO logs(metric, count) VALUES (%s, %s)",
                (key, value)
            )
        conn.commit()
        cur.close()
    finally:
        conn.close()

def save_history(filename, result):
    """Appends processing runs into database records serialized as JSON formats."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO analysis_history (filename, result) VALUES (%s, %s)",
            (filename, json.dumps(result))
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()

def get_history():
    """Extracts systemic timeline logs and formats output structures cleanly."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT filename, analyzed_at, result 
            FROM analysis_history 
            ORDER BY analyzed_at DESC
        """)
        rows = cur.fetchall()
        cur.close()
        
        cleaned_rows = []
        for r in rows:
            cleaned_rows.append({
                "filename": r[0],
                "analyzed_at": r[1],
                "result": json.loads(r[2]) if isinstance(r[2], str) else r[2]
            })
        return cleaned_rows
    finally:
        conn.close()