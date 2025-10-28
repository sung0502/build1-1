# Productivity Dashboard

A comprehensive productivity tracking application built with Streamlit and SQLite.

## Features

### Task Management
- **Today's To-Do**: View and manage tasks for today
- **Next 3 Days**: See upcoming tasks in the next 3 days
- **Next 7 Days**: Plan ahead with tasks for the next week
- **Priority Levels**: High, Medium, Low with color-coded indicators
- **Flexible Deadlines**: Add tasks with or without specific deadlines/times
- **Auto-Cleanup**: Completed tasks automatically disappear the next day
- **Visual Feedback**: Completed tasks shown with strikethrough until end of day

### Habit Tracking
- **Daily and Weekly Habits**: Track habits on different frequencies
- **Two Categories**:
  - Personal Habits (for self-care activities)
  - Responsibilities (for obligations)
- **Streak System**:
  - Current streak counter
  - Longest streak tracker
  - Grace period support (miss days without breaking streak)
- **Customization**:
  - Set "by this time" deadlines
  - Define minimum requirements (e.g., "3 push-ups")
  - Add custom icons and colors
  - Set priority levels

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the app:
```bash
streamlit run app.py
```

2. Open your browser to `http://localhost:8501`

## How to Use

### Adding Tasks
1. Click "Add New Task" at the bottom of the left panel
2. Fill in:
   - Task title (required)
   - Description (optional)
   - Category (Personal Habits or Responsibilities)
   - Priority (High/Medium/Low)
   - Deadline with optional specific time
3. Click "Add Task"

### Adding Habits
1. Click "Add New Habit" at the bottom of the right panel
2. Fill in:
   - Habit title (required)
   - Description (optional)
   - Category (Personal Habits or Responsibilities)
   - Frequency (Daily or Weekly)
   - Minimum requirement (e.g., "10 minutes", "3 reps")
   - "Complete by" time (optional)
   - Grace period (number of days you can miss)
   - Custom icon and color (optional)
3. Click "Add Habit"

### Completing Tasks/Habits
- Click the checkbox/circle button next to any item to mark it complete
- Completed tasks show with strikethrough and can be unmarked until end of day
- Completed habits contribute to your streak counter

### Managing Items
- Click the trash icon to delete any task or habit
- Use the arrow button to uncomplete a task (only works on same day)

## Data Storage

All data is stored in a local SQLite database (`productivity.db`) including:
- Tasks with deadlines and priorities
- Habits with frequencies and requirements
- Habit completion logs for streak calculation

## Technical Details

- **Backend**: Python with SQLite database
- **Frontend**: Streamlit web framework
- **Database Schema**:
  - `tasks`: Stores all task information
  - `habits`: Stores habit definitions
  - `habit_logs`: Tracks daily/weekly habit completions
  - `settings`: App configuration

## Time Format

All times are displayed in 12-hour format (AM/PM) as specified.

## Week Configuration

Weeks start on Monday for all weekly habit tracking.
