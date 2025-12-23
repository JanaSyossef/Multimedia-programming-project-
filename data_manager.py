import csv
import os
import io

class WorkoutDataManager:
    def __init__(self, storage_file="storage/data.csv"):
        self.storage_file = storage_file
        self.fieldnames = ["id", "workoutType", "reps", "duration", "sessionEnded", "postureScores", "timestamp"]
        self.ensure_storage_exists()

    def ensure_storage_exists(self):
        """Ensures the storage directory and file exist."""
        directory = os.path.dirname(self.storage_file)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()

    def load_sessions(self):
        """Loads all workout sessions from the CSV file."""
        if not os.path.exists(self.storage_file):
            return []
            
        try:
            with open(self.storage_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception:
            return []

    def save_session(self, session_data):
        """Saves a new workout session to the CSV file."""
        sessions = self.load_sessions()
        
        # Generate a simple ID based on existing count if not provided
        if "id" not in session_data:
            session_data["id"] = str(len(sessions))
            
        # Ensure only known fields are written
        row = {k: session_data.get(k, "") for k in self.fieldnames}
        
        # Handle list serialization for postureScores if needed
        if isinstance(row.get("postureScores"), list):
             row["postureScores"] = ";".join(map(str, row["postureScores"]))

        with open(self.storage_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            # Write header if file is empty (though ensure_exists handles this, safe check)
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(row)
        
        print(f"Session saved: {session_data}")
