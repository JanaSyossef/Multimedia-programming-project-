
import json
import math
import os
import threading
import time
import tkinter as tk
from datetime import datetime
from datetime import time as dt_time
from tkinter import Canvas

import cv2
import numpy as np
import pyttsx3
from customtkinter import *

# Global lock for TTS to prevent run loop errors
tts_lock = threading.Lock()

# ---- dark theme ------------------
set_appearance_mode("Dark")
set_default_color_theme("dark-blue")

# CORE COLORS (Tuple format: (Light, Dark))
PRIMARY = "#00eaff"    
SECONDARY = "#278495"  
BG_DARK = "#121427"
BG_DEEP = "#1a1b2e" # Dark mode card background
TEXT_LIGHT = "#e2e8f0"
BORDER = "#2dd4bf"

# LIGHT COLORS
LIGHT_BG = "#555992"
LIGHT_CARD = "#e2e8f0" # Light mode card background (brighter)
LIGHT_TEXT = "#1e293b"
LIGHT_BORDER = "#cbd5e1"
LIGHT_PRIMARY = "#0ea5e9"
LIGHT_SECONDARY = "#6366f1"

# --- THEME TUPLES (Automatic Switching) ---
# Format: (Light_Value, Dark_Value)
THEME_BG = (LIGHT_BG, BG_DARK)
THEME_BG_TRANSPARENT = (LIGHT_BG, BG_DARK) 
THEME_CARD = (LIGHT_CARD, BG_DEEP) 
THEME_TEXT = (LIGHT_TEXT, TEXT_LIGHT)
THEME_PRIMARY = (LIGHT_PRIMARY, PRIMARY)
THEME_SECONDARY = (LIGHT_SECONDARY, SECONDARY)
THEME_BORDER = (LIGHT_BORDER, BORDER)


