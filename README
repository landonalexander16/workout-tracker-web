# Workout Tracker (Web)

A Flask web app for logging workouts and tracking strength progress over time. It's the web version of my [command-line workout tracker](https://github.com/landonalexander16/workout-tracker), reusing the same data model.

## Features

- Log sets (date, exercise, weight, reps) through a web form
- Entries merge automatically: a new set goes into the existing session for that date and the existing exercise with the same name, ignoring capitalization
- Server-side validation of dates, weights, and reps, with error messages shown on the form
- Stats page showing the heaviest weight (and the reps done at it) for each exercise
- Progress chart for each exercise: max weight by date, drawn with Chart.js
- Handles a missing or corrupted data file by starting fresh and keeping a copy of the bad file

## Tech Stack

Python, Flask, Jinja2 templates, Chart.js, JSON file storage

## Setup

1. Clone the repo:
```
   git clone https://github.com/landonalexander16/workout-tracker-web.git
   cd workout-tracker-web
```
2. Create and activate a virtual environment:
```
   python -m venv venv
   venv\Scripts\activate        # Windows (PowerShell)
   source venv/bin/activate     # Mac/Linux
```
3. Install dependencies:
```
   pip install -r requirements.txt
```
4. Run the app:
```
   python app.py
```
5. Open http://127.0.0.1:5000 in your browser.

Workout data is saved to `workout_data.json`, which is created on the first entry. It isn't included in the repo, so a fresh clone starts empty.

## Project Structure

- `app.py`: routes, data loading, and the analytics functions
- `models.py`: `Sets`, `Exercise`, `Session`, and `WorkoutTracker` classes with JSON serialization, ported from the CLI version
- `templates/`: Jinja templates, all extending a shared `base.html`

## Planned

- Move storage from a JSON file to a database (SQLAlchemy)
- User accounts, so each person sees only their own workouts
- Deployment with a live demo link
- Screenshots