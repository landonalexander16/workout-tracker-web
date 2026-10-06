import json
from models import WorkoutTracker, Session, Exercise, Sets
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route("/")
def home():
    return "..."
    
def load_tracker():
    with open("workout_data.json", "r") as f:
        data = json.load(f)
    return WorkoutTracker.from_dict(data)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        weight = float(request.form["weight"])
        reps = int(request.form["reps"])
        exercise_name = request.form["exercise"]
        date = request.form["date"]

        sets = Sets(weight, reps)
        exercise = Exercise(exercise_name)
        exercise.add_sets(sets)
        session = Session(date)
        session.add_exercise(exercise)

        tracker = load_tracker()
        tracker.add_session(session)
        tracker.sessions = sorted(tracker.sessions, key = lambda s : s.date)

        with open("workout_data.json", "w") as f:
            json.dump(tracker.to_dict(), f, indent=4)

        return redirect(url_for("show_tracker"))

    return render_template("add_sessions.html")

@app.route("/tracker")
def show_tracker():
    my_tracker = load_tracker()
    return render_template("sessions.html", workout=my_tracker)

if __name__ == "__main__":
    app.run(debug=True)