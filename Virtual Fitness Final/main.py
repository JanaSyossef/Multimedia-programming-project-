import os
import time
from datetime import datetime

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk

from core_AI.ai_processor import CameraProcessor
from core_AI.angle_utils import AngleCalculator
from data_manager import WorkoutDataManager
from GUI.Gui import VirtualTrainerApp
from trackers.workout_detector import WorkoutDetector


# Function to recursively find a widget by its text
def find_widget_by_text(parent, text_pattern):
    try:
        # Standard tkinter/customtkinter text check
        if hasattr(parent, 'cget'):
            try:
                if text_pattern in parent.cget('text'):
                    return parent
            except: pass
    except: pass
    
    # CTkButton check
    if isinstance(parent, ctk.CTkButton):
         if text_pattern in parent._text:
             return parent

    # CTkLabel check for text storage
    if isinstance(parent, ctk.CTkLabel):
        if hasattr(parent, '_text') and text_pattern in parent._text:
            return parent

    # Recurse children
    children = parent.winfo_children()
    for child in children:
        result = find_widget_by_text(child, text_pattern)
        if result:
            return result
    return None

def find_option_menu(parent):
    # Search for the exercise option menu
    if isinstance(parent, ctk.CTkOptionMenu):
        return parent
    
    for child in parent.winfo_children():
        res = find_option_menu(child)
        if res: return res
    return None