class WaterReminder:
    """Class to manage water intake tracking and reminders"""
    def __init__(self, user_file="storage/user.json"):
        self.user_file = user_file
        self.reminder_interval = 3600  # 1 hour in seconds
        self.last_reminder_time = 0
        self.reminder_active = True
        
    def get_user_data(self):
        """Get user water goal from user profile"""
        try:
            if os.path.exists(self.user_file):
                with open(self.user_file, 'r') as f:
                    data = json.load(f)
                    daily_goal = int(data.get('dailyWaterNeeds', 3000))
                    current_intake = int(data.get('waterDrunk', 0))
                    return daily_goal, current_intake
        except:
            pass
        return 3000, 0  # Default values
    
    def add_water(self, amount_ml=250):
        """Add water intake to user profile"""
        try:
            data = {}
            if os.path.exists(self.user_file):
                with open(self.user_file, 'r') as f:
                    data = json.load(f)
            
            current = int(data.get('waterDrunk', 0))
            data['waterDrunk'] = current + amount_ml
            
            # Update last drink time
            data['lastDrinkTime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self.user_file, 'w') as f:
                json.dump(data, f, indent=4)
            
            return data['waterDrunk']
        except Exception as e:
            print(f"Error saving water intake: {e}")
            return 0
    
    def reset_daily_intake(self):
        """Reset water intake for new day"""
        try:
            data = {}
            if os.path.exists(self.user_file):
                with open(self.user_file, 'r') as f:
                    data = json.load(f)
            
            data['waterDrunk'] = 0
            data['lastDrinkTime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self.user_file, 'w') as f:
                json.dump(data, f, indent=4)
        except:
            pass
    
    def check_time_for_reset(self):
        """Check if it's a new day (after 5 AM) and reset if needed"""
        now = datetime.now()
        try:
            if os.path.exists(self.user_file):
                with open(self.user_file, 'r') as f:
                    data = json.load(f)
                
                last_reset_str = data.get('lastResetDate', '')
                if last_reset_str:
                    last_reset = datetime.strptime(last_reset_str, "%Y-%m-%d")
                    if now.date() > last_reset.date() and now.hour >= 5:
                        self.reset_daily_intake()
                        data['lastResetDate'] = now.strftime("%Y-%m-%d")
                        with open(self.user_file, 'w') as f:
                            json.dump(data, f, indent=4)
        except:
            pass
    
    def should_remind(self):
        """Check if it's time for a reminder"""
        if not self.reminder_active:
            return False
        
        current_time = time.time()
        if current_time - self.last_reminder_time >= self.reminder_interval:
            daily_goal, current_intake = self.get_user_data()
            progress = (current_intake / daily_goal) * 100 if daily_goal > 0 else 0
            
            # Don't remind if user already drank enough
            if progress >= 100:
                return False
            
            # Check if within reasonable hours (8 AM to 10 PM)
            hour = datetime.now().hour
            if 8 <= hour <= 22:
                self.last_reminder_time = current_time
                return True
        
        return False

class VirtualTrainerApp(CTk):
    def __init__(self, data_manager=None):
        super().__init__()
        self.data_manager = data_manager
        self.water_reminder = WaterReminder()
        self.title("🏋️ Virtual Fitness Trainer")
        self.geometry("1920x1080")
        self.resizable(True, True)

        # crack current theme
        self.current_theme = "dark"

        self.anim_time = 0

        self.gradient_frame = CTkFrame(self, fg_color="transparent")
        self.gradient_frame.pack(fill="both", expand=True)

        self.create_gradient_background()

        # Sidebar (left)
        self.sidebar = CTkFrame(self.gradient_frame, width=280, height=900,
                                corner_radius=20, fg_color=THEME_CARD,
                                border_width=1, border_color=THEME_PRIMARY)
        self.sidebar.place(x=40, y=40)

        # Main content container (Expanded to fill right side)
        self.container = CTkFrame(self.gradient_frame, fg_color="transparent")
        self.container.place(x=360, y=40, relwidth=0.75, relheight=0.92)

        self.setup_sidebar()
        self.setup_frames()
        self.show_frame("HomePage")

        # Start water reminder check
        self.check_water_reminder()
        
        self.bind('<Configure>', self.on_resize)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # Removed create_water_widget method


    def add_water(self, amount):
        """Add water intake"""
        new_total = self.water_reminder.add_water(amount)
        self.update_water_display()
        
        # Show confirmation
        self.show_water_notification(f"Added {amount}ml! Total: {new_total}ml")
        
        # Speak feedback
        self.speak_water_feedback(f"Good job! You drank {amount} milliliters of water.")

    # Removed add_custom_water method since it relied on the widget


    def reset_water(self):
        """Reset today's water intake"""
        self.water_reminder.reset_daily_intake()
        self.update_water_display()
        self.show_water_notification("Water intake reset for today!")

    def toggle_reminders(self):
        """Toggle water reminders on/off"""
        self.water_reminder.reminder_active = self.reminder_var.get()
        status = "enabled" if self.water_reminder.reminder_active else "disabled"
        self.show_water_notification(f"Water reminders {status}")

    def update_water_display(self):
        """Update any water displays if needed"""
        # Right widget removed, but might update other components or just pass
        # If WaterTrackerPage is visible, it updates itself via bindings/calls
        if "WaterTrackerPage" in self.frames:
             try:
                 self.frames["WaterTrackerPage"].update_display()
             except: pass

    def check_water_reminder(self):
        """Check and show water reminder if needed"""
        # Check for daily reset
        self.water_reminder.check_time_for_reset()
        
        # Check if reminder is needed
        if self.water_reminder.should_remind():
            daily_goal, current_intake = self.water_reminder.get_user_data()
            remaining = daily_goal - current_intake
            
            if remaining > 0:
                message = f"💧 Time to hydrate! You need {remaining}ml more today."
                self.show_water_notification(message, is_reminder=True)
                
                # Speak reminder
                self.speak_water_feedback(f"Reminder: Time to drink water. You have {remaining} milliliters left to reach your daily goal.")
        
        # Update display
        self.update_water_display()
        
        # Schedule next check (every minute)
        self.after(60000, self.check_water_reminder)

    def show_water_notification(self, message, is_reminder=False):
        """Show a temporary notification"""
        # Create notification frame on the main window
        notification = CTkFrame(self, fg_color="#10b981" if not is_reminder else SECONDARY,
                               corner_radius=10, height=60, width=400, border_color="white", border_width=1)
        # Place it at bottom center
        notification.place(relx=0.5, rely=0.9, anchor="center")
        
        CTkLabel(notification, text=message, font=("Arial", 16),
                text_color="white", wraplength=380).pack(expand=True, fill="both", padx=10, pady=10)
        
        # Remove after 3 seconds
        self.after(3000, notification.destroy)

    def speak_water_feedback(self, text):
        """Speak water-related feedback"""
        # Use a separate thread for TTS to avoid blocking
        threading.Thread(target=self._speak_text, args=(text,), daemon=True).start()

    def _speak_text(self, text):
        """Thread-safe text-to-speech"""
        with tts_lock:
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
                engine.say(text)
                if engine._inLoop:
                    engine.endLoop()
                engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")

    # -- switch theme --------
    # -- switch theme --------
    def toggle_theme(self):
        if self.current_theme == "dark":
            set_appearance_mode("Light")
            self.current_theme = "light"
        else:
            set_appearance_mode("Dark")
            self.current_theme = "dark"
            
        # Update water widget colors if necessary
        self.update_water_widget_theme()

    def update_water_widget_theme(self):
        """Update water widget colors based on theme - Removed for now"""
        pass

    # Removed manual apply_light/dark_theme methods as they are now handled by tuples

    # ---- background -----------
    def create_gradient_background(self):
        self.canvas = Canvas(self.gradient_frame, highlightthickness=0, bd=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.animate_gradient()

    def animate_gradient(self):
        try:
            self.canvas.delete("gradient")
            self.anim_time += 0.1

            width = self.winfo_width()
            height = self.winfo_height()

            # Detect current mode for gradient colors
            is_light = (get_appearance_mode() == "Light")

            if width > 1 and height > 1:
                for i in range(0, width, 15):
                    # Base alpha calculation
                    alpha = (math.sin(i * 0.01 + self.anim_time) * 0.3 + 0.7)
                    
                    if is_light:
                         # Light Mode Gradient (Soft Purples/Blues)
                        r = int(200 + alpha * 55)
                        g = int(200 + alpha * 55)
                        b = int(240 + alpha * 15)
                    else:
                        # Dark Mode Gradient (Original Deep Blues)
                        r = int(10 + alpha * 20)
                        g = int(0 + alpha * 40)
                        b = int(40 + alpha * 80)
                        
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    self.canvas.create_line(i, 0, i, height, fill=color, width=20, tags="gradient")

            self.after(150, self.animate_gradient)
        except:
            self.after(150, self.animate_gradient)

    # ---- sidebar ---
    def setup_sidebar(self):
        header = CTkFrame(self.sidebar, fg_color="transparent")
        header.pack(fill="x", pady=(30, 20))

        CTkLabel(header, text="🏋️Be Fit", font=("Arial", 28, "bold"),
                    text_color=THEME_PRIMARY).pack(pady=10)

        CTkLabel(header, text="Virtual Trainer", font=("Arial", 14),
                    text_color="#9ca3af").pack()

        buttons = [
            ("🏠 Home", "HomePage"),
            ("⚡ Workout", "WorkoutPage"),
            ("📊 Stats", "StatsPage"),
            ("💧 Water Tracker", "WaterTrackerPage"),
            ("💪 Exercises", "ExercisesPage"),
            ("👤 User", "UserPage"),
            ("⚙️ Settings", "SettingsPage")
        ]

        for text, page in buttons:
            btn = CTkButton(self.sidebar, text=text, width=240, height=55,
                            corner_radius=15, fg_color=THEME_BG_TRANSPARENT,
                            hover_color=THEME_SECONDARY, text_color=THEME_TEXT,
                            font=("Arial", 16, "bold"),
                            command=lambda p=page: self.show_frame(p))
            btn.pack(pady=8, padx=20)

    # ---- pages -------
    def setup_frames(self):
        self.frames = {}
        for F in (HomePage, WorkoutPage, StatsPage, ExercisesPage, UserPage, SettingsPage, WaterTrackerPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_propagate(False)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

        if (page_name == "StatsPage" or page_name == "HomePage") and self.data_manager:
            try:
                sessions = self.data_manager.load_sessions()
                frame.update_stats(sessions)
            except Exception as e:
                print(f"Error updating stats for {page_name}: {e}")

        if page_name == "WorkoutPage":
            frame.start_camera()
        elif hasattr(self, 'current_page') and self.current_page == "WorkoutPage":
            self.frames["WorkoutPage"].stop_camera()

        self.current_page = page_name
        
        # Update water display when switching pages
        self.update_water_display()

    def on_resize(self, event):
        pass

    def on_closing(self):
        workout_page = self.frames.get("WorkoutPage")
        if workout_page and hasattr(workout_page, 'cap'):
            workout_page.stop_camera()
        cv2.destroyAllWindows()
        self.destroy()

# ---- home page -----
class HomePage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME_BG_TRANSPARENT)
        self.controller = controller

        hero = CTkFrame(self, fg_color=THEME_CARD, corner_radius=25,
                        border_width=1, border_color=THEME_PRIMARY)
        hero.pack(padx=30, pady=(80, 20))

        CTkLabel(hero, text="Welcome Back Champion! 💪", font=("Arial", 48, "bold"),
                    text_color=THEME_PRIMARY).pack(pady=40, padx=40)

        CTkLabel(hero, text="Ready to crush your goals today?", font=("Arial", 24),
                    text_color=THEME_TEXT).pack(pady=(0, 30))

        btn_frame = CTkFrame(hero, fg_color="transparent")
        btn_frame.pack()

        CTkButton(btn_frame, text="🚀 Start Workout", width=220, height=65,
                    font=("Arial", 20, "bold"), fg_color=THEME_SECONDARY, hover_color="#278495",
                    text_color="white", corner_radius=15,
                    command=lambda: controller.show_frame("WorkoutPage")).pack(side="left", padx=20)

        CTkButton(btn_frame, text="📈 View Progress", width=220, height=65,
                    font=("Arial", 20, "bold"), fg_color=THEME_PRIMARY, hover_color="#06b6d4",
                    text_color="black", corner_radius=15,
                    command=lambda: controller.show_frame("StatsPage")).pack(side="left", padx=20)

        self.create_stats_cards()

    def create_stats_cards(self):
        # Container for cards
        self.cards_frame = CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=60, pady=60)
        self.cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Initial Placeholder
        self.update_stats([])

    def update_stats(self, sessions):
        # 1. Clear existing
        for child in self.cards_frame.winfo_children():
            child.destroy()
            
        # 2. Calculate Stats
        total_workouts = len(sessions)
        total_reps = 0
        
        for s in sessions:
            try:
                total_reps += int(float(s.get("reps", 0)))
            except: pass
            
        # Placeholder for streak
        best_streak = "N/A"

        # 3. Create Data
        stats_data = [
            {"title": "Total Workouts", "value": str(total_workouts), "color": PRIMARY},
            {"title": "Total Reps", "value": f"{total_reps:,}", "color": SECONDARY},
            {"title": "Best Streak", "value": best_streak, "color": "#00d4ff"}
        ]

        # 4. Populate GUI
        for i, data in enumerate(stats_data):
            card = CTkFrame(self.cards_frame, fg_color=THEME_CARD,
                            corner_radius=20, border_width=1, border_color=data["color"])
            card.grid(row=0, column=i, padx=20, pady=20, sticky="ew")

            CTkLabel(card, text=data["value"], font=("Arial", 36, "bold"),
                        text_color=data["color"]).pack(pady=20)
            CTkLabel(card, text=data["title"], font=("Arial", 16),
                        text_color=THEME_TEXT).pack()

# ---- workout page ----------------------
class WorkoutPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME_BG_TRANSPARENT)
        self.controller = controller
        self.reps = 0
        self.target_reps = 15
        self.reps = 0
        self.target_reps = 15
        self.cap = None
        self.start_time = None
        
        # TTS Control
        self.last_speech_time = time.time()
        self.speech_cooldown = 3.0
        self.last_spoken_feedback = ""
        self.speech_counter = 0

        self.create_controls_overlay()

    def create_controls_overlay(self):
    # -------- Overlay Frame --------
        overlay = CTkFrame(self, fg_color=THEME_CARD, corner_radius=25,
                            border_width=1,width=1000, border_color=THEME_SECONDARY, height=225)
        overlay.pack( padx=25, pady=20)
        overlay.pack_propagate(False)  # keep fixed height

        # -------- Exercise Selection --------
        exercise_frame = CTkFrame(overlay, fg_color="transparent")
        exercise_frame.pack(pady=10)

        CTkLabel(exercise_frame, text="Exercise:", font=("Arial", 16),
                    text_color=THEME_TEXT).pack(side="left", padx=(0, 10))

        self.exercise_var = StringVar(value="pushup")
        CTkOptionMenu(exercise_frame, values=["pushup", "squat", "bicep_curl", "general"],
                        variable=self.exercise_var, width=150,height=25).pack(side="left")

        # -------- Timer Label --------
        self.timer_label = CTkLabel(overlay, text="Time: 00:00", font=("Arial", 16),
                                    text_color=THEME_PRIMARY)
        self.timer_label.pack(pady=0)

        # -------- Reps Label --------
        self.reps_label = CTkLabel(overlay, text=f"Reps: 0/15",
                                    font=("Arial", 16, "bold"), text_color=THEME_PRIMARY)
        self.reps_label.pack(pady=0)

        # -------- Feedback Label --------
        self.feedback_var = StringVar(value="Standby: Ready to start...")
        self.feedback_label = CTkLabel(overlay, textvariable=self.feedback_var,
                                    font=("Arial", 16, "bold"), text_color="#ffcc00", wraplength=800,width=800)
        self.feedback_label.pack(pady=0)

        # -------- Progress Bar --------
        progress_frame = CTkFrame(overlay, fg_color=THEME_CARD, corner_radius=12, height=20)
        progress_frame.pack(fill="x", padx=40, pady=5)
        progress_frame.grid_propagate(False)

        self.progress_bar = CTkProgressBar(progress_frame, height=10, corner_radius=10,
                                            progress_color=THEME_PRIMARY, fg_color=THEME_CARD)
        self.progress_bar.pack(fill="x", padx=12, pady=2.5)
        self.progress_bar.set(0)

        # -------- Buttons --------
        btn_frame = CTkFrame(overlay, fg_color="transparent")
        btn_frame.pack(pady=10)

        CTkButton(btn_frame, text="▶ Start Timer", width=180, height=40,
                    font=("Arial", 16, "bold"), fg_color=THEME_PRIMARY, hover_color="#06b6d4",
                    text_color="black", corner_radius=18).pack(side="left", padx=10)

        CTkButton(btn_frame, text="💾 Save", width=140, height=40,
                    font=("Arial", 16, "bold"), fg_color="#10b981", hover_color="#059669",
                    text_color="white", corner_radius=18).pack(side="left", padx=10)

        CTkButton(btn_frame, text="✅ Rep Complete", width=200, height=40,
                    font=("Arial", 16, "bold"), fg_color=THEME_SECONDARY, hover_color="#166929",
                    text_color="white", corner_radius=18).pack(side="left", padx=10)

        CTkButton(btn_frame, text="🔄 Reset", width=140, height=40,
                    font=("Arial", 16, "bold"), fg_color="#64748b", hover_color="#475569",
                    text_color="white", corner_radius=18).pack(side="left", padx=10)

        CTkButton(btn_frame, text="🏠 Home", width=140, height=40,
                    font=("Arial", 16, "bold"), fg_color="#ef4444", hover_color="#dc2626",
                    text_color="white", corner_radius=18,
                    command=lambda: self.controller.show_frame("HomePage")).pack(side="left", padx=10)

    def start_camera(self):
        self.start_time = datetime.now()
        self.last_speech_time = time.time()
        self.last_spoken_feedback = ""

    def stop_camera(self):
        self.start_time = None

    def update_gui_labels(self, reps, posture_score, feedback, text_color):
        self.reps_label.configure(text=f"Reps: {reps}/{self.target_reps}")
        self.progress_bar.set(min(reps/self.target_reps, 1.0))

        # Update Feedback
        self.feedback_var.set(feedback)
        self.feedback_label.configure(text_color=text_color)

    # ====================================================================
    # TTS IMPLEMENTATION (Voice Feedback)
    # ====================================================================
    
    def speak_feedback(self, text: str, priority: str = "low"):
        """
        Calls TTS API in a separate thread, with cooldown logic.
        """
        current_time = time.time()

        # Voice Cooldown/Throttling
        if priority == "low" and (current_time - self.last_speech_time) < self.speech_cooldown:
            return
        
        # Avoid repeating the same error too quickly
        if self.last_spoken_feedback == text and priority == "low":
            return
        
        self.last_speech_time = current_time
        self.last_spoken_feedback = text
        
        # Increment counter to invalidate previous pending requests
        self.speech_counter += 1
        current_speech_id = self.speech_counter

        # Start TTS in a separate thread
        tts_thread = threading.Thread(target=self._run_tts_api, args=(text, current_speech_id), daemon=True)
        tts_thread.start()

    def _run_tts_api(self, text, speech_id):
        """
        Executes sound alerts based on feedback type. Replaces TTS.
        """
        # Acquire lock to ensure only one thread uses the engine at a time
        with tts_lock:
            # Check if this request is stale (a newer one has come in)
            if speech_id < self.speech_counter:
                return

            try:
                # Initialize TTS engine
                engine = pyttsx3.init()
            
                # Optional: Configure voice properties (speed, volume)
                engine.setProperty('rate', 150)  # Speed of speech
                
                # Visual indicator flash
                self.after(0, lambda: self.feedback_label.configure(text_color="#ff00ff"))
                
                # Speak the text
                engine.say(text)
                if engine._inLoop:
                     engine.endLoop()
                engine.runAndWait()
                
                # Snooze/Sleep for 1 second as requested
                time.sleep(1.0)
                
                self.after(0, lambda: self.feedback_label.configure(text_color="#ffcc00"))
                
            except Exception as e:
                print(f"Sound error: {e}")

# --- stats page---------
class StatsPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME_BG_TRANSPARENT)

        CTkLabel(self, text="📊 Your Progress", font=("Arial", 48, "bold"),
                    text_color=THEME_PRIMARY).pack(pady=80)

        # Container for stats
        self.table_frame = CTkScrollableFrame(self, fg_color=THEME_CARD,
                                            corner_radius=20, width=1000, height=150)
        self.table_frame.pack(fill="both", padx=80, pady=20)

        # Initial Placeholder
        self.update_stats([])

        CTkButton(self, text="🏠 Back to Home", width=250, height=70,
                    font=("Arial", 20, "bold"), fg_color="#ef4444", hover_color="#dc2626",
                    text_color="white", corner_radius=20,
                    command=lambda: controller.show_frame("HomePage")).pack(pady=40)

    def update_stats(self, sessions):
        # 1. Clear existing
        for child in self.table_frame.winfo_children():
            child.destroy()
            
        # 2. Calculate Stats
        total_workouts = len(sessions)
        total_reps = 0
        
        for s in sessions:
            try:
                total_reps += int(float(s.get("reps", 0)))
            except: pass
            
        # Placeholder for streak
        best_streak = "N/A"

        # 3. Create Data
        stats_data = [
            {"title": "Total Workouts", "value": str(total_workouts), "color": THEME_PRIMARY},
            {"title": "Total Reps", "value": f"{total_reps:,}", "color": THEME_SECONDARY},
            {"title": "Best Streak", "value": best_streak, "color": "#00d4ff"}
        ]

        # 4. Populate GUI
        item_width = 280
        
        # Grid configuration
        self.table_frame.grid_columnconfigure((0, 1, 2), weight=1)

        for i, data in enumerate(stats_data):
            card = CTkFrame(self.table_frame, fg_color=THEME_CARD,
                            corner_radius=20, border_width=1, border_color=data["color"])
            card.grid(row=0, column=i, padx=10, pady=10, sticky="ew")

            CTkLabel(card, text=data["value"], font=("Arial", 36, "bold"),
                        text_color=data["color"]).pack(pady=(20, 5))
            CTkLabel(card, text=data["title"], font=("Arial", 16),
                        text_color=THEME_TEXT).pack(pady=(0, 20))

