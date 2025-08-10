import os
import json
from datetime import datetime, timedelta
from io import BytesIO

import pytz  # <-- Required for timezone handling
from config import Config
from database import db
from export_utils import create_plan_pdf, create_daily_plan_excel#
from flask import (Flask, flash, jsonify, redirect, render_template,
                   request, send_file, session, url_for)
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from graph_utils import create_plot
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from ai_integration import (get_ai_chat_response, get_ai_diet_suggestion,
                            get_ai_workout_plan, get_daily_quote,
                            get_nutrition_info, get_workout_calories)

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- THE OFFICIAL TIMEZONE HELPERS ---
# All date/time logic will now use these functions to ensure consistency.
def get_current_ist_date():
    """Returns the current DATE in the Asia/Kolkata timezone."""
    return datetime.now(pytz.timezone('Asia/Kolkata')).date()

def get_current_ist_datetime():
    """Returns the current DATETIME in the Asia/Kolkata timezone."""
    return datetime.now(pytz.timezone('Asia/Kolkata'))

@app.context_processor
def inject_now():
    """Injects the datetime object into the template context for all templates."""
    return {'now': datetime.utcnow}


class User(UserMixin):
    def __init__(self, user_dict):
        self.id = user_dict.get('id')
        self.email = user_dict.get('email')
        self.name = user_dict.get('name')
        self.password = user_dict.get('password')
        self.profile_photo = user_dict.get('profile_photo', 'default.png')
        self.age = user_dict.get('age')
        self.gender = user_dict.get('gender')
        self.height = user_dict.get('height')
        self.weight = user_dict.get('weight')
        self.goal_weight = user_dict.get('goal_weight')
        self.diet_preference = user_dict.get('diet_preference')
        self.fitness_goal = user_dict.get('fitness_goal')
        self.activity_level = user_dict.get('activity_level')
        self.daily_calories = user_dict.get('daily_calories')
        self.dark_mode = user_dict.get('dark_mode', False)
        self.created_at = user_dict.get('created_at')
        self.medical_conditions = user_dict.get('medical_conditions')
        self.past_surgeries = user_dict.get('past_surgeries')

    def get_id(self):
        return str(self.id)

    def save(self):
        if self.id:
            query = """
                UPDATE users SET
                name = %s, email = %s, gender = %s, age = %s, height = %s,
                weight = %s, goal_weight = %s, diet_preference = %s,
                fitness_goal = %s, activity_level = %s, daily_calories = %s,
                profile_photo = %s, medical_conditions = %s, past_surgeries = %s, dark_mode = %s
                WHERE id = %s
            """
            params = (
                self.name, self.email, self.gender, self.age, self.height,
                self.weight, self.goal_weight, self.diet_preference,
                self.fitness_goal, self.activity_level, self.daily_calories,
                self.profile_photo, self.medical_conditions, self.past_surgeries, self.dark_mode,
                self.id
            )
            db.execute_query(query, params, commit=True)

    @staticmethod
    def get(user_id):
        user_data = db.execute_query("SELECT * FROM users WHERE id = %s", (user_id,), fetch_one=True)
        return User(user_data) if user_data else None

    @staticmethod
    def get_by_email(email):
        user_data = db.execute_query("SELECT * FROM users WHERE email = %s", (email,), fetch_one=True)
        return User(user_data) if user_data else None


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def calculate_daily_calories(user):
    if not all([user.age, user.height, user.weight, user.gender, user.activity_level, user.fitness_goal]):
        return 2000
    if user.gender.lower() == 'male':
        bmr = 88.362 + (13.397 * float(user.weight)) + (4.799 * float(user.height)) - (5.677 * int(user.age))
    else:
        bmr = 447.593 + (9.247 * float(user.weight)) + (3.098 * float(user.height)) - (4.330 * int(user.age))
    
    activity_multipliers = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
    tdee = bmr * activity_multipliers.get(user.activity_level, 1.2)

    goal_adjustments = {'lose': -500, 'maintain': 0, 'gain': 500}
    final_calories = tdee + goal_adjustments.get(user.fitness_goal, 0)
    return int(final_calories)


def calculate_streak(user_id):
    query = """
        (SELECT DISTINCT DATE(date) as log_date FROM meal_logs WHERE user_id = %s)
        UNION
        (SELECT DISTINCT DATE(date) as log_date FROM workout_logs WHERE user_id = %s)
        ORDER BY log_date DESC;
    """
    dates_data = db.execute_query(query, (user_id, user_id), fetch_all=True)
    
    if not dates_data:
        return 0

    dates = [row['log_date'] for row in dates_data]
    
    today = get_current_ist_date() # FIX: Use correct timezone for today's date
    yesterday = today - timedelta(days=1)
    
    if dates[0] < yesterday:
        return 0
        
    streak = 0
    if dates[0] == today or dates[0] == yesterday:
        streak = 1
        current_day = dates[0] - timedelta(days=1)
        for log_date in dates[1:]:
            if log_date == current_day:
                streak += 1
                current_day -= timedelta(days=1)
            else:
                break
            
    return streak


