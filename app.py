"""Flask web interface for the workout tracker.

Routes: home (workout count), add (log a set), show_workout (view history),
        stats (max weight and reps per exercise), progress (max weight over time chart).
Data is stored in a SQLite database (instance/workout.db) through the SQLAlchemy
models in db_models.py. Every workout currently belongs to a placeholder "demo"
user; real accounts come later.
"""

import json
from models import WorkoutTracker, Session, Exercise, Sets
from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import datetime
from db_models import db, User, Workout, WorkoutExercise, WorkoutSet

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///workout.db" # file is created in instance/
db.init_app(app)   # must come after the config line, because it reads the database path

def get_demo_user():
    """Return the placeholder user, creating it on first use.

    Replaced by the logged-in user once login is added.
    """
    user = User.query.filter_by(username="demo").first()
    if user is None:
        user = User(username="demo", password_hash="placeholder")
        db.session.add(user)
        db.session.commit()
    return user

def get_workouts():
    """Return the demo user's workouts, oldest first (the database sorts by date)."""
    user = get_demo_user()
    return Workout.query.filter_by(user_id=user.id).order_by(Workout.date).all()

def load_tracker():
    """Read the old workout_data.json. Only used for the one-time import into the database."""
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

def max_weight_by_exercise(workouts):
    """Return {exercise name (lowercase): (weight, reps)} for each exercise's best set.

    workouts is a list of Workout rows. Names are lowercased so "Bench" and "bench"
    count as one exercise. The best set is the heaviest; ties go to the set with more reps.
    """
    best = {}                                    # exercise name -> highest weight and reps logged so far
    for workout in workouts:                     # level 1
        for exercise in workout.exercises:       # level 2: the thing we group by
            key = exercise.name.lower()          # same exercise in any capitalization
            for s in exercise.sets:              # level 3: the values we compare
                if key not in best or (s.weight, s.reps) > best[key]:     # This condition allows a weight of 0 be stored
                    best[key] = (s.weight, s.reps)
    return best

def weight_over_time(workouts, name):
    """Return [(date, heaviest weight that day), ...] for one exercise.

    Workouts arrive ordered by date, so the list is too. Dates where the exercise
    wasn't done are left out. Dates are converted to "YYYY-MM-DD" strings, because
    the chart needs text labels.
    """
    points = []
    for workout in workouts:            
        best = None
        for exercise in workout.exercises:
            if exercise.name.lower() == name.lower():
                for s in exercise.sets:
                    if best is None or s.weight > best:
                        best = s.weight
        if best is not None:                    # None means "not found yet", so a weight of 0 still counts.
            points.append((str(workout.date), best))  # str() because tojson would turn a date object into a long GMT-style string
    return points


@app.route("/")
def home():
    my_workouts = get_workouts()
    # Pass only the count; the homepage doesn't need the workouts themselves
    return render_template("home.html", sessions=len(my_workouts))


@app.route("/add", methods=["GET", "POST"])
def add():
    error = None
    if request.method == "POST":
        # Validate everything begore touching the tracker or the file,
        # so bad input can never be saved
        try: 
            date = request.form["date"]
            # Called only as a check: raises ValueError on a bad format.
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
            # Runs only when validation passed. Find or create this user's workout
            # for the date, then the exercise inside it, then add the set.    
            user = get_demo_user()

            # The database column is a real date, so convert the string from the form
            workout_date =  datetime.strptime(date, "%Y-%m-%d").date()
            workout = Workout.query.filter_by(user_id=user.id, date=workout_date).first()
            if workout is None:
                workout = Workout(date=workout_date, athlete=user)
                db.session.add(workout)

            name = request.form["exercise"].strip()
            workout_exercise = None
            for e in workout.exercises:
                if e.name.lower() == name.lower():   # Names are compared case-insensitively so "Bench" and "bench" merge.
                    workout_exercise = e
                    break
            if workout_exercise is None:
                workout_exercise = WorkoutExercise(name=name, workout=workout)
                db.session.add(workout_exercise)
            
            db.session.add(WorkoutSet(exercise = workout_exercise, weight=weight, reps=reps))
            db.session.commit()
            return redirect(url_for("add"))  # Redirect after a successful save so refreshing doesn't resubmit the form
        
    # Reached on a plain GET, or when validation failed (error is set)
    return render_template("add.html", error=error)


@app.route("/tracker")
def show_workout():
    my_workout = get_workouts()
    # The template loops over this list: workouts > exercises > sets
    return render_template("sessions.html", workouts=my_workout)

@app.route("/stats")
def stats():
    workouts = get_workouts()
    result = max_weight_by_exercise(workouts)
    return render_template("stats.html", stat=result)

@app.route("/progress/<name>")     # <name> in the URL becomes the function argument.
def progress(name):
    workouts = get_workouts()
    points = weight_over_time(workouts, name)
    return render_template("progress.html", name=name, points=points)

with app.app_context():
    db.create_all()   # creates any missing tables on startup; never alters existing ones

if __name__ == "__main__":
    app.run(debug=True) # debug mode is for development only; turn off before deploying