# 🏆 Tournament Manager – Flask Web App

A lightweight web-based **Tournament Management System** built with Flask and SQLite, designed for quick setup and seamless use during events or hackathons. Users can register players, auto-form teams, generate fixtures, and track scores live through a simple UI.

> 💡 Built during a hackathon to streamline managing team tournaments with zero hassle.

---

## ⚙️ Features

- ✅ Add and remove players
- 🤖 Auto-generate teams randomly
- 📅 Generate round-robin fixtures
- 📊 Submit match results and auto-update team stats
- 🧮 Tracks wins, draws, losses, goals, and points
- 🧹 Clear/reset data or regenerate matches anytime
- 🔍 View leaderboard and fixtures by matchday

---

## 🛠 Tech Stack

- **Backend:** Python + Flask
- **Database:** SQLite
- **Frontend:** HTML (Jinja2 templates)
- **Data Handling:** SQL, JSON, Python logic

---

## 🧩 How It Works

1. **Add Players** ➡️ names are stored in the DB.
2. **Form Teams** ➡️ random 2-player teams are auto-created.
3. **Generate Fixtures** ➡️ round-robin format ensures each team plays all others.
4. **Submit Results** ➡️ input scores to calculate points and update standings.
5. **Leaderboard** ➡️ ranks teams by points and goal difference.

---

## 🚀 Setup Instructions

```bash
# 1. Clone the repo
git clone https://github.com/your-username/tournament-manager.git
cd tournament-manager

# 2. (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use venv\Scripts\activate

# 3. Install dependencies
pip install flask

# 4. Run the app
python app.py
