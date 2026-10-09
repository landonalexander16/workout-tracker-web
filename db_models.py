"""SQLAlchemy models: User > Workout > WorkoutExercise > WorkoutSet.

Each child table stores the id of its parent (a foreign key). The relationships
let code move between levels like lists: workout.exercises, exercise.sets.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"  # "user" is a reserved word in PostgreSQL
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    workouts = db.relationship("Workout", backref="athlete", cascade="all, delete-orphan")
    # cascade: deleting a user also deletes their workouts. backref adds workout.athlete.

class Workout(db.Model):
    # one workout per user per date (enforced by the constraint)
    __table_args__ = (db.UniqueConstraint("user_id", "date"),)
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    exercises = db.relationship("WorkoutExercise", backref="workout", cascade ="all, delete-orphan")

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
