import cv2
from customtkinter import *
from tkinter import Canvas
import tkinter as tk
import math
import numpy as np

# ---- dark theme ------------------
set_appearance_mode("Dark")
set_default_color_theme("dark-blue")

PRIMARY = "#00eaff"    
SECONDARY = "#278495"  
BG_DARK = "#121427"
BG_DEEP = "#1a1b2e"
TEXT_LIGHT = "#e2e8f0"
BORDER = "#2dd4bf"

# ------ light colors ----
LIGHT_BG = "#f7f9fc"
LIGHT_CARD = "#ffffff"
LIGHT_TEXT = "#1e293b"
LIGHT_BORDER = "#cbd5e1"
LIGHT_PRIMARY = "#0ea5e9"
LIGHT_SECONDARY = "#6366f1"

class VirtualTrainerApp(CTk):
    def __init__(self):
        super().__init__()
        self.title("🏋️ Virtual Fitness Trainer")
        self.geometry("1920x1080")
        self.resizable(True, True)

        # crack current theme
        self.current_theme = "dark"

        self.anim_time = 0

        self.gradient_frame = CTkFrame(self, fg_color="transparent")
        self.gradient_frame.pack(fill="both", expand=True)

        self.create_gradient_background()

        self.sidebar = CTkFrame(self.gradient_frame, width=280, height=900,
                                corner_radius=20, fg_color=BG_DEEP,
                                border_width=1, border_color=PRIMARY)
        self.sidebar.place(x=40, y=40)

        self.container = CTkFrame(self.gradient_frame, fg_color="transparent")
        self.container.place(x=360, y=40, relwidth=1, relheight=1)

        self.setup_sidebar()
        self.setup_frames()
        self.show_frame("HomePage")

        self.bind('<Configure>', self.on_resize)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # -- switch theme --------
    def toggle_theme(self):
        if self.current_theme == "dark":
            self.apply_light_theme()
            self.current_theme = "light"
        else:
            self.apply_dark_theme()
            self.current_theme = "dark"

    def apply_light_theme(self):
        set_appearance_mode("Light")
        self.sidebar.configure(fg_color=LIGHT_CARD, border_color=LIGHT_PRIMARY)

    def apply_dark_theme(self):
        set_appearance_mode("Dark")
        self.sidebar.configure(fg_color=BG_DEEP, border_color=PRIMARY)

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

            if width > 1 and height > 1:
                for i in range(0, width, 15):
                    alpha = (math.sin(i * 0.01 + self.anim_time) * 0.3 + 0.7)
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

        CTkLabel(header, text="🏋️‍♂️ Be Fit", font=("Arial", 28, "bold"),
                    text_color=PRIMARY).pack(pady=10)

        CTkLabel(header, text="Virtual Trainer", font=("Arial", 14),
                    text_color="#9ca3af").pack()

        buttons = [
            ("🏠 Home", "HomePage"),
            ("⚡ Workout", "WorkoutPage"),
            ("📊 Stats", "StatsPage"),
            ("💪 Exercises", "ExercisesPage"),
            ("⚙️ Settings", "SettingsPage")
        ]

        for text, page in buttons:
            btn = CTkButton(self.sidebar, text=text, width=240, height=55,
                            corner_radius=15, fg_color=BG_DARK,
                            hover_color=SECONDARY, text_color=TEXT_LIGHT,
                            font=("Arial", 16, "bold"),
                            command=lambda p=page: self.show_frame(p))
            btn.pack(pady=8, padx=20)

    # ---- pages -------
    def setup_frames(self):
        self.frames = {}
        for F in (HomePage, WorkoutPage, StatsPage, ExercisesPage, SettingsPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_propagate(False)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

        if page_name == "WorkoutPage":
            frame.start_camera()
        elif hasattr(self, 'current_page') and self.current_page == "WorkoutPage":
            self.frames["WorkoutPage"].stop_camera()

        self.current_page = page_name

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
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        hero = CTkFrame(self, fg_color=BG_DEEP, corner_radius=25,
                        border_width=1, border_color=PRIMARY)
        hero.pack(fill="x", padx=60, pady=(80, 40))

        CTkLabel(hero, text="Welcome Back Champion! 💪", font=("Arial", 48, "bold"),
                    text_color=PRIMARY).pack(pady=40)

        CTkLabel(hero, text="Ready to crush your goals today?", font=("Arial", 24),
                    text_color=TEXT_LIGHT).pack(pady=(0, 30))

        btn_frame = CTkFrame(hero, fg_color="transparent")
        btn_frame.pack()

        CTkButton(btn_frame, text="🚀 Start Workout", width=220, height=65,
                    font=("Arial", 20, "bold"), fg_color=SECONDARY, hover_color="#278495",
                    text_color="white", corner_radius=15,
                    command=lambda: controller.show_frame("WorkoutPage")).pack(side="left", padx=20)

        CTkButton(btn_frame, text="📈 View Progress", width=220, height=65,
                    font=("Arial", 20, "bold"), fg_color=PRIMARY, hover_color="#06b6d4",
                    text_color="black", corner_radius=15,
                    command=lambda: controller.show_frame("StatsPage")).pack(side="left", padx=20)

        self.create_stats_cards()

    def create_stats_cards(self):
        stats_data = [
            {"title": "Total Workouts", "value": "12", "color": PRIMARY},
            {"title": "Total Reps", "value": "1,247", "color": SECONDARY},
            {"title": "Best Streak", "value": "7 days", "color": "#00d4ff"}
        ]

        cards_frame = CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=60, pady=60)
        cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        for i, data in enumerate(stats_data):
            card = CTkFrame(cards_frame, fg_color=BG_DARK,
                            corner_radius=20, border_width=1, border_color=data["color"])
            card.grid(row=0, column=i, padx=20, pady=20, sticky="ew")

            CTkLabel(card, text=data["value"], font=("Arial", 36, "bold"),
                        text_color=data["color"]).pack(pady=20)
            CTkLabel(card, text=data["title"], font=("Arial", 16),
                        text_color=TEXT_LIGHT).pack()


