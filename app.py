import json
from models import WorkoutTracker
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return "..."
    
def load_tracker():
    with open("workout_data.json", "r") as f:
        data = json.load(f)
    return WorkoutTracker.from_dict(data)

@app.route("/tracker")
def show_tracker():
    my_tracker = load_tracker()
    return render_template("sessions.html", workout=my_tracker)

if __name__ == "__main__":
    app.run(debug=True)