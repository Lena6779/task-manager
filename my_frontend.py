import requests
import streamlit as st

# --- CONFIG: match these to your backend ---
API_URL = "http://127.0.0.1:8000"
LOGIN_ENDPOINT = "/auth/token"
TASKS_ENDPOINT = "/tasks"
TIMEOUT = 5  # seconds before we give up on the backend

st.set_page_config(page_title="Task Manager", page_icon="✅", layout="wide")

# --- Session state ---
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "flash" not in st.session_state:
    st.session_state.flash = None

# --- Helpers ---
class BackendUnreachable(Exception):
    """Raised when the API can't be reached at all."""


def api_request(method, endpoint, **kwargs):
    """Send a request to the API. Raises BackendUnreachable if the server is down."""
    try:
        return requests.request(method, f"{API_URL}{endpoint}", timeout=TIMEOUT, **kwargs)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        raise BackendUnreachable()


def auth_headers():
    """The header that proves we're logged in."""
    return {"Authorization": f"Bearer {st.session_state.token}"}


def login(email, password):
    """Try to log in. Returns (token, error_message); one of them will be None."""
    response = api_request(
        "POST", LOGIN_ENDPOINT, data={"username": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"], None
    if response.status_code == 401:
        return None, "Incorrect email or password."
    if response.status_code == 403:
        return None, "This account is inactive."
    return None, f"Login failed (status {response.status_code})."


def show_backend_down():
    st.error(
        f"🚫 Can't reach the backend at {API_URL}. "
        "Start it with `uvicorn app.main:app --reload` and try again."
    )

def logout(message=None):
    """Forget the token and send the user back to the login page."""
    st.session_state.token = None
    st.session_state.username = None
    st.session_state.flash = message
    st.rerun()
    
def get_tasks():
    """Ask the API for the logged-in user's tasks."""
    return api_request("GET", TASKS_ENDPOINT, headers=auth_headers())

def create_task(title, description, priority):
    """Send a new task to the API."""
    payload = {
        "title": title,
        "description": description or None,  # send None instead of an empty string
        "priority": priority,
    }
    return api_request("POST", TASKS_ENDPOINT, json=payload, headers=auth_headers())

def toggle_task(task_id, completed):  # Wanted a way to say that a task was completed or not
    """Flip a task between done and not done."""
    return api_request(
        "PATCH",
        f"{TASKS_ENDPOINT}/{task_id}",
        json={"completed": not completed},
        headers=auth_headers(),
    )

# --- Pages ---
def login_page():
    st.title("🔐 Task Manager Login")
    
    if st.session_state.flash:
        st.warning(st.session_state.flash)
        st.session_state.flash = None

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        if not email or not password:
            st.error("Please enter both your email and password.")
            return
        try:
            token, error = login(email, password)
        except BackendUnreachable:
            show_backend_down()
            return

        if token:
            st.session_state.token = token
            st.session_state.username = email
            st.rerun()
        else:
            st.error(error)

def dashboard_page():
    with st.sidebar:
        st.header("👤 Account")
        st.write(f"Logged in as **{st.session_state.username}**")
        if st.button("Log out", use_container_width=True):
            logout("You have been logged out.")

    st.title("✅ My Tasks")

    if st.session_state.flash:
        st.success(st.session_state.flash)
        st.session_state.flash = None

    # Load tasks, handling every way it can go wrong
    try:
        response = get_tasks()
    except BackendUnreachable:
        show_backend_down()
        return

    if response.status_code == 401:
        logout("Your session expired. Please log in again.")
    if response.status_code != 200:
        st.error(f"Couldn't load tasks (status {response.status_code}).")
        return

    tasks = response.json()

    # --- Metrics ---
    total = len(tasks)
    completed = sum(1 for task in tasks if task["completed"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tasks", total)
    col2.metric("Completed", completed)
    col3.metric("Pending", total - completed)

    st.divider()

    # --- Task list ---
    st.subheader("📋 Task List")
    if not tasks:
        st.info("No tasks yet. Add one with the form!")
    for task in tasks:
        status = "✅ Done" if task["completed"] else "⏳ Pending"
        with st.container(border=True):
            info, action = st.columns([4, 1])
            with info:
                st.markdown(f"**{task['title']}** · {status} · Priority: {task['priority']}")
                if task["description"]:
                    st.caption(task["description"])
            with action:
                label = "Undo" if task["completed"] else "Mark Completed"
                if st.button(label, key=f"toggle_{task['id']}"):
                    try:
                        response = toggle_task(task["id"], task["completed"])
                    except BackendUnreachable:
                        show_backend_down()
                        return
                    if response.status_code == 401:
                        logout("Your session expired. Please log in again.")
                    if response.status_code == 200:
                        st.rerun()
                    else:
                        st.error(f"Couldn't update the task (status {response.status_code}).")

    st.divider()

    # --- Add task form ---
    st.subheader("➕ Add a Task")
    with st.form("add_task_form", clear_on_submit=True):
        title = st.text_input("Title", max_chars=200)
        description = st.text_area("Description (optional)", max_chars=1000)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
        add = st.form_submit_button("Add task")

    if add:
        if not title.strip():
            st.error("A task needs a title.")
            return
        try:
            response = create_task(title.strip(), description.strip(), priority)
        except BackendUnreachable:
            show_backend_down()
            return

        if response.status_code == 401:
            logout("Your session expired. Please log in again.")
        if response.status_code == 201:
            st.session_state.flash = f"Added '{title.strip()}'!"
            st.rerun()
        else:
            st.error(f"Couldn't add the task (status {response.status_code}).")


# --- Router: pick a page based on whether we have a token ---
if st.session_state.token:
    dashboard_page()
else:
    login_page()