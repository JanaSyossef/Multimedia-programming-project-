
# Imports ====================================================================================
from datetime import datetime
from trackers.DataStore import DataStore

# Classes ====================================================================================
class WorkoutSession:
    all_sessions = []
    dataStoreName = "./storage/WorkoutSessions"

    def __init__(self, workoutType: str, id: str = None, reps: int = 0, duration: float = 0, sessionEnded: bool = False, postureScores: list = None, timestamp: datetime = None):
        if id is None:
            id = str(len(WorkoutSession.all_sessions))
        self.id = id
        self.workoutType = workoutType
        self.reps = reps
        self.duration = duration
        self.sessionEnded = sessionEnded
        self.postureScores = postureScores if postureScores is not None else []
        self.timestamp = timestamp if timestamp is not None else datetime.now().isoformat()

        WorkoutSession.all_sessions.append(self)

    # Instance methods ====================================================================================
    def addRep(self):
        self.reps += 1

    def endSession(self):
        if self.sessionEnded:
            return
        self.sessionEnded = True
        start = datetime.fromisoformat(self.timestamp)
        self.duration = (datetime.now() - start).total_seconds()

    # Static methods ====================================================================================
    @staticmethod
    def saveSessions():
        DataStore.saveData(WorkoutSession.dataStoreName, WorkoutSession.all_sessions)

    @staticmethod
    def loadSessions():
        return DataStore.loadData(WorkoutSession.dataStoreName)

    @staticmethod
    def loadSessionByID(id):
        data = WorkoutSession.loadSessions()
        for item in data:
            if item["id"] == id:
                return WorkoutSession(**item)
        return None

    @classmethod
    def loadAllSessions(cls):
        cls.all_sessions.clear() # Clear existing session in memory to avoid duplicates on reload
        try:
            data = cls.loadSessions()
            if data:
                for item in data:
                    cls(**item)
        except Exception as e:
            print(f"No existing sessions found or error loading: {e}")
            
        return cls.all_sessions

    @classmethod
    def endAllSessions(cls):
        for session in cls.all_sessions:
            session.endSession()
        cls.saveSessions()
        DataStore.flatten_for_analysis(cls.all_sessions)

    def __init__(self, workoutType: str, id: str = None, reps: int = 0, duration: float = 0, sessionEnded: bool = False, postureScores: list = None, timestamp: datetime = None):
        if id is None:
            id = str(len(WorkoutSession.all_sessions))
        self.id = id
        self.workoutType = workoutType
        self.reps = reps
        self.duration = duration
        self.sessionEnded = sessionEnded
        self.postureScores = postureScores if postureScores is not None else []
        self.timestamp = timestamp if timestamp is not None else datetime.now().isoformat()

        WorkoutSession.all_sessions.append(self)

    # Instance methods ====================================================================================
    def addRep(self):
        self.reps += 1

    def endSession(self):
        if self.sessionEnded:
            return
        self.sessionEnded = True
        start = datetime.fromisoformat(self.timestamp)
        self.duration = (datetime.now() - start).total_seconds()

    # Static methods ====================================================================================
    @staticmethod
    def saveSessions():
        DataStore.saveData(WorkoutSession.dataStoreName, WorkoutSession.all_sessions)

    @staticmethod
    def loadSessions():
        return DataStore.loadData(WorkoutSession.dataStoreName)

    @staticmethod
    def loadSessionByID(id):
        data = WorkoutSession.loadSessions()
        for item in data:
            if item["id"] == id:
                return WorkoutSession(**item)
        return None

    @classmethod
    def loadAllSessions(cls):
        cls.all_sessions.clear() # Clear existing session in memory to avoid duplicates on reload
        try:
            data = cls.loadSessions()
            if data:
                for item in data:
                    cls(**item)
        except Exception as e:
            print(f"No existing sessions found or error loading: {e}")
            
        return cls.all_sessions

    @classmethod
    def endAllSessions(cls):
        for session in cls.all_sessions:
            session.endSession()
        cls.saveSessions()
        DataStore.flatten_for_analysis(cls.all_sessions)

# Testing ====================================================================================
def test():
    WorkoutSession.loadAllSessions()
    WorkoutSession.endAllSessions()
    WorkoutSession.loadSessionByID('1')
    print(WorkoutSession.all_sessions)
    # print(WorkoutSession.all_sessions)

test()
