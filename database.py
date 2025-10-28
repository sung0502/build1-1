import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json

DATABASE_NAME = "productivity.db"

def get_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            deadline TIMESTAMP,
            time_specific TEXT,
            completed BOOLEAN DEFAULT 0,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Habits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            frequency TEXT NOT NULL,
            by_time TEXT,
            minimum_requirement TEXT,
            priority TEXT,
            color TEXT,
            icon TEXT,
            grace_period INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1
        )
    """)

    # Habit logs table (for tracking completions and streaks)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
        )
    """)

    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

# ==================== TASK FUNCTIONS ====================

def add_task(title: str, category: str, priority: str, description: str = "",
             deadline: Optional[datetime] = None, time_specific: str = "") -> int:
    """Add a new task."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks (title, description, category, priority, deadline, time_specific)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, description, category, priority, deadline, time_specific))

    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_tasks(days_ahead: Optional[int] = None, completed: bool = False) -> List[Dict]:
    """Get tasks filtered by days ahead and completion status."""
    conn = get_connection()
    cursor = conn.cursor()

    if days_ahead is not None:
        end_date = datetime.now() + timedelta(days=days_ahead)
        cursor.execute("""
            SELECT * FROM tasks
            WHERE completed = ? AND (deadline IS NULL OR deadline <= ?)
            ORDER BY
                CASE priority
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Low' THEN 3
                END,
                deadline ASC
        """, (completed, end_date))
    else:
        cursor.execute("""
            SELECT * FROM tasks
            WHERE completed = ?
            ORDER BY
                CASE priority
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Low' THEN 3
                END,
                deadline ASC
        """, (completed,))

    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

def get_today_tasks() -> Tuple[List[Dict], List[Dict]]:
    """Get today's tasks separated into pending and completed."""
    conn = get_connection()
    cursor = conn.cursor()

    today_end = datetime.now().replace(hour=23, minute=59, second=59)

    # Pending tasks for today
    cursor.execute("""
        SELECT * FROM tasks
        WHERE completed = 0 AND (deadline IS NULL OR deadline <= ?)
        ORDER BY
            CASE priority
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 3
            END,
            deadline ASC
    """, (today_end,))
    pending = [dict(row) for row in cursor.fetchall()]

    # Completed tasks for today
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    cursor.execute("""
        SELECT * FROM tasks
        WHERE completed = 1 AND completed_at >= ?
        ORDER BY completed_at DESC
    """, (today_start,))
    completed = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return pending, completed

def complete_task(task_id: int):
    """Mark a task as completed."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET completed = 1, completed_at = ?
        WHERE id = ?
    """, (datetime.now(), task_id))

    conn.commit()
    conn.close()

def uncomplete_task(task_id: int):
    """Mark a task as not completed."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET completed = 0, completed_at = NULL
        WHERE id = ?
    """, (task_id,))

    conn.commit()
    conn.close()

def delete_task(task_id: int):
    """Delete a task."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    conn.commit()
    conn.close()

def update_task(task_id: int, title: str, category: str, priority: str,
                description: str = "", deadline: Optional[datetime] = None,
                time_specific: str = ""):
    """Update a task."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET title = ?, description = ?, category = ?, priority = ?,
            deadline = ?, time_specific = ?
        WHERE id = ?
    """, (title, description, category, priority, deadline, time_specific, task_id))

    conn.commit()
    conn.close()

def cleanup_old_completed_tasks():
    """Remove completed tasks that are older than today."""
    conn = get_connection()
    cursor = conn.cursor()

    today_start = datetime.now().replace(hour=0, minute=0, second=0)

    cursor.execute("""
        DELETE FROM tasks
        WHERE completed = 1 AND completed_at < ?
    """, (today_start,))

    conn.commit()
    conn.close()

# ==================== HABIT FUNCTIONS ====================

def add_habit(title: str, category: str, frequency: str, by_time: str = "",
              minimum_requirement: str = "", description: str = "",
              priority: str = "Medium", color: str = "", icon: str = "",
              grace_period: int = 0) -> int:
    """Add a new habit."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO habits (title, description, category, frequency, by_time,
                           minimum_requirement, priority, color, icon, grace_period)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, description, category, frequency, by_time, minimum_requirement,
          priority, color, icon, grace_period))

    habit_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return habit_id

def get_habits(category: Optional[str] = None, active_only: bool = True) -> List[Dict]:
    """Get all habits, optionally filtered by category."""
    conn = get_connection()
    cursor = conn.cursor()

    if category:
        cursor.execute("""
            SELECT * FROM habits
            WHERE category = ? AND active = ?
            ORDER BY
                CASE priority
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Low' THEN 3
                END
        """, (category, active_only))
    else:
        cursor.execute("""
            SELECT * FROM habits
            WHERE active = ?
            ORDER BY category,
                CASE priority
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Low' THEN 3
                END
        """, (active_only,))

    habits = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return habits

