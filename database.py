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
        self.initialize_db()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'fitness_tracker'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', '')
            )
            if self.connection.is_connected():
                print("Connected to MySQL database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            raise

    @contextmanager
    def get_cursor(self):
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            yield cursor
        except Error as e:
            print(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def initialize_db(self):
        try:
            with self.get_cursor() as cursor:
                # Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        password VARCHAR(200) NOT NULL,
                        profile_photo VARCHAR(200),
                        age INT,
                        gender VARCHAR(10),
                        height FLOAT,
                        weight FLOAT,
                        goal_weight FLOAT,
                        diet_preference VARCHAR(50),
                        fitness_goal VARCHAR(20),
                        activity_level VARCHAR(20),
                        daily_calories INT,
                        dark_mode BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create meal_logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS meal_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        calories INT NOT NULL,
                        protein INT,
                        carbs INT,
                        fat INT,
                        notes TEXT,
                        date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)

                # Create workout_logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workout_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        type VARCHAR(50) NOT NULL,
                        duration INT,
                        calories_burned INT,
                        notes TEXT,
                        date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)

                # Create weight_logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS weight_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        weight FLOAT NOT NULL,
                        notes TEXT,
                        date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)

                self.connection.commit()
        except Error as e:
            print(f"Error initializing database: {e}")
            raise

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False, commit=False):
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params or ())
                
                if commit:
                    self.connection.commit()
                
                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                return None
        except Error as e:
            print(f"Error executing query: {e}")
            self.connection.rollback()
            raise

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

# Singleton database instance
db = Database()