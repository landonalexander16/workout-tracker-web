"""Flask web interface for the workout tracker.

Routes: home(summary), add(log a set), show_tracker (view history), 
        stats (show max weight and reps per exercise), progress (show max weight over time).
Data is stored in workout_data.json and loaded fresh on each request.
"""
import json
from models import WorkoutTracker, Session, Exercise, Sets
from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import datetime
from db_models import db, User, Workout, WorkoutExercise, WorkoutSet

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///workout.db"
db.init_app(app)
    
def load_tracker():
    # No file yet (first run or fresh clone): start with an empty tracker
    if not os.path.exists("workout_data.json"):
        return WorkoutTracker()

    try:
        with open("workout_data.json", "r") as f:
            data = json.load(f)
        return WorkoutTracker.from_dict(data)
    except(json.JSONDecodeError, KeyError):
        # Unreadable file: move it aside instead of deleting it, so the data
        # can be inspected or repaired by hand. Done after the with-block closes,
        # because Windows won't move a file that's still open.
        os.replace("workout_data.json", "workout_data.corrupt.json")
        return WorkoutTracker()

def max_weight_by_exercise(tracker):
    """Return {exercise name (lowercase): (weight, reps)} for each exercise's best set.

    Names are lowercased so "Bench" and "bench" count as one exercise. The best set is
    the heaviest; ties go to the set with more reps.
    """

    best = {}                                    # exercise name -> highest weight and reps logged so far
    for session in tracker.sessions:             # level 1
        for exercise in session.exercises:       # level 2: the thing we group by
            key = exercise.name.lower()          # same exercise in any capitalization
            for s in exercise.sets:              # level 3: the values we compare
                if key not in best or (s.weight, s.reps) > best[key]:     # This condition allows a weight of 0 be stored
                    best[key] = (s.weight, s.reps)
    return best

def weight_over_time(tracker, name):
    """Return [(date, heaviest weight that day), ...] for one exercise.

    Sessions are already stored in date order, so the list is too.
    Dates where the exercise wasn't done are left out.
    """
     
    points = []
    for session in tracker.sessions:            
        best = None
        for exercise in session.exercises:
            if exercise.name.lower() == name.lower():
                for s in exercise.sets:
                    if best is None or s.weight > best:
                        best = s.weight
        if best is not None:                    # None means "not found yet", so a weight of 0 still counts.
            points.append((session.date, best))
    return points


@app.route("/")
def home():
    my_tracker = load_tracker()
    # Pass only the count; homepage doesn't need the full tracker
    return render_template("home.html", sessions=len(my_tracker.sessions))


@app.route("/add", methods=["GET", "POST"])
def add():
    error = None
    if request.method == "POST":
        # Validate everything begore touching the tracker or the file,
        # so bad input can never be saved
        try: 
            date = request.form["date"]
            # Called only as a check: raises ValueError on a bad format.
            # date stays a string so it compares, sorts and serializes cleanly.
            datetime.strptime(date, "%Y-%m-%d")
            
            weight = float(request.form["weight"])
            if weight < 0: # zero is allowed (bodyweight exercises)
                raise ValueError ("Weight must be a number greater than or equal to zero.")
            
            reps = int(request.form["reps"])
            if reps <= 0:
                raise ValueError("Reps must be a number greater than zero.")

        except ValueError as e: # falls through to re-render the form with the message
            error = str(e)

        else:    
            # Runs only when validation passed
            tracker = load_tracker()
            sets = Sets(weight, reps)
            name = request.form["exercise"].strip()

            # Find the session for this date, or create it
            session = None
            for s in tracker.sessions:
                if s.date == date:
                    session = s
                    break

            if session is None:
                session = Session(date)
                tracker.add_session(session)

            # Find the exercise within that session, or create it.
            # Names are compared case-insensitively so "Bench" and "bench" merge.
            exercise = None
            for e in session.exercises:
                if e.name.lower() == name.lower():
                    exercise = e
                    break

            if exercise is None:
                exercise = Exercise(name)
                session.add_exercise(exercise)


            exercise.add_sets(sets)

            # Dates are YYYY-MM-DD strings, so alphabetical order is chronological order
            tracker.sessions = sorted(tracker.sessions, key = lambda s : s.date)

            # Writes the whole tracker back; saving only the new session would
            # overwrite everything already in the file
            with open("workout_data.json", "w") as f:
                json.dump(tracker.to_dict(), f, indent=4)

            # Redirect after a sucessfull POST so refreshing the page
            # doesn't resubmit the form
            return redirect(url_for("show_tracker"))
        
    # Reached on a plain FET, or when validation failed (error is set)
    return render_template("add.html", error=error)


@app.route("/tracker")
def show_tracker():
    my_tracker = load_tracker()
    # The template refers to this object as "workout"
    return render_template("sessions.html", workout=my_tracker)

@app.route("/stats")
def stats():
    my_tracker = load_tracker()
    result = max_weight_by_exercise(my_tracker)
    return render_template("stats.html", stat=result)

@app.route("/progress/<name>")     # <name> in the URL becomes the function argument.
def progress(name):
    points = weight_over_time(load_tracker(), name)
    return render_template("progress.html", name=name, points=points)

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True) # debug mode is for development only; turn off before deploying