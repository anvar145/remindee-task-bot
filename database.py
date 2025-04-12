import sqlite3
import logging

logger = logging.getLogger(__name__)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task TEXT,
            deadline TEXT,
            status TEXT
        )"""
    )
    conn.commit()
    conn.close()