import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()


def save_results(data):
    for key, value in data.items():
        cur.execute(
            "INSERT INTO logs(metric, count) VALUES (%s, %s)",
            (key, value)
        )
    conn.commit()