def get_or_create_plan_html(user, date, plan_type):
    """
    Checks for a cached daily plan. If not found, generates a new one
    using the simple AI format and saves it.
    """
    query = "SELECT html_content FROM daily_plans WHERE user_id = %s AND date = %s AND plan_type = %s"
    existing_plan = db.execute_query(query, (user.id, date, plan_type), fetch_one=True)

    if existing_plan and existing_plan['html_content']:
        return existing_plan['html_content']

    html_content = ""
    try:
        if plan_type == 'diet':
            ai_response_str = get_ai_diet_suggestion(user) or ""
            # FIX: Reverted to parse the simple 3-part format
            for item in ai_response_str.split(';'):
                if ':' in item and len(item.split(':')) == 3:
                    meal_type, food, cals = item.split(':')
                    html_content += f"""<li class="plan-item" data-name="{meal_type}: {food}" data-calories="{float(cals)}" data-type="meal">
                        <input type="checkbox"><div class="item-details">
                        <div class="item-name">{meal_type}: {food}</div>
                        <div class="item-info">{float(cals):.0f} kcal</div></div></li>"""
        
        elif plan_type == 'workout':
            ai_response_str = get_ai_workout_plan(user) or ""
            # FIX: Reverted to parse the simple 3-part format
            for item in ai_response_str.split(';'):
                if ':' in item and len(item.split(':')) == 3:
                    cat, ex, cals = item.split(':')
                    html_content += f"""<li class="plan-item" data-name="{cat}: {ex}" data-calories="{float(cals)}" data-type="workout">
                        <input type="checkbox"><div class="item-details">
                        <div class="item-name">{cat}: {ex}</div>
                        <div class="item-info">{float(cals):.0f} kcal burned</div></div></li>"""
        
        if html_content:
            save_query = "INSERT INTO daily_plans (user_id, date, plan_type, html_content) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE html_content = VALUES(html_content)"
            db.execute_query(save_query, (user.id, date, plan_type, html_content), commit=True)

    except Exception as e:
        print(f"CRITICAL ERROR generating AI {plan_type} plan: {e}")
        return ""

    return html_content

