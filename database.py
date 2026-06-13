import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

# ---------------- logs table result ----------------
def save_results(data):
    for key, value in data.items():
        cur.execute(
            "INSERT INTO logs(metric, count) VALUES (%s, %s)",
            (key, value)
        )
    conn.commit()

# ---------------- history table ----------------
def save_history(filename, result):
    cur.execute(
        "INSERT INTO analysis_history(filename, result) VALUES (%s, %s)",
        (filename, json.dumps(result))
    )
    conn.commit()