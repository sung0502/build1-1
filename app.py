import streamlit as st
from datetime import datetime, timedelta
import database as db

# Page config
st.set_page_config(
    page_title="Productivity Dashboard",
    page_icon="🎯",
    layout="wide"
)

# Initialize database
db.init_database()

# Clean up old completed tasks on app start
db.cleanup_old_completed_tasks()

# Custom CSS for better styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stButton button {
        width: 100%;
    }
    .task-completed {
        text-decoration: line-through;
        opacity: 0.6;
    }
    .priority-high {
        border-left: 4px solid #ff4444;
        padding-left: 8px;
    }
    .priority-medium {
        border-left: 4px solid #ffaa44;
        padding-left: 8px;
    }
    .priority-low {
        border-left: 4px solid #44ff44;
        padding-left: 8px;
    }
    .habit-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    .streak-badge {
        background-color: #ff6b35;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def format_time_12hr(time_str):
    """Convert 24hr time to 12hr format."""
    if not time_str:
        return ""
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
        return time_obj.strftime("%I:%M %p")
    except:
        return time_str

def get_priority_color(priority):
    """Get color class for priority level."""
    if priority == "High":
        return "priority-high"
    elif priority == "Medium":
        return "priority-medium"
    else:
        return "priority-low"

def display_task(task, show_completed=False):
    """Display a single task with actions."""
    priority_class = get_priority_color(task['priority'])

    col1, col2, col3, col4 = st.columns([0.5, 3, 1, 0.8])

    with col1:
        if show_completed:
            if st.button("↩️", key=f"uncomplete_{task['id']}", help="Mark as pending"):
                db.uncomplete_task(task['id'])
                st.rerun()
        else:
            if st.button("✅", key=f"complete_{task['id']}", help="Mark as done"):
                db.complete_task(task['id'])
                st.rerun()

    with col2:
        title = task['title']
        if show_completed:
            st.markdown(f"<div class='task-completed {priority_class}'>~~{title}~~</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='{priority_class}'>{title}</div>", unsafe_allow_html=True)

        if task['description']:
            st.caption(task['description'])

        # Show deadline if exists
        if task['deadline']:
            deadline = datetime.fromisoformat(task['deadline'])
            deadline_str = deadline.strftime("%m/%d %I:%M %p") if task['time_specific'] else deadline.strftime("%m/%d")
            st.caption(f"📅 {deadline_str}")

    with col3:
        badge_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
        st.caption(f"{badge_color.get(task['priority'], '')} {task['priority']}")

    with col4:
        if st.button("🗑️", key=f"delete_{task['id']}", help="Delete task"):
            db.delete_task(task['id'])
            st.rerun()

def display_habit(habit, category):
    """Display a single habit with completion tracking."""
    completed = db.is_habit_completed_today(habit['id'])
    streak_info = db.get_habit_streak(habit['id'])

    with st.container():
        col1, col2, col3 = st.columns([0.5, 3, 0.8])

        with col1:
            if completed:
                if st.button("✅", key=f"hab_complete_{habit['id']}", help="Mark as incomplete"):
                    db.remove_habit_completion(habit['id'])
                    st.rerun()
            else:
                if st.button("⭕", key=f"hab_incomplete_{habit['id']}", help="Mark as complete"):
                    db.log_habit_completion(habit['id'])
                    st.rerun()

        with col2:
            icon = habit['icon'] if habit['icon'] else ""
            title = f"{icon} {habit['title']}" if icon else habit['title']

            if completed:
                st.markdown(f"**~~{title}~~**")
            else:
                st.markdown(f"**{title}**")

            # Show details
            details = []
            if habit['minimum_requirement']:
                details.append(f"Min: {habit['minimum_requirement']}")
            if habit['by_time']:
                details.append(f"By: {format_time_12hr(habit['by_time'])}")
            if habit['frequency']:
                details.append(f"{habit['frequency']}")

            if details:
                st.caption(" | ".join(details))

            # Show streaks
            if streak_info['current_streak'] > 0:
                st.markdown(
                    f"<span class='streak-badge'>🔥 {streak_info['current_streak']} day streak</span> "
                    f"<span style='color: #888; font-size: 0.8rem;'>Best: {streak_info['longest_streak']}</span>",
                    unsafe_allow_html=True
                )

        with col3:
            if st.button("🗑️", key=f"del_hab_{habit['id']}", help="Delete habit"):
                db.delete_habit(habit['id'])
                st.rerun()

# Main App
st.title("🎯 Productivity Dashboard")

# Create two main columns
left_col, right_col = st.columns([1, 1])

# ==================== LEFT SIDE: TASKS ====================
with left_col:
    st.header("📋 Tasks")

    # Today's Tasks
    st.subheader("✅ Today's To-Do")
    pending_today, completed_today = db.get_today_tasks()

    if not pending_today and not completed_today:
        st.info("No tasks for today. Add one below!")
    else:
        # Show pending tasks
        for task in pending_today:
            display_task(task, show_completed=False)

        # Show completed tasks in a separate section
        if completed_today:
            st.markdown("---")
            st.caption("✓ Completed Today")
            for task in completed_today:
                display_task(task, show_completed=True)

    st.markdown("---")

    # Next 3 Days
    st.subheader("📅 Next 3 Days")
    tasks_3days = db.get_tasks(days_ahead=3, completed=False)
    # Filter out today's tasks
    today_ids = [t['id'] for t in pending_today]
    tasks_3days = [t for t in tasks_3days if t['id'] not in today_ids]

    if not tasks_3days:
        st.info("No tasks in the next 3 days")
    else:
        for task in tasks_3days[:5]:  # Limit display
            display_task(task, show_completed=False)

    st.markdown("---")

    # Next 7 Days
    st.subheader("🔮 Next 7 Days")
    tasks_7days = db.get_tasks(days_ahead=7, completed=False)
    # Filter out tasks already shown
    shown_ids = today_ids + [t['id'] for t in tasks_3days]
    tasks_7days = [t for t in tasks_7days if t['id'] not in shown_ids]

    if not tasks_7days:
        st.info("No tasks in the next 7 days")
    else:
        for task in tasks_7days[:5]:  # Limit display
            display_task(task, show_completed=False)

    st.markdown("---")

    # Add Task Form
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("add_task_form", clear_on_submit=True):
            task_title = st.text_input("Task Title*", placeholder="What needs to be done?")
            task_desc = st.text_area("Description (optional)", placeholder="Additional details...")

            col1, col2 = st.columns(2)
            with col1:
                task_priority = st.selectbox("Priority*", ["High", "Medium", "Low"], index=1)
                deadline_date = st.date_input("Date (optional)", value=None)

            with col2:
                deadline_time = st.time_input("Time (optional)", value=None)

            submitted = st.form_submit_button("Add Task")

            if submitted and task_title:
                deadline = None
                time_str = ""
                if deadline_date:
                    if deadline_time:
                        deadline = datetime.combine(deadline_date, deadline_time)
                        time_str = deadline_time.strftime("%H:%M")
                    else:
                        deadline = datetime.combine(deadline_date, datetime.min.time())

                db.add_task(
                    title=task_title,
                    category="Tasks",
                    priority=task_priority,
                    description=task_desc,
                    deadline=deadline,
                    time_specific=time_str
                )
                st.success("Task added!")
                st.rerun()

# ==================== RIGHT SIDE: HABITS ====================
with right_col:
    st.header("🌟 Habits & Routines")

    # Personal Habits
    st.subheader("☀️ Personal Habits")
    personal_habits = db.get_habits(category="Personal Habits")

    if not personal_habits:
        st.info("No personal habits yet. Add one below!")
    else:
        for habit in personal_habits:
            display_habit(habit, "Personal Habits")

    st.markdown("---")

    # Responsibilities
    st.subheader("📌 Responsibilities")
    responsibilities = db.get_habits(category="Responsibilities")

    if not responsibilities:
        st.info("No responsibilities yet. Add one below!")
    else:
        for habit in responsibilities:
            display_habit(habit, "Responsibilities")

    st.markdown("---")

    # Add Habit Form
    with st.expander("➕ Add New Habit", expanded=False):
        with st.form("add_habit_form", clear_on_submit=True):
            habit_title = st.text_input("Habit Title*", placeholder="e.g., Morning workout")
            habit_desc = st.text_area("Description (optional)", placeholder="Additional details...")

            col1, col2 = st.columns(2)
            with col1:
                habit_category = st.selectbox("Category*", ["Personal Habits", "Responsibilities"])
                habit_frequency = st.selectbox("Frequency*", ["Daily", "Weekly"])
                habit_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)

            with col2:
                habit_min_req = st.text_input("Minimum Requirement", placeholder="e.g., 3 push-ups")
                habit_by_time = st.time_input("Complete by (optional)", value=None)
                habit_grace = st.number_input("Grace Period (days)", min_value=0, max_value=7, value=0,
                                             help="Number of days you can miss before streak breaks")

            col3, col4 = st.columns(2)
            with col3:
                habit_icon = st.text_input("Icon (optional)", placeholder="e.g., 💪")
            with col4:
                habit_color = st.color_picker("Color (optional)", value="#FF6B35")

            submitted = st.form_submit_button("Add Habit")

            if submitted and habit_title:
                by_time_str = habit_by_time.strftime("%H:%M") if habit_by_time else ""

                db.add_habit(
                    title=habit_title,
                    category=habit_category,
                    frequency=habit_frequency,
                    by_time=by_time_str,
                    minimum_requirement=habit_min_req,
                    description=habit_desc,
                    priority=habit_priority,
                    color=habit_color,
                    icon=habit_icon,
                    grace_period=habit_grace
                )
                st.success("Habit added!")
                st.rerun()

# Footer
st.markdown("---")
st.caption("💡 Tip: Click the checkboxes to mark tasks/habits as complete!")
