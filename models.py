
class Sets:
    def __init__(self, weight, reps):
        self.weight = weight
        self.reps = reps

    # This method converts the Sets instance into a dictionary format.
    def to_dict(self):
        return {
            "weight": self.weight,
            "reps": self.reps
        }

    #This method creates a new Sets instance from a dictionary containing the weight and reps values.
    @staticmethod
    def from_dict(data):
        return Sets(data["weight"], data["reps"])

class Exercise:
    def __init__(self, name):
        self.name = name
        self.sets = []

    def add_sets(self, sets):
        self.sets.append(sets)
    
    # This method converts the Exercise instance into a dictionary format, including the exercise name and a list of sets represented as dictionaries.
    def to_dict(self):
        return {
            "exercise": self.name,
            "sets": [s.to_dict() for s in self.sets]
        }

    # This method creates a new Exercise instance from a dictionary containing the exercise name and a list of sets represented as dictionaries.
    # It uses the from_dict method of the Sets class to create Sets objects for each set in the list.
    @staticmethod
    def from_dict(data):
        exercise = Exercise(data["exercise"])
        exercise.sets = [Sets.from_dict(s) for s in data["sets"]]
        return exercise



class Session:
    def __init__(self, date):
        self.date = date
        self.exercises = []

    def add_exercise(self, exercise):
        self.exercises.append(exercise)

    # This method converts the Session instance into a dictionary format, including the session date and a list of exercises represented as dictionaries.
    def to_dict(self):
        return {
            "date": self.date,
            "exercises": [e.to_dict() for e in self.exercises]
        }

    # This method creates a new Session instance from a dictionary containing the session date and a list of exercises represented as dictionaries.
    # It uses the from_dict method of the Exercise class to create Exercise objects for each exercise in the list.
    @staticmethod
    def from_dict(data):
        session = Session(data["date"])
        session.exercises = [Exercise.from_dict(e) for e in data["exercises"]]
        return session

class WorkoutTracker:
    def __init__(self):
        self.sessions = []

    def add_session(self, session):
        self.sessions.append(session)

    # This method converts the WorkoutTracker instance into a dictionary format, including a list of sessions represented as dictionaries.
    def to_dict(self):
        return {
            "sessions": [s.to_dict() for s in self.sessions]
        }

    # This method creates a new WorkoutTracker instance and populates it with Session objects created from the provided dictionary data. 
    # It iterates through the list of sessions in the data, creating a Session object for each one using the from_dict method of the Session class,
    # and adds them to the sessions list of the WorkoutTracker instance.
    @staticmethod
    def from_dict(data):
        tracker = WorkoutTracker()
        tracker.sessions = [Session.from_dict(s) for s in data["sessions"]]
        return tracker