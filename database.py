import sqlite3
from datetime import datetime, timedelta

DB_PATH = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        user_id INTEGER,
        timestamp TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        file_id TEXT PRIMARY KEY,
        requests INTEGER DEFAULT 0,
        added TEXT
    )
    """)

    conn.commit()
    conn.close()

def add_user(user_id: int):
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("INSERT INTO stats (user_id, timestamp) VALUES (?, ?)", (user_id, now))
    conn.commit()
    conn.close()

def increase_file_count(file_id: str):
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT file_id FROM files WHERE file_id = ?", (file_id,))
    if cursor.fetchone():
        cursor.execute("UPDATE files SET requests = requests + 1 WHERE file_id = ?", (file_id,))
    else:
        cursor.execute("INSERT INTO files (file_id, requests, added) VALUES (?, 1, ?)", (file_id, now))
    conn.commit()
    conn.close()

def get_file_count(file_id: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT requests FROM files WHERE file_id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def increase_file_request(user_id: int):
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stats (user_id, timestamp) VALUES (?, ?)", (user_id, now))
    conn.commit()
    conn.close()

def file_exists(file_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM files WHERE file_id = ?", (file_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def get_stats():
    now = datetime.now()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM stats")
    all_users = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT user_id, timestamp FROM stats")
    records = cursor.fetchall()

    def count_in_period(seconds):
        return len({u for u, t in records if (now - datetime.fromisoformat(t)).total_seconds() <= seconds})

    stats = {
        "total_users": len(all_users),
        "hour": count_in_period(3600),
        "day": count_in_period(86400),
        "week": count_in_period(604800),
        "month": count_in_period(2592000)
    }

    cursor.execute("SELECT COUNT(*) FROM files")
    stats["file_count"] = cursor.fetchone()[0]

    conn.close()
    return stats