def log_habit_completion(habit_id: int, notes: str = ""):
    """Log a habit completion for today."""
    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    # Check if already logged today
    cursor.execute("""
        SELECT id FROM habit_logs
        WHERE habit_id = ? AND date = ?
    """, (habit_id, today))

    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO habit_logs (habit_id, date, notes)
            VALUES (?, ?, ?)
        """, (habit_id, today, notes))
        conn.commit()

    conn.close()

def remove_habit_completion(habit_id: int, date: Optional[str] = None):
    """Remove a habit completion log."""
    conn = get_connection()
    cursor = conn.cursor()

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        DELETE FROM habit_logs
        WHERE habit_id = ? AND date = ?
    """, (habit_id, date))

    conn.commit()
    conn.close()

def is_habit_completed_today(habit_id: int) -> bool:
    """Check if a habit was completed today."""
    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT id FROM habit_logs
        WHERE habit_id = ? AND date = ?
    """, (habit_id, today))

    result = cursor.fetchone() is not None
    conn.close()
    return result

def get_habit_streak(habit_id: int) -> Dict:
    """Calculate current streak and longest streak for a habit."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get habit details for grace period
    cursor.execute("SELECT grace_period, frequency FROM habits WHERE id = ?", (habit_id,))
    habit_row = cursor.fetchone()
    if not habit_row:
        conn.close()
        return {"current_streak": 0, "longest_streak": 0}

    grace_period = habit_row["grace_period"]
    frequency = habit_row["frequency"]

    # Get all completion logs
    cursor.execute("""
        SELECT date FROM habit_logs
        WHERE habit_id = ?
        ORDER BY date DESC
    """, (habit_id,))

    logs = [row["date"] for row in cursor.fetchall()]
    conn.close()

    if not logs:
        return {"current_streak": 0, "longest_streak": 0}

    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    temp_streak = 0

    # For daily habits
    if frequency == "Daily":
        today = datetime.now().date()
        expected_date = today

        # Check current streak
        for log_date_str in logs:
            log_date = datetime.strptime(log_date_str, "%Y-%m-%d").date()

            # Check if this log is within grace period of expected date
            days_diff = (expected_date - log_date).days

            if days_diff <= grace_period and days_diff >= 0:
                current_streak += 1
                expected_date = log_date - timedelta(days=1)
            else:
                break

        # Calculate longest streak
        if len(logs) > 0:
            temp_streak = 1
            longest_streak = 1

            for i in range(len(logs) - 1):
                current_date = datetime.strptime(logs[i], "%Y-%m-%d").date()
                next_date = datetime.strptime(logs[i + 1], "%Y-%m-%d").date()

                days_between = (current_date - next_date).days

                if days_between <= grace_period + 1:
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1

    # For weekly habits
    elif frequency == "Weekly":
        # Get the current week number
        today = datetime.now().date()
        current_week = today.isocalendar()[1]
        current_year = today.year

        # Group logs by week
        weeks_completed = set()
        for log_date_str in logs:
            log_date = datetime.strptime(log_date_str, "%Y-%m-%d").date()
            week_num = log_date.isocalendar()[1]
            year = log_date.year
            weeks_completed.add((year, week_num))

        # Check current streak (in weeks)
        expected_year = current_year
        expected_week = current_week

        for _ in range(len(weeks_completed)):
            if (expected_year, expected_week) in weeks_completed:
                current_streak += 1
                # Move to previous week
                expected_week -= 1
                if expected_week < 1:
                    expected_week = 52
                    expected_year -= 1
            else:
                # Check grace period (allow missing some weeks)
                grace_used = 0
                found = False
                while grace_used < grace_period:
                    expected_week -= 1
                    grace_used += 1
                    if expected_week < 1:
                        expected_week = 52
                        expected_year -= 1
                    if (expected_year, expected_week) in weeks_completed:
                        current_streak += 1
                        found = True
                        break

                if not found:
                    break

        # Calculate longest streak
        if weeks_completed:
            sorted_weeks = sorted(weeks_completed)
            temp_streak = 1
            longest_streak = 1

            for i in range(len(sorted_weeks) - 1):
                curr_year, curr_week = sorted_weeks[i]
                next_year, next_week = sorted_weeks[i + 1]

                # Calculate week difference
                if next_year == curr_year:
                    week_diff = next_week - curr_week
                else:
                    week_diff = (52 - curr_week) + next_week

                if week_diff <= grace_period + 1:
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak
    }

def delete_habit(habit_id: int):
    """Delete a habit and all its logs."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM habit_logs WHERE habit_id = ?", (habit_id,))
    cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))

    conn.commit()
    conn.close()

def update_habit(habit_id: int, title: str, category: str, frequency: str,
                 by_time: str = "", minimum_requirement: str = "",
                 description: str = "", priority: str = "Medium",
                 color: str = "", icon: str = "", grace_period: int = 0):
    """Update a habit."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE habits
        SET title = ?, description = ?, category = ?, frequency = ?,
            by_time = ?, minimum_requirement = ?, priority = ?,
            color = ?, icon = ?, grace_period = ?
        WHERE id = ?
    """, (title, description, category, frequency, by_time, minimum_requirement,
          priority, color, icon, grace_period, habit_id))

    conn.commit()
    conn.close()
