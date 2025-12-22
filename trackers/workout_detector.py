"""
WorkoutDetector Module
Analyzes joint angle data to detect workout repetitions and evaluate posture quality.
Receives input from core_AI and outputs metrics to WorkoutSession.
"""

class WorkoutDetector:
    """
    Detects workout repetitions and evaluates posture based on joint angle measurements.
    
    Input Format (matches AngleCalculator output):
        angle_data = {
            'SHOULDER_ANGLE': float,
            'ELBOW_ANGLE': float,
            'HIP_ANGLE': float,
            'KNEE_ANGLE': float
        }
    
    Output:
        - detectReps(angle_data): Returns rep count (int)
        - detectPosture(angle_data): Returns tuple(posture score (int, 0-100), feedback (str))
    """
    
    def __init__(self, workout_type: str = "general"):
        """
        Initialize the WorkoutDetector with specific workout parameters.
        
        Args:
            workout_type (str): Type of workout to detect (e.g., "pushup", "squat", "bicep_curl")
        """
        self.workout_type = workout_type.lower()
        self.rep_count = 0
        self.in_rep = False  # Tracks if currently in a repetition
        self.previous_angles = None
        self.last_feedback = ""
        
        # Define threshold ranges for different workout types
        self.workout_thresholds = {
            "pushup": {
                "elbow_down": (70, 110),   # Elbow angle when down
                "elbow_up": (160, 180),    # Elbow angle when up
                "hip_min": 160,             # Hip should stay relatively straight
                "shoulder_min": 30
            },
            "squat": {
                "knee_down": (70, 110),    # Knee angle when squatting
                "knee_up": (160, 180),     # Knee angle when standing
                "hip_down": (70, 110),     # Hip angle when squatting
                "hip_up": (160, 180)       # Hip angle when standing
            },
            "bicep_curl": {
                "elbow_down": (150, 180),  # Arm extended
                "elbow_up": (30, 100),      # Arm curled
                "shoulder_stable": (150, 180)  # Shoulder should stay stable
            },
            "general": {
                "elbow_down": (70, 110),
                "elbow_up": (160, 180),
                "knee_down": (70, 110),
                "knee_up": (160, 180)
            }
        }
        
        self.thresholds = self.workout_thresholds.get(self.workout_type, self.workout_thresholds["general"])
    
    def detectReps(self, angle_data: dict) -> int:
        """
        Detects and counts repetitions based on joint angle data.
        
        Args:
            angle_data (dict): Dictionary containing joint angles from AngleCalculator
                {
                    'SHOULDER_ANGLE': float,
                    'ELBOW_ANGLE': float,
                    'HIP_ANGLE': float,
                    'KNEE_ANGLE': float
                }
        
        Returns:
            int: Current repetition count
        """
        if not angle_data:
            return self.rep_count
        
        # Convert to lowercase keys for internal processing
        normalized_data = {
            'shoulder': angle_data.get('SHOULDER_ANGLE', 180),
            'elbow': angle_data.get('ELBOW_ANGLE', 180),
            'hip': angle_data.get('HIP_ANGLE', 180),
            'knee': angle_data.get('KNEE_ANGLE', 180)
        }
        
        # Workout-specific rep detection logic
        if self.workout_type == "pushup":
            self.rep_count = self._detect_pushup_rep(normalized_data)
        elif self.workout_type == "squat":
            self.rep_count = self._detect_squat_rep(normalized_data)
        elif self.workout_type == "bicep_curl":
            self.rep_count = self._detect_bicep_curl_rep(normalized_data)
        else:
            self.rep_count = self._detect_general_rep(normalized_data)
        
        # Store current angles for next frame comparison
        self.previous_angles = normalized_data.copy()
        
        return self.rep_count
    
    def detectPosture(self, angle_data: dict) -> tuple[int, str]:
        """
        Evaluates posture quality based on joint angle data.
        
        Args:
            angle_data (dict): Dictionary containing joint angles from AngleCalculator
        
        Returns:
            tuple[int, str]: Posture score (0-100) and specific feedback message.
        """
        if not angle_data:
            return 0, "No data."
        
        # Convert to lowercase keys for internal processing
        normalized_data = {
            'shoulder': angle_data.get('SHOULDER_ANGLE', 180),
            'elbow': angle_data.get('ELBOW_ANGLE', 180),
            'hip': angle_data.get('HIP_ANGLE', 180),
            'knee': angle_data.get('KNEE_ANGLE', 180)
        }
        
        # Workout-specific posture evaluation
        if self.workout_type == "pushup":
            score, feedback = self._evaluate_pushup_posture(normalized_data)
        elif self.workout_type == "squat":
            score, feedback = self._evaluate_squat_posture(normalized_data)
        elif self.workout_type == "bicep_curl":
            score, feedback = self._evaluate_bicep_curl_posture(normalized_data)
        else:
            score, feedback = self._evaluate_general_posture(normalized_data)
            
        self.last_feedback = feedback
        return score, feedback
    
    # Private helper methods for push-up detection
    def _detect_pushup_rep(self, angle_data: dict) -> int:
        """Detects push-up repetitions based on elbow angle."""
        elbow = angle_data.get('elbow', 180)
        
        # Check if in down position (elbow bent)
        if not self.in_rep and self.thresholds["elbow_down"][0] <= elbow <= self.thresholds["elbow_down"][1]:
            self.in_rep = True
        
        # Check if returned to up position (elbow extended)
        elif self.in_rep and elbow >= self.thresholds["elbow_up"][0]:
            self.in_rep = False
            self.rep_count += 1
        
        return self.rep_count
    
    def _evaluate_pushup_posture(self, angle_data: dict) -> tuple[int, str]:
        """Evaluates push-up posture quality and generates specific feedback."""
        score = 100
        feedback = "Excellent form. Keep focusing."
        
        hip = angle_data.get('hip', 180)
        shoulder = angle_data.get('shoulder', 180)
        
        # Deduct points for improper hip alignment (sagging or piking)
        if hip < self.thresholds["hip_min"]:
            deduction = min(30, (self.thresholds["hip_min"] - hip) / 2)
            score -= deduction
            if deduction > 15:
                 feedback = "Tighten your core and glutes to stabilize your back!"
            elif deduction > 5:
                feedback = "Keep your body straight like a plank."
        
        # Deduct points for improper shoulder position
        if shoulder < self.thresholds["shoulder_min"]:
            deduction = min(20, (self.thresholds["shoulder_min"] - shoulder) / 2)
            score -= deduction
             # Only update feedback if it's the primary error
            if deduction > 10 and feedback == "Excellent form. Keep focusing.":
                 feedback = "Lift your chest, don't let your shoulders collapse."
        
        return max(0, int(score)), feedback
    
    # Private helper methods for squat detection
    def _detect_squat_rep(self, angle_data: dict) -> int:
        """Detects squat repetitions based on knee and hip angles."""
        knee = angle_data.get('knee', 180)
        hip = angle_data.get('hip', 180)
        
        # Check if in down position (squatting)
        if not self.in_rep and (
            self.thresholds["knee_down"][0] <= knee <= self.thresholds["knee_down"][1] and
            self.thresholds["hip_down"][0] <= hip <= self.thresholds["hip_down"][1]
        ):
            self.in_rep = True
        
        # Check if returned to standing position
        elif self.in_rep and knee >= self.thresholds["knee_up"][0] and hip >= self.thresholds["hip_up"][0]:
            self.in_rep = False
            self.rep_count += 1
        
        return self.rep_count
    
    def _evaluate_squat_posture(self, angle_data: dict) -> tuple[int, str]:
        """Evaluates squat posture quality."""
        score = 100
        feedback = "Excellent form. Keep your balance."
        
        knee = angle_data.get('knee', 180)
        hip = angle_data.get('hip', 180)
        
        # Check for proper depth and form
        if self.in_rep:
            # Deduct points if not squatting deep enough
            if knee > self.thresholds["knee_down"][1]:
                deduction = min(25, (knee - self.thresholds["knee_down"][1]) / 2)
                score -= deduction
                if deduction > 10:
                    feedback = "Go deeper. Push your hips back."
            
            # Deduct points if hip-knee coordination is off
            angle_diff = abs(knee - hip)
            if angle_diff > 30:
                deduction = min(20, angle_diff / 2)
                score -= deduction
                if deduction > 10 and feedback == "Excellent form. Keep your balance.":
                     feedback = "Watch for back arching! Keep your chest up."
        
        return max(0, int(score)), feedback
    
    # Private helper methods for bicep curl detection
    def _detect_bicep_curl_rep(self, angle_data: dict) -> int:
        """Detects bicep curl repetitions based on elbow angle."""
        elbow = angle_data.get('elbow', 180)
        
        # Check if in curled position (elbow bent)
        if not self.in_rep and self.thresholds["elbow_up"][0] <= elbow <= self.thresholds["elbow_up"][1]:
            self.in_rep = True
        
        # Check if returned to extended position
        elif self.in_rep and elbow >= self.thresholds["elbow_down"][0]:
            self.in_rep = False
            self.rep_count += 1
        
        return self.rep_count
    
    def _evaluate_bicep_curl_posture(self, angle_data: dict) -> tuple[int, str]:
        """Evaluates bicep curl posture quality."""
        score = 100
        feedback = "Excellent form. Good muscle isolation."
        
        shoulder = angle_data.get('shoulder', 180)
        elbow = angle_data.get('elbow', 180)
        
        # Deduct points for shoulder movement (should stay stable)
        if shoulder < self.thresholds["shoulder_stable"][0]:
            deduction = min(30, (self.thresholds["shoulder_stable"][0] - shoulder) / 2)
            score -= deduction
            if deduction > 15:
                 feedback = "Don't swing your shoulder! Keep your upper arm steady."
        
        # Deduct points for incomplete range of motion
        if self.in_rep and elbow > self.thresholds["elbow_up"][1]:
            deduction = min(20, (elbow - self.thresholds["elbow_up"][1]) / 2)
            score -= deduction
            if deduction > 10 and feedback == "Excellent form. Good muscle isolation.":
                 feedback = "Squeeze up more. Complete the rep."
        
        return max(0, int(score)), feedback
    
    # General detection methods (fallback)
    def _detect_general_rep(self, angle_data: dict) -> int:
        """Generic rep detection for undefined workout types."""
        # Simple detection based on primary joint movement
        primary_angle = angle_data.get('elbow') or angle_data.get('knee', 180)
        
        if not self.in_rep and primary_angle <= 110:
            self.in_rep = True
        elif self.in_rep and primary_angle >= 160:
            self.in_rep = False
            self.rep_count += 1
        
        return self.rep_count
    
    def _evaluate_general_posture(self, angle_data: dict) -> tuple[int, str]:
        """Generic posture evaluation."""
        # Basic posture check - penalize extreme angles
        score = 100
        feedback = "Good general movement."
        
        for joint, angle in angle_data.items():
            if angle < 30:  # Too bent
                score -= 10
            elif angle > 190:  # Hyperextended
                score -= 10
        
        return max(0, int(score)), feedback
    
    def reset(self):
        """Resets the rep counter and state for a new workout session."""
        self.rep_count = 0
        self.in_rep = False
        self.previous_angles = None
        self.last_feedback = ""
    
    def get_current_state(self) -> dict:
        """
        Returns the current state of the detector.
        
        Returns:
            dict: Current detector state including rep count and workout type
        """
        return {
            "workout_type": self.workout_type,
            "rep_count": self.rep_count,
            "in_rep": self.in_rep,
            "last_feedback": self.last_feedback
        }