# ---- water tracker page ----
class WaterTrackerPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME_BG_TRANSPARENT)
        self.controller = controller
        
        # Center the main card
        self.card = CTkFrame(self, fg_color=THEME_CARD, corner_radius=25,
                             border_width=1, border_color=THEME_SECONDARY, width=400)
        self.card.place(relx=0.5, rely=0.05, anchor="n")
        
        self.setup_ui()
        
        # Update on show
        self.bind("<Visibility>", lambda e: self.update_display())

    def setup_ui(self):
        # 1. Header
        CTkLabel(self.card, text="Water Tracker", font=("Arial", 28, "bold"),
                text_color=THEME_PRIMARY).pack(pady=(15, 10))

        # 2. Progress Circle
        self.progress_container = CTkFrame(self.card, width=220, height=220,
                                         fg_color=THEME_CARD, corner_radius=110,
                                         border_width=4, border_color=THEME_PRIMARY)
        self.progress_container.pack(pady=5)
        self.progress_container.pack_propagate(False)
        
        self.amount_label = CTkLabel(self.progress_container, text="0 / 3000 ml",
                                    font=("Arial", 20, "bold"), text_color=THEME_TEXT)
        self.amount_label.place(relx=0.5, rely=0.4, anchor="center")
        
        self.percent_label = CTkLabel(self.progress_container, text="0%",
                                     font=("Arial", 32, "bold"), text_color=THEME_PRIMARY)
        self.percent_label.place(relx=0.5, rely=0.6, anchor="center")

        # 3. Quick Add Section
        CTkLabel(self.card, text="Quick Add:", font=("Arial", 16),
                text_color=THEME_TEXT).pack(pady=(10, 5))
        
        quick_btns = CTkFrame(self.card, fg_color="transparent")
        quick_btns.pack()
        
        for amount in [250, 500, 750]:
            CTkButton(quick_btns, text=f"+{amount}ml", width=90, height=40,
                     font=("Arial", 14, "bold"), fg_color=SECONDARY,
                     hover_color="#278495", corner_radius=10,
                     command=lambda a=amount: self.add_water(a)).pack(side="left", padx=5)

        # 4. Custom Add Section
        custom_row = CTkFrame(self.card, fg_color="transparent")
        custom_row.pack(pady=8)
        
        self.custom_entry = CTkEntry(custom_row, width=100, height=35,
                                    font=("Arial", 14), placeholder_text="ml")
        self.custom_entry.pack(side="left", padx=(0, 10))
        
        CTkButton(custom_row, text="Add", width=70, height=35,
                 font=("Arial", 14, "bold"), fg_color=PRIMARY,
                 text_color="black", hover_color="#06b6d4",
                 command=self.add_custom).pack(side="left")

        # 5. Reset Button
        CTkButton(self.card, text="🔄 Reset Today", width=250, height=45,
                 font=("Arial", 14, "bold"), fg_color="#64748b",
                 hover_color="#475569", text_color="white", corner_radius=15,
                 command=self.reset_day).pack(pady=5)
                 
        # 6. Reminders Toggle
        self.reminder_var = BooleanVar(value=True) # Should sync with controller logic ideally
        # Trying to sync with existing logic if possible, or just default true
        if hasattr(self.controller.water_reminder, 'reminder_active'):
             self.reminder_var.set(self.controller.water_reminder.reminder_active)
             
        CTkCheckBox(self.card, text="Enable Reminders", variable=self.reminder_var,
                   font=("Arial", 14), text_color=THEME_TEXT,
                   command=self.toggle_reminders).pack(pady=5)

        # 7. Last Drink Label
        self.last_drink_label = CTkLabel(self.card, text="Last drink: Never",
                                        font=("Arial", 12), text_color="#94a3b8")
        self.last_drink_label.pack(pady=(0, 15))

    def toggle_reminders(self):
        # Update controller logic
        self.controller.water_reminder.reminder_active = self.reminder_var.get()
        status = "enabled" if self.reminder_var.get() else "disabled"
        self.controller.show_water_notification(f"Water reminders {status}")

    def update_display(self):
        try:
           daily_goal, current_intake = self.controller.water_reminder.get_user_data()
           
           # Update labels
           self.amount_label.configure(text=f"{current_intake} / {daily_goal} ml")
           
           if daily_goal > 0:
               percent = (current_intake / daily_goal) * 100
               self.percent_label.configure(text=f"{int(percent)}%")
               
               # Color logic
               if percent >= 100:
                   self.progress_container.configure(border_color="#10b981") # Green
                   self.percent_label.configure(text_color="#10b981")
               elif percent >= 75:
                   self.progress_container.configure(border_color="#f59e0b") # Orange
                   self.percent_label.configure(text_color="#f59e0b")
               else:
                   self.progress_container.configure(border_color=PRIMARY)
                   self.percent_label.configure(text_color=PRIMARY)
           
           # Update Last Drink Time
           try:
                user_file = self.controller.water_reminder.user_file
                if os.path.exists(user_file):
                    with open(user_file, 'r') as f:
                        data = json.load(f)
                        last_time = data.get('lastDrinkTime', 'Never')
                        if last_time != 'Never':
                            try:
                                last_dt = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
                                last_time = last_dt.strftime("%I:%M %p")
                            except: pass
                        self.last_drink_label.configure(text=f"Last drink: {last_time}")
           except: pass
                   
        except Exception as e:
            print(f"Error updating water page: {e}")

    def add_water(self, amount):
        self.controller.add_water(amount) 
        self.update_display()

    def add_custom(self):
        try:
            val = int(self.custom_entry.get())
            if val > 0:
                self.add_water(val)
                self.custom_entry.delete(0, 'end')
        except:
            pass

    def reset_day(self):
        self.controller.reset_water() 
        self.update_display()

        # 2. Calculate Stats
        total_workouts = len(sessions)
        total_reps = 0
        total_duration = 0.0
        
        for s in sessions:
            try:
                total_reps += int(float(s.get("reps", 0)))
                total_duration += float(s.get("duration", 0))
            except: pass
            
        total_cals = int((total_reps * 0.5) + (total_duration * 0.1))
        
        avg_session_min = 0
        if total_workouts > 0:
            avg_session_min = int((total_duration / total_workouts) // 60)

        # 3. Create Data Rows
        stats_data = [
            ["Total Workouts", str(total_workouts), "Lifetime"],
            ["Total Reps", f"{total_reps:,}", "Lifetime"],
            ["Calories Burned", f"{total_cals:,}", "Est."],
            ["Avg Session", f"{avg_session_min} min", "Per Workout"]
        ]

        # 4. Populate GUI
        for i, row in enumerate(stats_data):
            row_frame = CTkFrame(self.table_frame, fg_color="transparent")
            row_frame.grid(row=i, column=0, sticky="ew", padx=20, pady=15)

            CTkLabel(row_frame, text=row[0], font=("Arial", 20),
                        text_color=TEXT_LIGHT, width=300, anchor="w").pack(side="left", padx=(0, 40))
            CTkLabel(row_frame, text=row[1], font=("Arial", 28, "bold"),
                        text_color=PRIMARY, width=200).pack(side="left", padx=(0, 20))
            CTkLabel(row_frame, text=row[2], font=("Arial", 16),
                        text_color=SECONDARY).pack(side="right")

# --- exercises page ------
class ExercisesPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME_BG_TRANSPARENT)

        CTkLabel(self, text="💪 Exercise Library", font=("Arial", 48, "bold"),
                    text_color=THEME_PRIMARY).pack(pady=80)

        exercises = [
            ("squat", "🦵 Lower Body", THEME_PRIMARY, "Targets quads, hamstrings"),
            ("pushup", "💪 Chest", THEME_SECONDARY, "Targets chest, shoulders, triceps"),
            ("bicep_curl", "💪 Arms", "#00d4ff", "Targets biceps"),
            ("general", "✨ General", "#c084fc", "Freestyle workout tracking")
        ]

        grid_frame = CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=60, pady=40)
        grid_frame.grid_columnconfigure((0, 1, 2), weight=1)

        for i, (name, type_, color, desc) in enumerate(exercises):
            row = i // 3
            col = i % 3

            card = CTkFrame(grid_frame, fg_color=THEME_CARD,
                            corner_radius=20, border_width=2, border_color=color)
            card.grid(row=row, column=col, padx=20, pady=20, sticky="nsew")

            CTkLabel(card, text=name, font=("Arial", 28, "bold"), text_color=color).pack(pady=(20, 5))
            CTkLabel(card, text=type_, font=("Arial", 16), text_color="#94a3b8").pack(pady=(0, 10))
            CTkLabel(card, text=desc, font=("Arial", 12), text_color=THEME_TEXT,
                        wraplength=200).pack(pady=(0, 20))

            CTkButton(card, text="Select", width=120, height=35,
                        font=("Arial", 14), fg_color=color, hover_color=color,
                        text_color="white", corner_radius=10).pack(pady=(0, 20))

        CTkButton(self, text="🏠 Back to Home", width=250, height=70,
                    font=("Arial", 20, "bold"), fg_color="#ef4444", hover_color="#dc2626",
                    text_color="white", corner_radius=20,
                    command=lambda: controller.show_frame("HomePage")).pack(pady=40)

