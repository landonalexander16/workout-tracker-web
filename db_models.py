from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    workouts = db.relationship("Workout", backref="athlete", cascade="all, delete-orphan")

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    exercises = db.relationship("WorkoutExercise", backref="workout", cascade = "all, delete-orphan")

class WorkoutExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    workout_id = db.Column(db.Integer, db.ForeignKey("workout.id"), nullable=False)
    sets = db.relationship("WorkoutSet", backref="exercise", cascade="all, delete-orphan")

class WorkoutSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    workout_exercise_id = db.Column(db.Integer, db.ForeignKey("workout_exercise.id"), nullable=False)