import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# ---------------- CONNECTION ----------------
def get_connection():
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        sslmode="require"
    )

# ---------------- INIT DB ----------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            metric TEXT,
            count INT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id SERIAL PRIMARY KEY,
            filename TEXT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            result TEXT
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

# ---------------- USER ----------------
def create_user(username, password):
    from werkzeug.security import generate_password_hash

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, generate_password_hash(password))
        )
        conn.commit()
        return True

    except Exception as e:
        print("DB ERROR:", e)
        return False

    finally:
        cur.close()
        conn.close()

def get_user(username):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT username, password FROM users WHERE username=%s",
        (username,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return {"username": row[0], "password": row[1]}
    return None

# ---------------- LOGS ----------------
def save_results(data):
    conn = get_connection()
    cur = conn.cursor()

    for k, v in data.items():
        cur.execute(
            "INSERT INTO logs(metric, count) VALUES (%s, %s)",
            (k, v)
        )

    conn.commit()
    cur.close()
    conn.close()

# ---------------- HISTORY ----------------
def save_history(filename, result):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO analysis_history (filename, result) VALUES (%s, %s)",
        (filename, json.dumps(result))
    )

    conn.commit()
    cur.close()
    conn.close()

def get_history():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT filename, analyzed_at, result
        FROM analysis_history
        ORDER BY analyzed_at DESC
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "filename": r[0],
            "analyzed_at": r[1],
            "result": json.loads(r[2]) if isinstance(r[2], str) else r[2]
        }
        for r in rows
    ]