@app.route('/export/excel')
@login_required
def export_excel():
    try:
        today = get_current_ist_date()

        # Get the plan from the cache (or generate if needed)
        diet_plan_html = get_or_create_plan_html(current_user, today, 'diet')
        workout_plan_html = get_or_create_plan_html(current_user, today, 'workout')

        if not diet_plan_html and not workout_plan_html:
            flash("No plan is available to export for today.", "warning")
            return redirect(url_for('dashboard'))

        excel_file = create_daily_plan_excel(diet_plan_html, workout_plan_html)

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'FitTrack_Daily_Plan_{today}.xlsx'
        )
    except Exception as e:
        flash(f"Error creating Excel file: {str(e)}", "error")
        return redirect(url_for('dashboard'))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.get_by_email(request.form['email'])
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user, remember=request.form.get('remember'))
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if User.get_by_email(request.form.get('email')):
            flash('Email address already exists.', 'error')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(request.form['password'])
        db.execute_query(
            "INSERT INTO users (name, email, password, created_at) VALUES (%s, %s, %s, %s)",
            (request.form['name'], request.form['email'], hashed_password, get_current_ist_datetime()), # FIX: Use IST datetime
            commit=True
        )
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    try:
        today = get_current_ist_date() # FIX: Use IST date for all dashboard logic.

        if not all([current_user.age, current_user.height, current_user.weight, current_user.daily_calories]):
            flash('Please complete your profile for a personalized experience.', 'warning')
            return redirect(url_for('profile'))

        user_meals_today = db.execute_query("SELECT * FROM meal_logs WHERE user_id = %s AND DATE(date) = %s", (current_user.id, today), fetch_all=True) or []
        user_workouts_today = db.execute_query("SELECT * FROM workout_logs WHERE user_id = %s AND DATE(date) = %s", (current_user.id, today), fetch_all=True) or []
        
        total_calories = sum(float(meal.get('calories', 0)) for meal in user_meals_today)
        workout_calories = sum(float(workout.get('calories_burned', 0)) for workout in user_workouts_today)
        streak = calculate_streak(current_user.id)

        thirty_days_ago = today - timedelta(days=29)
        seven_days_ago = today - timedelta(days=6)
        weight_data = db.execute_query("SELECT date, weight FROM weight_logs WHERE user_id = %s AND DATE(date) >= %s ORDER BY date", (current_user.id, thirty_days_ago), fetch_all=True) or []
        calorie_trend_data = db.execute_query("SELECT DATE(date) as log_date, SUM(calories) as total_calories FROM meal_logs WHERE user_id = %s AND DATE(date) >= %s GROUP BY DATE(date) ORDER BY log_date", (current_user.id, seven_days_ago), fetch_all=True) or []

        weight_graph_img = None
        if weight_data and len(weight_data) > 1:
            weight_dates = [entry['date'].strftime('%b %d') for entry in weight_data]
            weights = [float(entry['weight']) for entry in weight_data]
            weight_graph_img = create_plot(weight_dates, weights, "Weight Progress (30 Days)", "Weight (kg)", "#4f46e5")

        calorie_graph_img = None
        date_map = { (seven_days_ago + timedelta(days=i)).strftime('%b %d'): 0 for i in range(7) }
        for row in calorie_trend_data:
            date_map[row['log_date'].strftime('%b %d')] = float(row['total_calories'])
        if any(v > 0 for v in date_map.values()):
             calorie_graph_img = create_plot(list(date_map.keys()), list(date_map.values()), "Calorie Trend (7 Days)", "Calories (kcal)", "#10b981")

        today_str = today.isoformat()
        if session.get('quote_date') != today_str:
            session['daily_quote'] = get_daily_quote()
            session['quote_date'] = today_str
        daily_quote = session.get('daily_quote')
        
        diet_plan_html = get_or_create_plan_html(current_user, today, 'diet')
        workout_plan_html = get_or_create_plan_html(current_user, today, 'workout')

        return render_template('dashboard.html',
            total_calories=total_calories, workout_calories=workout_calories,
            weight_graph_img=weight_graph_img, calorie_graph_img=calorie_graph_img,
            streak=streak, daily_goal=current_user.daily_calories,
            diet_plan_html=diet_plan_html, workout_plan_html=workout_plan_html,
            user_meals_today=user_meals_today, user_workouts_today=user_workouts_today,
            daily_quote=daily_quote
        )
    except Exception as e:
        print(f"--- CRITICAL DASHBOARD ERROR ---"); import traceback; traceback.print_exc()
        flash("A critical error occurred while loading the dashboard.", "error")
        return redirect(url_for('profile'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            if 'profile_photo' in request.files:
                file = request.files['profile_photo']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"user_{current_user.id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    current_user.profile_photo = filename
            
            current_user.name = request.form.get('name')
            current_user.email = request.form.get('email')
            current_user.gender = request.form.get('gender')
            current_user.age = int(request.form.get('age', 0))
            current_user.height = float(request.form.get('height', 0))
            current_user.weight = float(request.form.get('weight', 0))
            current_user.goal_weight = float(request.form.get('goal_weight', 0))
            current_user.diet_preference = request.form.get('diet_preference')
            current_user.fitness_goal = request.form.get('fitness_goal')
            current_user.activity_level = request.form.get('activity_level')
            current_user.medical_conditions = request.form.get('medical_conditions')
            current_user.past_surgeries = request.form.get('past_surgeries')
            
            current_user.daily_calories = calculate_daily_calories(current_user)
            current_user.save()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating profile: {str(e)}', 'error')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=current_user)


@app.route('/log/meal', methods=['GET', 'POST'])
@login_required
def log_meal():
    if request.method == 'POST':
        try:
            db.execute_query(
                "INSERT INTO meal_logs (user_id, name, calories, protein, carbs, fat, notes, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (current_user.id, request.form.get('name'), float(request.form.get('calories', 0)), float(request.form.get('protein', 0)), float(request.form.get('carbs', 0)), float(request.form.get('fat', 0)), request.form.get('notes'), get_current_ist_datetime()), # FIX: Use IST datetime
                commit=True
            )
            flash('Meal logged successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error logging meal: {str(e)}', 'error')
    
    recent_meals = db.execute_query("SELECT * FROM meal_logs WHERE user_id = %s ORDER BY date DESC LIMIT 5", (current_user.id,), fetch_all=True)
    return render_template('logs/meals.html', recent_meals=recent_meals)


@app.route('/log/workout', methods=['GET', 'POST'])
@login_required
def log_workout():
    if request.method == 'POST':
        try:
            db.execute_query(
                "INSERT INTO workout_logs (user_id, type, duration, calories_burned, notes, date) VALUES (%s, %s, %s, %s, %s, %s)",
                (current_user.id, request.form.get('type'), int(request.form.get('duration', 0)), float(request.form.get('calories_burned', 0)), request.form.get('notes'), get_current_ist_datetime()), # FIX: Use IST datetime
                commit=True
            )
            flash('Workout logged successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error logging workout: {str(e)}', 'error')

    recent_workouts = db.execute_query("SELECT * FROM workout_logs WHERE user_id = %s ORDER BY date DESC LIMIT 5", (current_user.id,), fetch_all=True)
    return render_template('logs/workouts.html', recent_workouts=recent_workouts)


@app.route('/log/weight', methods=['GET', 'POST'])
@login_required
def log_weight():
    if request.method == 'POST':
        try:
            weight_today = float(request.form.get('weight', 0))
            db.execute_query("INSERT INTO weight_logs (user_id, weight, notes, date) VALUES (%s, %s, %s, %s)", (current_user.id, weight_today, request.form.get('notes'), get_current_ist_datetime()), commit=True) # FIX: Use IST datetime
            current_user.weight = weight_today
            current_user.daily_calories = calculate_daily_calories(current_user)
            current_user.save()
            flash('Weight logged successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error logging weight: {str(e)}', 'error')
    recent_weights = db.execute_query("SELECT * FROM weight_logs WHERE user_id = %s ORDER BY date DESC LIMIT 5", (current_user.id,), fetch_all=True)
    return render_template('logs/weight.html', recent_weights=recent_weights)


@app.route('/log_item_from_dashboard', methods=['POST'])
@login_required
def log_item_from_dashboard():
    try:
        data = request.get_json()
        item_type, name, calories = data.get('type'), data.get('name'), data.get('calories')
        log_time = get_current_ist_datetime() # FIX: Use IST datetime

        if item_type == 'meal':
            db.execute_query("INSERT INTO meal_logs (user_id, name, calories, date) VALUES (%s, %s, %s, %s)", (current_user.id, name, calories, log_time), commit=True)
        elif item_type == 'workout':
            workout_type, workout_name = name.split(': ', 1) if ': ' in name else (name, '')
            db.execute_query("INSERT INTO workout_logs (user_id, type, calories_burned, date) VALUES (%s, %s, %s, %s)", (current_user.id, workout_type, calories, log_time), commit=True)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/get-nutrition-info', methods=['POST'])
@login_required
def api_get_nutrition_info():
    description = request.json.get('description')
    if not description:
        return jsonify({'success': False, 'error': 'Description is required'}), 400
    
    nutrition_data = get_nutrition_info(description)
    if not nutrition_data:
        return jsonify({'success': False, 'error': 'Could not analyze food item'}), 500
        
    return jsonify({'success': True, 'data': nutrition_data})


@app.route('/api/get-workout-calories', methods=['POST'])
@login_required
def api_get_workout_calories():
    description = request.json.get('description')
    if not description:
        return jsonify({'success': False, 'error': 'Description is required'}), 400
    
    calorie_data = get_workout_calories(description)
    if not calorie_data:
        return jsonify({'success': False, 'error': 'Could not calculate calories'}), 500
        
    return jsonify({'success': True, 'data': calorie_data})


@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    try:
        prompt = request.json.get('prompt')
        if not prompt:
            return jsonify({'reply': 'Please enter a message.'})
        chat_history = session.get('chat_history', [])
        chat_history.append({"role": "user", "content": prompt})
        ai_reply = get_ai_chat_response(chat_history)
        chat_history.append({"role": "assistant", "content": ai_reply})
        session['chat_history'] = chat_history
        return jsonify({'reply': ai_reply})
    except Exception as e:
        return jsonify({'reply': f'An error occurred: {str(e)}'}), 500


@app.route('/toggle-dark-mode', methods=['POST'])
@login_required
def toggle_dark_mode():
    try:
        current_user.dark_mode = not current_user.dark_mode
        current_user.save()
        return jsonify({'success': True, 'dark_mode': current_user.dark_mode})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/export/pdf')
@login_required
def export_pdf():
    try:
        today = get_current_ist_date() # FIX: Use IST date
        diet_plan_html = get_or_create_plan_html(current_user, today, 'diet')
        workout_plan_html = get_or_create_plan_html(current_user, today, 'workout')
        pdf_bytes = create_plan_pdf(current_user, diet_plan_html, workout_plan_html)
        return send_file(BytesIO(pdf_bytes), mimetype='application/pdf', as_attachment=True, download_name=f'FitTrack_Plan_{today}.pdf')
    except Exception as e:
        flash(f"Error creating PDF: {str(e)}", "error")
        return redirect(url_for('dashboard'))




if __name__ == '__main__':
    app.run(debug=True)