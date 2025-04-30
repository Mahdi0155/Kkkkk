import sqlite3

def init_db():
    conn = sqlite3.connect("bot.db")
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
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scheduled_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT,
        media_type TEXT,
        caption TEXT,
        send_time TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS file_count (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        count INTEGER DEFAULT 0
    )
    """)
    cursor.execute("INSERT OR IGNORE INTO file_count (id, count) VALUES (1, 0)")

    conn.commit()
    conn.close()

def add_user(user_id: int):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("INSERT INTO stats (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def increase_file_count():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE file_count SET count = count + 1 WHERE id = 1")
    conn.commit()
    conn.close()

def get_file_count():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM file_count WHERE id = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count
