import sqlite3
from datetime import datetime

DB_PATH = "assistant_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            user_id INTEGER,
            username TEXT,
            text TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_message(msg_type, user_id, username, text):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (type, user_id, username, text, date) VALUES (?, ?, ?, ?, ?)",
        (msg_type, user_id, username, text, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()