# --- user page ------
class UserPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME_BG_TRANSPARENT)
        self.controller = controller
        self.user_file = "storage/user.json"

        CTkLabel(self, text="👤 User Profile", font=("Arial", 48, "bold"),
                    text_color=THEME_PRIMARY).pack(pady=60)

        # Form Container
        self.form_frame = CTkFrame(self, fg_color=THEME_CARD, corner_radius=25)
        self.form_frame.pack(fill="y", padx=100, pady=20)

        # --- Fields ---
        self.entries = {}
        fields = [
            ("Full Name", "name"),
            ("Age", "age"),
            ("Weight (kg)", "weight"),
            ("Gender", "gender"),
            ("Daily Water (ml)", "dailyWaterNeeds"),
            ("Daily Calories (kcal)", "dailyCalorieNeeds")
        ]

        for i, (label_text, key) in enumerate(fields):
            row_frame = CTkFrame(self.form_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=40, pady=10)
            
            CTkLabel(row_frame, text=label_text, font=("Arial", 16),
                        text_color=THEME_TEXT, width=150, anchor="w").pack(side="left")
            
            entry = CTkEntry(row_frame, width=250, height=40, font=("Arial", 16))
            entry.pack(side="left", padx=20)
            self.entries[key] = entry

        # Load Data
        self.load_user_data()

        # Buttons
        btn_frame = CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=40)

        CTkButton(btn_frame, text="💾 Save Profile", width=200, height=60,
                    font=("Arial", 18, "bold"), fg_color=THEME_PRIMARY, hover_color="#06b6d4",
                    text_color="black", corner_radius=15,
                    command=self.save_user_data).pack(side="left", padx=20)

        CTkButton(btn_frame, text="🏠 Back to Home", width=200, height=60,
                    font=("Arial", 18, "bold"), fg_color="#ef4444", hover_color="#dc2626",
                    text_color="white", corner_radius=15,
                    command=lambda: controller.show_frame("HomePage")).pack(side="left", padx=20)

    def load_user_data(self):
        import json
        if os.path.exists(self.user_file):
            try:
                with open(self.user_file, 'r') as f:
                    data = json.load(f)
                    for key, entry in self.entries.items():
                        if key in data:
                            entry.delete(0, "end")
                            entry.insert(0, str(data[key]))
            except Exception as e:
                print(f"Error loading user profile: {e}")

    def save_user_data(self):
        import json

        # Load existing to preserve other fields like waterDrunk
        current_data = {}
        if os.path.exists(self.user_file):
             try:
                with open(self.user_file, 'r') as f:
                    current_data = json.load(f)
             except: pass
        
        # Update inputs
        try:
            for key, entry in self.entries.items():
                val = entry.get()
                # Basic type conversion
                if key in ["age", "dailyWaterNeeds", "dailyCalorieNeeds"]:
                   current_data[key] = int(val)
                elif key == "weight":
                   current_data[key] = float(val)
                else:
                   current_data[key] = val
            
            with open(self.user_file, 'w') as f:
                json.dump(current_data, f, indent=4)
            print("User profile saved.")
        except Exception as e:
            print(f"Error saving user profile: {e}")