# ---- workout page ----------------------
class WorkoutPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.reps = 0
        self.target_reps = 15
        self.cap = None

        self.create_controls_overlay()

    def create_controls_overlay(self):
        overlay = CTkFrame(self, fg_color=BG_DEEP, corner_radius=25,
                            border_width=1, border_color=SECONDARY)
        overlay.pack(fill="x", padx=60, pady=(0, 40))

        exercise_frame = CTkFrame(overlay, fg_color="transparent")
        exercise_frame.pack(pady=10)

        CTkLabel(exercise_frame, text="Exercise:", font=("Arial", 18),
                    text_color=TEXT_LIGHT).pack(side="left", padx=(0, 10))

        self.exercise_var = StringVar(value="Push-ups")
        CTkOptionMenu(exercise_frame, values=["Push-ups", "Squats", "Lunges", "Plank"],
                        variable=self.exercise_var).pack(side="left")

        self.timer_label = CTkLabel(overlay, text="Time: 00:00", font=("Arial", 20),
                                    text_color=PRIMARY)
        self.timer_label.pack(pady=5)

        self.reps_label = CTkLabel(overlay, text=f"Reps: 0/15",
                                    font=("Arial", 48, "bold"), text_color=PRIMARY)
        self.reps_label.pack(pady=30)

        progress_frame = CTkFrame(overlay, fg_color=BG_DARK, corner_radius=12, height=25)
        progress_frame.pack(fill="x", padx=60, pady=10)
        progress_frame.grid_propagate(False)

        self.progress_bar = CTkProgressBar(progress_frame, height=20, corner_radius=10,
                                            progress_color=PRIMARY, fg_color="#2d3748")
        self.progress_bar.pack(fill="x", padx=12, pady=2.5)
        self.progress_bar.set(0)

        btn_frame = CTkFrame(overlay, fg_color="transparent")
        btn_frame.pack(pady=20)

        CTkButton(btn_frame, text="▶ Start Timer", width=200, height=70,
                    font=("Arial", 18, "bold"), fg_color=PRIMARY, hover_color="#06b6d4",
                    text_color="black", corner_radius=20).pack(side="left", padx=15)

        CTkButton(btn_frame, text="✅ Rep Complete", width=220, height=70,
                    font=("Arial", 20, "bold"), fg_color=SECONDARY, hover_color="#166929",
                    text_color="white", corner_radius=20).pack(side="left", padx=15)

        CTkButton(btn_frame, text="🔄 Reset", width=150, height=70,
                    font=("Arial", 18, "bold"), fg_color="#64748b", hover_color="#475569",
                    text_color="white", corner_radius=20).pack(side="left", padx=15)

        CTkButton(btn_frame, text="🏠 Home", width=150, height=70,
                    font=("Arial", 18, "bold"), fg_color="#ef4444", hover_color="#dc2626",
                    text_color="white", corner_radius=20,
                    command=lambda: self.controller.show_frame("HomePage")).pack(side="left", padx=15)

    def start_camera(self):
        pass 

    def stop_camera(self):
        pass 
