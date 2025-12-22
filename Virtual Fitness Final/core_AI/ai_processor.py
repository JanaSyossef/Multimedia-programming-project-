import cv2
import mediapipe as mp


class CameraProcessor:
    """
    Handles initialization of the webcam and the MediaPipe Pose model.
    It provides a clean interface to fetch processed frames and pose landmarks.
    This class is the entry point for the AI Core module.
    """

    def __init__(self, camera_index=0):
        """
        Initializes the video capture device and the MediaPipe Pose Solution.

        Args:
            camera_index (int, optional): The index of the webcam (0 is usually the default).
        """
        # Initialize the webcam capture object
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            # Raise an error if the camera cannot be accessed
            raise IOError("Cannot open webcam or camera index is wrong.")

        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose

        # Initialize the MediaPipe Pose model with specific settings for performance
        self.pose = self.mp_pose.Pose(
            # static_image_mode=False: Optimizes for video processing (faster)
            static_image_mode=False,
            # model_complexity=1: Uses the lightweight model for better real-time performance
            model_complexity=1,
            # smooth_landmarks=True: Reduces jitter in landmark detection
            smooth_landmarks=True,
            # enable_segmentation=False: We don't need background segmentation, so we disable it
            enable_segmentation=False
        )

    def get_processed_frame(self):
        """
        Reads a frame from the camera, processes it using MediaPipe, and returns
        the image and the detected pose landmarks.

        Returns:
            tuple: (image, landmarks).
                   image (np.array): The processed frame (BGR format).
                   landmarks (mp.solution.pose.PoseLandmark): The detected pose landmarks, or None.
        """
        # Read a frame from the video stream
        success, image = self.cap.read()
        if not success:
            # Return None if reading the frame failed (stream ended)
            return None, None

        image = cv2.flip(image, 1)

        #  MediaPipe Processing Steps
        # 1. Prepare Image: Set image to read-only for performance
        image.flags.writeable = False
        # 2. Convert to RGB: MediaPipe requires RGB input
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # 3. Process Pose: Run the detection model
        results = self.pose.process(image)

        # 4. Finalize Image: Set image back to writeable
        image.flags.writeable = True
        # 5. Convert back to BGR: OpenCV uses BGR for display
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Return the processed image and the landmarks if detected
        if results.pose_landmarks:
            return image, results.pose_landmarks
        else:
            return image, None

    def release_camera(self):
        """
        Releases the webcam resources when the application is closing.
        Crucial to avoid camera access errors in future runs.
        """
        self.cap.release()