# --- settings page --
class SettingsPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME_BG_TRANSPARENT)

        CTkLabel(self, text="⚙️ Settings", font=("Arial", 48, "bold"),
                    text_color=THEME_PRIMARY).pack(pady=80)

        settings_frame = CTkFrame(self, fg_color=THEME_CARD, corner_radius=25)
        settings_frame.pack(fill="x", padx=100, pady=40)

        CTkLabel(settings_frame, text="Appearance", font=("Arial", 24, "bold"),
                    text_color=THEME_TEXT).pack(pady=(40, 10))

        # theme toggle button
        self.theme_btn = CTkButton(settings_frame, text="🌙 Dark Mode", width=300, height=60,
                                    font=("Arial", 18), fg_color=THEME_CARD, text_color="black", hover_color=THEME_SECONDARY,
                                    command=controller.toggle_theme)
        self.theme_btn.pack(pady=10)

        CTkButton(settings_frame, text="🏠 Back to Home", width=250, height=60,
                    font=("Arial", 18, "bold"), fg_color="#ef4444", hover_color="#dc2626",
                    command=lambda: controller.show_frame("HomePage")).pack(pady=50)

# --- run app ---
if __name__ == "__main__":
    # Create storage directory if it doesn't exist
    os.makedirs("storage", exist_ok=True)
    
    # Initialize user.json with default values if it doesn't exist
    user_file = "storage/user.json"
    if not os.path.exists(user_file):
        default_user = {
            "name": "User",
            "age": 25,
            "weight": 70,
            "gender": "Not specified",
            "dailyWaterNeeds": 3000,
            "dailyCalorieNeeds": 2500,
            "waterDrunk": 0,
            "lastDrinkTime": "Never",
            "lastResetDate": datetime.now().strftime("%Y-%m-%d")
        }
        with open(user_file, 'w') as f:
            json.dump(default_user, f, indent=4)
    
    app = VirtualTrainerApp()
    app.mainloop()