# --- stats page---------
class StatsPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")

        CTkLabel(self, text="📊 Your Progress", font=("Arial", 48, "bold"),
                    text_color=PRIMARY).pack(pady=80)

        stats_data = [
            ["Total Workouts", "28", "+12%"],
            ["Total Reps", "2,847", "+245"],
            ["Calories Burned", "15,240", "+3,200"],
            ["Best Streak", "12 days", "🔥 New Record!"],
            ["Avg Session", "28 min", "+5 min"]
        ]

        table_frame = CTkScrollableFrame(self, fg_color=BG_DEEP,
                                            corner_radius=20, width=1000, height=400)
        table_frame.pack(fill="both", expand=True, padx=80, pady=40)

        for i, row in enumerate(stats_data):
            row_frame = CTkFrame(table_frame, fg_color="transparent")
            row_frame.grid(row=i, column=0, sticky="ew", padx=20, pady=15)

            CTkLabel(row_frame, text=row[0], font=("Arial", 20),
                        text_color=TEXT_LIGHT, width=300, anchor="w").pack(side="left", padx=(0, 40))
            CTkLabel(row_frame, text=row[1], font=("Arial", 28, "bold"),
                        text_color=PRIMARY, width=200).pack(side="left", padx=(0, 20))
            CTkLabel(row_frame, text=row[2], font=("Arial", 16),
                        text_color=SECONDARY).pack(side="right")

        CTkButton(self, text="🏠 Back to Home", width=250, height=70,
                    font=("Arial", 20, "bold"), fg_color="#ef4444", hover_color="#dc2626",
                    text_color="white", corner_radius=20,
                    command=lambda: controller.show_frame("HomePage")).pack(pady=40)

# --- exercises page ------
class ExercisesPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")

        CTkLabel(self, text="💪 Exercise Library", font=("Arial", 48, "bold"),
                    text_color=PRIMARY).pack(pady=80)

        exercises = [
            ("Squat", "🦵 Lower Body", PRIMARY, "Targets quads, hamstrings"),
            ("Push-up", "💪 Chest", SECONDARY, "Targets chest, shoulders, triceps"),
            ("Deadlift", "💥 Full Body", "#00d4ff", "Targets back, legs, core"),
            ("Plank", "🧘 Core", "#c084fc", "Targets abs, back, shoulders"),
            ("Lunges", "🦵 Legs", "#818cf8", "Targets quads, hamstrings"),
            ("Pull-ups", "🤸 Back", "#ef4444", "Targets back, biceps, shoulders")
        ]

        grid_frame = CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=60, pady=40)
        grid_frame.grid_columnconfigure((0, 1, 2), weight=1)

        for i, (name, type_, color, desc) in enumerate(exercises):
            row = i // 3
            col = i % 3

            card = CTkFrame(grid_frame, fg_color=BG_DARK,
                            corner_radius=20, border_width=2, border_color=color)
            card.grid(row=row, column=col, padx=20, pady=20, sticky="nsew")

            CTkLabel(card, text=name, font=("Arial", 28, "bold"), text_color=color).pack(pady=(20, 5))
            CTkLabel(card, text=type_, font=("Arial", 16), text_color="#94a3b8").pack(pady=(0, 10))
            CTkLabel(card, text=desc, font=("Arial", 12), text_color=TEXT_LIGHT,
                        wraplength=200).pack(pady=(0, 20))

            CTkButton(card, text="Select", width=120, height=35,
                        font=("Arial", 14), fg_color=color, hover_color=color,
                        text_color="white", corner_radius=10).pack(pady=(0, 20))

        CTkButton(self, text="🏠 Back to Home", width=250, height=70,
                    font=("Arial", 20, "bold"), fg_color="#ef4444", hover_color="#dc2626",
                    text_color="white", corner_radius=20,
                    command=lambda: controller.show_frame("HomePage")).pack(pady=40)


# --- settings page --
class SettingsPage(CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")

        CTkLabel(self, text="⚙️ Settings", font=("Arial", 48, "bold"),
                    text_color=PRIMARY).pack(pady=80)

        settings_frame = CTkFrame(self, fg_color=BG_DEEP, corner_radius=25)
        settings_frame.pack(fill="x", padx=100, pady=40)

        CTkLabel(settings_frame, text="Appearance", font=("Arial", 24, "bold"),
                    text_color=TEXT_LIGHT).pack(pady=(40, 10))

        # theme toggle button
        self.theme_btn = CTkButton(settings_frame, text="🌙 Dark Mode", width=300, height=60,
                                    font=("Arial", 18), fg_color=BG_DARK, hover_color=SECONDARY,
                                    command=controller.toggle_theme)
        self.theme_btn.pack(pady=10)

        CTkButton(settings_frame, text="🏠 Back to Home", width=250, height=60,
                    font=("Arial", 18, "bold"), fg_color="#ef4444", hover_color="#dc2626",
                    command=lambda: controller.show_frame("HomePage")).pack(pady=50)

# --- run app ---
if __name__ == "__main__":
    app = VirtualTrainerApp()
    app.mainloop()