# Main Application Class Integration
def main():
    # 1. Initialize the GUI Application
    # Initialize Data Manager First
    data_manager = WorkoutDataManager()
    
    # Pass it to the App
    app = VirtualTrainerApp(data_manager=data_manager)
    
    # 2. Initialize AI Components
    try:
        camera = CameraProcessor(camera_index=0)
    except Exception as e:
        print(f"Error initializing camera: {e}")
        camera = None

    angle_calc = AngleCalculator()
    workout_detector = WorkoutDetector()


    # 3. Dynamic GUI Injection: Video Display on WorkoutPage
    workout_page = app.frames["WorkoutPage"]
    
    video_frame = ctk.CTkFrame(workout_page, fg_color="transparent")
    video_frame.pack(side="top", fill="both", expand=True, padx=0, pady=(0,1000))
    video_label = ctk.CTkLabel(video_frame, text="")
    video_label.pack(fill="both", expand=True)

    # 4. State Variables
    app.is_timer_running = False
    app.camera_paused = False
    app.timer_seconds = 0
    app.last_time = time.time()


    # 5. Button Callbacks
    def toggle_timer():
        app.is_timer_running = not app.is_timer_running
        btn = find_widget_by_text(workout_page, "Timer")
        
        if app.is_timer_running:
            # START RECORDING
            app.camera_paused = False
            if btn: btn.configure(text="⏸ Stop Timer")
        else:
            # STOP / PAUSE
            if btn: btn.configure(text="▶ Start Timer")

    def manual_rep_complete():
        workout_detector.rep_count += 1
        workout_page.reps_label.configure(text=f"Reps: {workout_detector.rep_count}/{workout_page.target_reps}")
        progress = min(workout_detector.rep_count / workout_page.target_reps, 1.0)
        workout_page.progress_bar.set(progress)

    def reset_workout():
        # Reset counters
        workout_detector.reset()
        app.timer_seconds = 0
        app.is_timer_running = False
        
        # Reset GUI
        workout_page.reps_label.configure(text=f"Reps: 0/{workout_page.target_reps}")
        workout_page.progress_bar.set(0)
        workout_page.timer_label.configure(text="Time: 00:00")
        
        # Reset Timer Button Text
        btn = find_widget_by_text(workout_page, "Timer")
        if btn:
            btn.configure(text="▶ Start Timer")

    
    def save_workout():
        if workout_detector.rep_count > 0 or app.timer_seconds > 0:
            new_session = {
                "workoutType": workout_page.exercise_var.get(),
                "reps": workout_detector.rep_count,
                "duration": float(app.timer_seconds),
                "sessionEnded": True,
                "postureScores": [], 
                "timestamp": datetime.now().isoformat()
            }
            data_manager.save_session(new_session)
            print("Workout Saved Manually")

    # 6. Bind Buttons (Recursive Search)
    btn_start = find_widget_by_text(workout_page, "Start Timer")
    if btn_start:
        btn_start.configure(command=toggle_timer)
    
    btn_save = find_widget_by_text(workout_page, "Save")
    if btn_save:
        btn_save.configure(command=save_workout)

    btn_rep = find_widget_by_text(workout_page, "Rep Complete")
    if btn_rep:
        btn_rep.configure(command=manual_rep_complete)
        
    btn_reset = find_widget_by_text(workout_page, "Reset")
    if btn_reset:
        btn_reset.configure(command=reset_workout)

    # Auto-reset on exercise change
    workout_page.exercise_var.trace_add("write", lambda *args: reset_workout())

    # 7. Bind Exercise Page Buttons and Cleanup
    def select_exercise(exercise_name):
        print(f"Selected Exercise: {exercise_name}")
        workout_page.exercise_var.set(exercise_name)
        app.show_frame("WorkoutPage")

    def bind_exercise_buttons():
        try:
            exercises_page = app.frames["ExercisesPage"]
            grid_frame = None
            for child in exercises_page.winfo_children():
                if len(child.winfo_children()) > 2: # The cards
                    grid_frame = child
                    break
            
            if grid_frame:
                for card in grid_frame.winfo_children():
                    children = card.winfo_children()
                    if len(children) >= 4:
                        name_label = children[0]
                        
                        select_btn = None
                        for sub in children:
                            if isinstance(sub, ctk.CTkButton) and "Select" in sub._text:
                                select_btn = sub
                                break
                        
                        if select_btn and hasattr(name_label, 'cget'):
                            try:
                                # The label text now matches the IDs (e.g., "squat")
                                exercise_name = name_label._text 
                                select_btn.configure(command=lambda n=exercise_name: select_exercise(n))
                            except: pass
        except Exception as e:
            print(f"Error binding/cleaning exercise buttons: {e}")

    bind_exercise_buttons()

    # 8. Define the Main Update Loop
    def update_loop():
        current_time = time.time()
        
        # -- Timer Logic --
        if app.is_timer_running:
            if current_time - app.last_time >= 1.0:
                app.timer_seconds += 1
                app.last_time = current_time
                # Format time
                mins, secs = divmod(app.timer_seconds, 60)
                time_str = f"Time: {mins:02d}:{secs:02d}"
                workout_page.timer_label.configure(text=time_str)
        else:
            app.last_time = current_time

        # Only process AI if we are on the Workout Page
        if app.current_page == "WorkoutPage" and camera and not app.camera_paused:
            frame, landmarks = camera.get_processed_frame()
            
            if frame is not None:
                # -- AI Processing --
                if landmarks:
                    try:
                        lm_list = landmarks.landmark
                        angles = angle_calc.get_essential_angles(lm_list)
                        
                        # Sync Workout Type
                        dtype = workout_page.exercise_var.get()
                        
                        if workout_detector.workout_type != dtype:
                             workout_detector.workout_type = dtype
                             workout_detector.thresholds = workout_detector.workout_thresholds.get(dtype, workout_detector.workout_thresholds["general"])

                        # Detect Reps (Only if timer is running)
                        previous_reps = workout_detector.rep_count
                        if app.is_timer_running:
                            reps = workout_detector.detectReps(angles)
                        else:
                            # Ahmyd : toggle timer if the user reps
                            reps = workout_detector.detectReps(angles)
                            if reps:
                                toggle_timer()
                            
                        posture_score, feedback = workout_detector.detectPosture(angles)

                        # Determine Feedback Color & Priority
                        feedback_color = "#ffcc00" # Default yellow

                        priority = "low"
                        
                        if posture_score < 60:
                            feedback_text = f"Error: {feedback}"
                            feedback_color = "#ef4444" # Red
                            priority = "high"
                            # 80 was too high (always Warning)
                        elif posture_score < 75:
                            feedback_text = f"Warning: {feedback}"
                            feedback_color = "#ffcc00" # Yellow
                            priority = "low"
                        else:
                            feedback_text = feedback
                            feedback_color = "#00eaff" # Blue (PRIMARY)
                            priority = "low"

                        # Handle Rep Completion Feedback
                        if reps > previous_reps:
                            if posture_score >= 90:
                                rep_message = "Excellent! Perfect rep."
                            elif posture_score < 70:
                                rep_message = "Good, but correct your form."
                            else:
                                rep_message = "Rep completed."
                            
                            # workout_page.speak_feedback(rep_message, priority="high")
                            feedback_text = rep_message 
                        
                        # Session Complete Logic (15 Reps)
                        if reps >= 15:
                            workout_page.speak_feedback("Excellent work! Session complete.", priority="high")
                            save_workout()
                            reset_workout()
                            # app.camera_paused = False 
                            # return  <-- REMOVED to keep loop alive
                            last_processed_time = time.time()  # throttling placeholder logic if needed or pass

                        # Trigger Voice Feedback for Errors/Warnings
                        if posture_score < 80 and reps == previous_reps:
                             workout_page.speak_feedback(feedback_text, priority=priority)

                        # Update GUI
                        workout_page.update_gui_labels(reps, posture_score, feedback_text, feedback_color)


                        # Draw Landmarks
                        camera.mp_drawing.draw_landmarks(
                            frame, landmarks, camera.mp_pose.POSE_CONNECTIONS,
                             camera.mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                             camera.mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                        )
                        
                    except Exception as e:
                        print(f"Error in AI loop: {e}")

                # -- Video Display --
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                # --- CAMERA SCALE (Change this to resize the video feed) ---
                camera_scale =1  # <--- EDIT THIS (0.5 = half, 1.0 = normal)
                # -----------------------------------------------------------
                
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, 
                                     size=(int(740*camera_scale), int(470*camera_scale)))
                video_label.configure(image=ctk_img)
                video_label.image = ctk_img

        # Schedule next update
        app.after(10, update_loop)

    # Start the loop
    update_loop()

    # Handle Cleanup on Exit
    def on_closing():
        if camera:
            camera.release_camera()
        app.on_closing()

    app.protocol("WM_DELETE_WINDOW", on_closing)

    # Run App
    app.mainloop()

if __name__ == "__main__":
    print("Virtual Fitness Trainer Project Started!")
    main()
