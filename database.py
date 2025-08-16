import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        self.connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'fitness_tracker'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )

    @contextmanager
    def get_cursor(self):
        cursor = self.connection.cursor(dictionary=True)
        try:
            yield cursor
        finally:
            cursor.close()

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False, commit=False):
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            if commit: self.connection.commit()
            if fetch_one: return cursor.fetchone()
            if fetch_all: return cursor.fetchall()

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

db = Database()
