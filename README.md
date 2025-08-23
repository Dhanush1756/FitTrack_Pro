# 🏋️ FitTrack Pro – Personalized Fitness & Health Tracker

**FitTrack Pro** is a full-stack fitness tracking web application built with **Flask, MySQL, and AI-powered recommendation systems**.  
It helps users manage **workouts, diet plans, health metrics**, and track progress toward their fitness goals.

---

## 🚀 Features

- 🔐 **User Authentication** (Login/Register)  
- 📊 **Dashboard** with weight, calorie, and activity metrics  
- 🧠 **AI-based personalized diet and workout recommendations** (GROQ/LLaMA)  
- 📆 **Daily logging** for:  
  - Meals 🍽️  
  - Workouts 🏃‍♂️  
  - Weight tracking ⚖️  
- 📄 **Export workout/diet plan** as PDF and Excel  
- 🌑 **Dark Mode** toggle  
- 💬 **Motivational quotes** on login  
- 🏅 **Progress Milestones** (streaks, goals achieved)  
- 📈 **AI Alerts** for calorie and eating trends  

---

## 🎥 Demo Video  
Here’s a quick walkthrough of FitTracker:  
👉 [Watch Demo](https://drive.google.com/file/d/1YUKWXffrixS-RjBDMRg0fkvRch3ym23U/view?usp=sharing)

## 🛠️ Tech Stack

| Layer         | Technology Used                  |
|---------------|----------------------------------|
| Frontend      | HTML, CSS, JavaScript            |
| Backend       | Python (Flask)                   |
| Database      | MySQL                            |
| AI Integration| GROQ / LLaMA                     |

## ⚙️ Installation

1. **Clone the repository**

```bash
git clone https://github.com/Dhanush1756/FitTrackPro.git fitness-tracker
cd fitness-tracker

```

2. **Create a virtual environment**

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # macOS/Linux
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=root
DB_NAME=fitness_tracker
GROQ_API_KEY=your_actual_groq_api_key
SECRET_KEY=your_flask_secret_key
```

5. **Set up the database**

Use the provided SQL file or run:

```sql
CREATE DATABASE fitness_tracker;
```

Then, import the tables or let the app auto-create them.

6. **Run the app**

```bash
python app.py
```

App will be available at: `http://127.0.0.1:5000`

## 🧠 AI Integration (GROQ/LLaMA)

This app integrates with GROQ AI to provide:
- Calorie trend analysis
- Personalized diet and workout plans
- Motivation and mindfulness tips

## 📦 Export Features

- Download diet/workout plans as **PDF**
- Export your logged workouts as **Excel**

## 🛡️ Security

- Passwords are hashed before storing
- Sessions are managed securely using Flask
- Environment variables hidden via `.env`

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.


## 👥 Contributors

This project was made possible by the amazing efforts of the following contributors:

- [@Dhanush1756](https://github.com/Dhanush1756) — Project Lead & Backend Development  
- [@gtanu13](https://github.com/gtanu13) — Data Processing, Model Integration & Optimization  
- [@sasivaishnav](https://github.com/sasivaishnav) — Documentation & Testing  
- [@dilip-ravichandra](https://github.com/dilip-ravichandra) — Frontend & Deployment  

✨ Every role was essential in making **FitTrack Pro** a success!


## 📝 License

This project is open-source and available under the MIT License.

---

### 🙋 Author

**Dhanush S**  
📧 dhanushs1756@gmail.com  
🔗 [GitHub Profile](https://github.com/Dhanush1756)
