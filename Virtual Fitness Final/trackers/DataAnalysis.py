import pandas as pd
from datetime import datetime, timedelta


def load_workout_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


def filter_by_date(df: pd.DataFrame, date_str: str) -> pd.DataFrame:
    target_date = pd.to_datetime(date_str).date()
    return df[df['timestamp'].dt.date == target_date]


def filter_by_workout(df: pd.DataFrame, workout_type: str) -> pd.DataFrame:
    return df[df['workoutType'] == workout_type]


def filter_by_date_range(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
    return df[mask]


def human_friendly_time(df: pd.DataFrame) -> pd.DataFrame:
    def format_time(dt):
        now = datetime.now()
        if dt.date() == now.date():
            return dt.strftime("Today at %I:%M %p")
        elif dt.date() == (now.date() - timedelta(days=1)):
            return dt.strftime("Yesterday at %I:%M %p")
        else:
            return dt.strftime("%A, %d %B %Y %I:%M %p")
    
    df = df.copy()
    df['time_friendly'] = df['timestamp'].apply(format_time)
    return df


def testing():
    df = load_workout_csv("./storage/data.csv")
    
    df_today = filter_by_date(df, "2025-12-06")
    
    print("=" * 50)
    print(f"today: \n{df_today}")

    df_squat = filter_by_workout(df, "Squat")
    
    print("=" * 50)
    print(f"squats: \n{df_squat}")

    df_squat_today = filter_by_workout(df_today, "Squat")

    print("=" * 50)
    print(f"squats today: \n{df_squat_today}")
    
    df_squat_today = human_friendly_time(df_squat_today)

    print("=" * 50)
    print(f"human friendly squat today: \n{df_squat_today}")
    
    print("=" * 50)
    print(df_squat_today[['id','workoutType','time_friendly','reps','duration']])

testing()