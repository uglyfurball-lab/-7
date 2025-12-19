import sqlite3
import logging
from contextlib import contextmanager


class Database:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()  #commit для сохранения изменений

    async def add_user(self, user_id: int, first_name: str, last_name: str = None, email: str = None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, first_name, last_name, email)
                VALUES (?, ?, ?, ?)
            ''', (user_id, first_name, last_name, email))
            conn.commit()  # commit для сохранения изменений
        return True

    async def get_user(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()

            if result:
                return {
                    'user_id': result[0],
                    'first_name': result[1],
                    'last_name': result[2],
                    'email': result[3],
                    'created_at': result[4]
                }
            return None
