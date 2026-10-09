"""Flask web interface for the workout tracker.

Routes: home (workout count), add (log a set), show_workout (view history),
        stats (max weight and reps per exercise), progress (max weight over time chart).
Data is stored in a SQLite database (instance/workout.db) through the SQLAlchemy
models in db_models.py. Every workout currently belongs to a placeholder "demo"
user; real accounts come later.
"""

from flask import Flask, render_template, request, redirect, url_for, abort
from datetime import datetime
from db_models import db, User, Workout, WorkoutExercise, WorkoutSet
import os
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///workout.db" # file is created in instance/
db.init_app(app)   # must come after the config line, because it reads the database path

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"    

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def get_workouts():
    """Return the demo user's workouts, oldest first (the database sorts by date)."""
    user = current_user
    return Workout.query.filter_by(user_id=user.id).order_by(Workout.date).all()

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

def parse_set_form(form):
    weight = float(form["weight"])
    if weight < 0: # zero is allowed (bodyweight exercises)
        raise ValueError ("Weight must be a number greater than or equal to zero.")
    reps = int(form["reps"])
    if reps <= 0:
        raise ValueError("Reps must be a number greater than zero.")
    return weight, reps

def get_my_set(set_id):
    s = db.get_or_404(WorkoutSet, set_id)
    if s.exercise.workout.user_id != current_user.id:
        abort(404)
    return s

def get_my_exercise(exercise_id):
    exercise = db.get_or_404(WorkoutExercise, exercise_id)
    if exercise.workout.user_id != current_user.id:
        abort(404)
    return exercise

def get_my_workout(workout_id):
    workout = db.get_or_404(Workout, workout_id)
    if workout.user_id != current_user.id:
        abort(404)
    return workout

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        if not username or len(password) < 8:
            error = "Enter an username and password of at least 8 characters"
        elif User.query.filter_by(username=username).first():
            error = "That username is already registered"
        else:
            user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("home"))
    return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user is None or not check_password_hash(user.password_hash, password):
            error = "Invalid username or password."
        else: 
            login_user(user)
            return redirect(url_for("home"))
    return render_template("login.html", error=error)

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))    

@app.route("/")
def home():
    if current_user.is_authenticated:
        count = len(get_workouts())
    else:
        count = 0
    # Pass only the count; the homepage doesn't need the workouts themselves
    return render_template("home.html", sessions=count)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    error = None
    if request.method == "POST":
        # Validate everything before touching the database
        # so bad input can never be saved
        try: 
            date = request.form["date"]
            # Called only as a check: raises ValueError on a bad format.
            datetime.strptime(date, "%Y-%m-%d")
            weight, reps = parse_set_form(request.form)
            
        except ValueError as e: # falls through to re-render the form with the message
            error = str(e)

        else:
            # Runs only when validation passed. Find or create this user's workout
            # for the date, then the exercise inside it, then add the set.    
            user = current_user

            # The database column is a real date, so convert the string from the form
            workout_date =  datetime.strptime(date, "%Y-%m-%d").date()
            workout = Workout.query.filter_by(user_id=user.id, date=workout_date).first()
            if workout is None:
                workout = Workout(date=workout_date, user_id=current_user.id)
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
@login_required
def show_workout():
    my_workout = get_workouts()
    # The template loops over this list: workouts > exercises > sets
    return render_template("sessions.html", workouts=my_workout)

@app.route("/stats")
@login_required
def stats():
    workouts = get_workouts()
    result = max_weight_by_exercise(workouts)
    return render_template("stats.html", stat=result)

@app.route("/progress/<name>")     # <name> in the URL becomes the function argument.
@login_required
def progress(name):
    workouts = get_workouts()
    points = weight_over_time(workouts, name)
    return render_template("progress.html", name=name, points=points)

@app.route("/set/<int:set_id>/delete", methods=["POST"])
@login_required
def delete_set(set_id):
    workout_set = get_my_set(set_id)
    exercise = workout_set.exercise
    workout = exercise.workout

    db.session.delete(workout_set)
    db.session.commit()

    if not exercise.sets:
        db.session.delete(exercise)
        db.session.commit()

        if not workout.exercises:
            db.session.delete(workout)
            db.session.commit()

    return redirect(url_for("show_workout"))

@app.route("/set/<int:set_id>/edit", methods=["GET", "POST"])
@login_required
def edit_set(set_id):
    s = get_my_set(set_id)
    error = None
    if request.method == "POST":
        try:
            weight, reps = parse_set_form(request.form)
        except ValueError as e:
            error = str(e)
        else:
            s.weight = weight
            s.reps = reps
            db.session.commit()
            return redirect(url_for("show_workout"))
    return render_template("edit_set.html", s=s, error=error)

@app.route("/exercise/<int:exercise_id>/delete", methods=["POST"])
@login_required
def delete_exercise(exercise_id):
    exercise = get_my_exercise(exercise_id)
    workout = exercise.workout
    db.session.delete(exercise)
    db.session.commit()
    if not workout.exercises:
        db.session.delete(workout)
        db.session.commit()
    return redirect(url_for("show_workout"))
    
@app.route("/workout/<int:workout_id>/delete", methods=["POST"])
@login_required
def delete_workout(workout_id):
    workout = get_my_workout(workout_id)
    db.session.delete(workout)
    db.session.commit()
    return redirect(url_for("show_workout"))


with app.app_context():
    db.create_all()   # creates any missing tables on startup; never alters existing ones

if __name__ == "__main__":
    app.run(debug=True) # debug mode is for development only; turn off before deploying