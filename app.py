import json
from models import WorkoutTracker, Session, Exercise, Sets
from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return "..."
    
def load_tracker():
    if not os.path.exists("workout_data.json"):
        return WorkoutTracker()

    try:
        with open("workout_data.json", "r") as f:
            data = json.load(f)
        return WorkoutTracker.from_dict(data)
    except(json.JSONDecodeError, KeyError):
        os.replace("workout_data.json", "workout_data.corrupt.json")
        return WorkoutTracker()


@app.route("/add", methods=["GET", "POST"])
def add():
    error = None
    if request.method == "POST":
        try: 
            date = datetime.strptime(request.form["date"], "%Y-%m-%d")
            weight = float(request.form["weight"])
            if weight < 0:
                raise ValueError ("Weight must be a number greater than or equal to zero.")
            
            reps = int(request.form["reps"])
            if reps <= 0:
                raise ValueError("Reps must be a number greater than zero.")

        except ValueError as e:
            error = str(e)

        else:    
            tracker = load_tracker()
            sets = Sets(weight, reps)
            name = request.form["exercise"].strip()

            session = None
            for s in tracker.sessions:
                if s.date == date:
                    session = s
                    break

            if session is None:
                session = Session(date)
                tracker.add_session(session)

            exercise = None
            for e in session.exercises:
                if e.name.lower() == name.lower():
                    exercise = e
                    break

            if exercise is None:
                exercise = Exercise(name)
                session.add_exercise(exercise)


            exercise.add_sets(sets)
            tracker.sessions = sorted(tracker.sessions, key = lambda s : s.date)

            with open("workout_data.json", "w") as f:
                json.dump(tracker.to_dict(), f, indent=4)

            return redirect(url_for("show_tracker"))
        
    return render_template("add_sessions.html", error=error)

@app.route("/tracker")
def show_tracker():
    my_tracker = load_tracker()
    return render_template("sessions.html", workout=my_tracker)

if __name__ == "__main__":
    app.run(debug=True)