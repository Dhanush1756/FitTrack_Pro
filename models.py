from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from database import db  # Your custom MySQL database helper

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.email = user_data.get('email')
        self.name = user_data.get('name')
        self.password = user_data.get('password')
        self.profile_photo = user_data.get('profile_photo')
        self.age = user_data.get('age')
        self.gender = user_data.get('gender')
        self.height = user_data.get('height')
        self.weight = user_data.get('weight')
        self.goal_weight = user_data.get('goal_weight')
        self.diet_preference = user_data.get('diet_preference')
        self.fitness_goal = user_data.get('fitness_goal')
        self.activity_level = user_data.get('activity_level')
        self.daily_calories = user_data.get('daily_calories')
        self.dark_mode = user_data.get('dark_mode', False)
        self.created_at = user_data.get('created_at', datetime.utcnow())

    @staticmethod
    def create(email, name, password):
        hashed_pw = generate_password_hash(password)
        db.execute_query(
            """INSERT INTO users (email, name, password) 
               VALUES (%s, %s, %s)""",
            (email, name, hashed_pw),
            commit=True
        )
        return User.get_by_email(email)

    @staticmethod
    def get_by_id(user_id):
        user_data = db.execute_query(
            "SELECT * FROM users WHERE id = %s",
            (user_id,),
            fetch_one=True
        )
        return User(user_data) if user_data else None

    @staticmethod
    def get_by_email(email):
        user_data = db.execute_query(
            "SELECT * FROM users WHERE email = %s",
            (email,),
            fetch_one=True
        )
        return User(user_data) if user_data else None

    def update_profile(self):
        db.execute_query(
            """UPDATE users SET 
               email=%s, name=%s, profile_photo=%s, age=%s, 
               gender=%s, height=%s, weight=%s, goal_weight=%s,
               diet_preference=%s, fitness_goal=%s, activity_level=%s,
               daily_calories=%s, dark_mode=%s
               WHERE id=%s""",
            (self.email, self.name, self.profile_photo, self.age,
             self.gender, self.height, self.weight, self.goal_weight,
             self.diet_preference, self.fitness_goal, self.activity_level,
             self.daily_calories, self.dark_mode, self.id),
            commit=True
        )

    def check_password(self, password):
        return check_password_hash(self.password, password)

class MealLog:
    @staticmethod
    def create(user_id, name, calories, protein=None, carbs=None, fat=None, notes=None):
        db.execute_query(
            """INSERT INTO meal_logs 
               (user_id, name, calories, protein, carbs, fat, notes)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user_id, name, calories, protein, carbs, fat, notes),
            commit=True
        )

    @staticmethod
    def get_recent(user_id, days=7):
        return db.execute_query(
            """SELECT * FROM meal_logs 
               WHERE user_id = %s AND date >= %s
               ORDER BY date DESC""",
            (user_id, datetime.utcnow() - timedelta(days=days)),
            fetch_all=True
        )

class WorkoutLog:
    @staticmethod
    def create(user_id, workout_type, duration, calories_burned=None, notes=None):
        db.execute_query(
            """INSERT INTO workout_logs 
               (user_id, type, duration, calories_burned, notes)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, workout_type, duration, calories_burned, notes),
            commit=True
        )

    @staticmethod
    def get_recent(user_id, days=7):
        return db.execute_query(
            """SELECT * FROM workout_logs 
               WHERE user_id = %s AND date >= %s
               ORDER BY date DESC""",
            (user_id, datetime.utcnow() - timedelta(days=days)),
            fetch_all=True
        )

class WeightLog:
    @staticmethod
    def create(user_id, weight, notes=None):
        db.execute_query(
            """INSERT INTO weight_logs 
               (user_id, weight, notes)
               VALUES (%s, %s, %s)""",
            (user_id, weight, notes),
            commit=True
        )

    @staticmethod
    def get_history(user_id, days=30):
        return db.execute_query(
            """SELECT * FROM weight_logs 
               WHERE user_id = %s AND date >= %s
               ORDER BY date""",
            (user_id, datetime.utcnow() - timedelta(days=days)),
            fetch_all=True
        )