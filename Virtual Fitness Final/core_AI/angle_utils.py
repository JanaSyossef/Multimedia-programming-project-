import numpy as np
import math


class AngleCalculator:
    """
    A utility class dedicated to calculating joint angles based on
    MediaPipe landmark coordinates.

    This class provides core geometrical logic for the AI Core module.
    """

    def calculate_angle(self, a, b, c):
        """
        Calculates the angle (in degrees) between three 2D points (A, B, C),
        where B is the vertex of the angle (the joint itself).

        Args:
            a (Landmark): The start point (e.g., Shoulder, Hip).
            b (Landmark): The vertex/joint (e.g., Elbow, Knee).
            c (Landmark): The end point (e.g., Wrist, Ankle).

        Returns:
            float: The calculated angle in degrees (0 to 180).
        """
        # Convert MediaPipe landmarks (a, b, c) into NumPy arrays (x, y coordinates)
        # We only use x and y for 2D angle calculation.
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])

        # Calculate the angle using the arctan2 method, which is robust
        # for handling different quadrants and calculating the angle between vectors BA and BC.
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
                  np.arctan2(a[1] - b[1], a[0] - b[0])

        # Convert radians to degrees and take the absolute value
        angle = np.abs(radians * 180.0 / np.pi)

        # Ensure the angle is the acute angle (internal angle), keeping it between 0 and 180.
        if angle > 180.0:
            angle = 360 - angle
        return angle

    def get_essential_angles(self, landmarks_list):
        """
        Calculates the four essential angles (Elbow, Knee, Hip, Shoulder)
        for tracking side view exercises like Squats, Lunges, or Pushups.

        Args:
            landmarks_list (list).

        Returns:
            dict: A dictionary containing the four calculated angles (float).
        """
        #   Landmark Indices (Standard MediaPipe Pose Model)
        LEFT_SHOULDER = 11
        LEFT_HIP = 23
        LEFT_ELBOW = 13
        LEFT_WRIST = 15
        LEFT_KNEE = 25
        LEFT_ANKLE = 27

        # 1. ELBOW_ANGLE: Angle at the elbow joint (Shoulder - Elbow - Wrist)
        elbow_angle = self.calculate_angle(
            landmarks_list[LEFT_SHOULDER],  # A
            landmarks_list[LEFT_ELBOW],  # B (Vertex)
            landmarks_list[LEFT_WRIST]  # C
        )

        # 2. KNEE_ANGLE: Angle at the knee joint (Hip - Knee - Ankle)
        knee_angle = self.calculate_angle(
            landmarks_list[LEFT_HIP],  # A
            landmarks_list[LEFT_KNEE],  # B (Vertex)
            landmarks_list[LEFT_ANKLE]  # C
        )

        # 3. HIP_ANGLE: Angle at the hip joint (Shoulder - Hip - Knee)
        hip_angle = self.calculate_angle(
            landmarks_list[LEFT_SHOULDER],  # A
            landmarks_list[LEFT_HIP],  # B (Vertex)
            landmarks_list[LEFT_KNEE]  # C
        )

        # 4. SHOULDER_ANGLE: Angle at the shoulder joint (Elbow - Shoulder - Hip)
        shoulder_angle = self.calculate_angle(
            landmarks_list[LEFT_ELBOW],  # A
            landmarks_list[LEFT_SHOULDER],  # B (Vertex)
            landmarks_list[LEFT_HIP]  # C
        )

        # Return the collected angles for the tracker/logic modules
        return {
            'KNEE_ANGLE': knee_angle,
            'ELBOW_ANGLE': elbow_angle,
            'HIP_ANGLE': hip_angle,
            'SHOULDER_ANGLE': shoulder_angle
        }
