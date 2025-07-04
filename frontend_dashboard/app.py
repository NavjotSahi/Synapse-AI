# frontend_dashboard/app.py (or your main Streamlit file)

import streamlit as st
import requests
import pandas as pd
import json # For parsing JSON responses

# --- Configuration ---
DJANGO_API_HOST = "http://127.0.0.1:8000" # Your Django backend URL

# Auth URLs from dj-rest-auth
LOGIN_URL = f"{DJANGO_API_HOST}/api/auth/login/"
LOGOUT_URL = f"{DJANGO_API_HOST}/api/auth/logout/"
USER_DETAIL_URL = f"{DJANGO_API_HOST}/api/auth/user/" # dj-rest-auth default user detail
REGISTRATION_URL = f"{DJANGO_API_HOST}/api/auth/registration/"
# PASSWORD_RESET_URL = f"{DJANGO_API_HOST}/api/auth/password/reset/" # For forgot password page later
# PASSWORD_RESET_CONFIRM_URL = f"{DJANGO_API_HOST}/api/auth/password/reset/confirm/" # For forgot password later

# Student Data URLs
MY_COURSES_URL = f"{DJANGO_API_HOST}/api/my-courses/"
MY_ASSIGNMENTS_URL = f"{DJANGO_API_HOST}/api/my-assignments/"
MY_GRADES_URL = f"{DJANGO_API_HOST}/api/my-grades/"
CHATBOT_URL = f"{DJANGO_API_HOST}/api/chatbot/query/"

# Teacher Data URLs
TEACHER_COURSES_URL = f"{DJANGO_API_HOST}/api/teacher/my-courses/" # Ensure this endpoint exists
UPLOAD_CONTENT_URL = f"{DJANGO_API_HOST}/api/teacher/upload-content/"


# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None # Will store 'Student' or 'Teacher' string
if 'error_message' not in st.session_state:
    st.session_state.error_message = None
if 'current_page' not in st.session_state: # For multi-page feeling in single script
    st.session_state.current_page = "login"
if 'logout_message' not in st.session_state: # New state for logout message
    st.session_state.logout_message = None

# Use a global requests.Session object stored in session_state
if 'api_session' not in st.session_state:
    st.session_state.api_session = requests.Session()
    # If your Django backend expects a CSRF token for POST non-cookie auth (not typical for dj-rest-auth JWT)
    # you might fetch it here. But for JWT cookie auth, CSRF is often handled differently or not needed for API.
    # For now, assume dj-rest-auth handles CSRF for its cookie auth if needed.


# --- API Helper Functions ---

def fetch_user_details_and_set_role():
    print("DEBUG: Attempting to fetch user details...")
    try:
        response = st.session_state.api_session.get(USER_DETAIL_URL)
        print(f"DEBUG: User detail response status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            st.session_state.user_info = user_data
            groups = user_data.get('groups', [])
            
            if "Teachers" in groups:
                st.session_state.user_role = 'Teacher'
            elif "Students" in groups:
                st.session_state.user_role = 'Student'
            else:
                st.session_state.user_role = None 
            
            print(f"DEBUG: User details: {user_data}, Role: {st.session_state.user_role}")
            return True
        elif response.status_code == 401:
            logout_user(silent=True, error_msg="Session invalid. Please log in.")
            return False
        else:
            st.session_state.error_message = f"Failed to fetch user details (Status: {response.status_code})."
            return False
    except requests.exceptions.RequestException as e:
        st.session_state.error_message = f"Network error fetching user details: {e}"
        return False

def login_user(username, password):
    print(f"DEBUG: Logging in user: {username}")
    try:
        response = st.session_state.api_session.post(
            LOGIN_URL,
            data={'username': username, 'password': password} # dj-rest-auth can take 'email' or 'username' in 'username' field if configured
        )
        if response.status_code == 200:
            # Cookies should be set. Now verify by fetching user details.
            if fetch_user_details_and_set_role():
                st.session_state.logged_in = True
                st.session_state.error_message = None
                st.session_state.current_page = "dashboard" # Navigate to dashboard on successful login
                print("DEBUG: Login and user details fetch successful. Rerunning for dashboard.")
                st.rerun()
            else:
                # User details fetch failed even after 200 OK on login
                st.session_state.logged_in = False # Ensure not marked as logged in
                if not st.session_state.get('error_message'): # Avoid overwriting specific error from fetch
                    st.session_state.error_message = "Login successful, but failed to confirm user session."
        elif response.status_code == 400:
            try:
                error_data = response.json()
                detail = error_data.get('non_field_errors', [error_data.get('detail', 'Invalid credentials.')])[0]
                st.session_state.error_message = detail
            except json.JSONDecodeError:
                 st.session_state.error_message = "Invalid credentials or server error."
            print(f"DEBUG: Login failed (400). Error: {st.session_state.error_message}")
        else:
            st.session_state.error_message = f"Login failed (Status: {response.status_code})."
            print(f"DEBUG: Login failed. Status: {response.status_code}, Text: {response.text}")
    except requests.exceptions.RequestException as e:
        st.session_state.error_message = f"Network error during login: {e}"

def logout_user(silent=False, error_msg=None):
    print("DEBUG: Logging out.")
    try:
        st.session_state.api_session.post(LOGOUT_URL)
    except requests.exceptions.RequestException as e:
        print(f"Network error during backend logout: {e}")

    keys_to_clear = ['logged_in', 'user_info', 'user_role', 'error_message']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.current_page = "login" # Always go to login after logout
    
    if error_msg: 
        st.session_state.error_message = error_msg # This will be displayed by login page
    elif not silent:
        st.session_state.logout_message = "Logged out successfully." # Set flag for message


def api_register_user(username, email, password, password2, role):
    print(f"DEBUG: Registering user: {username} with role: {role}")
    try:
        # The backend serializer is expecting 'password' (or 'password1') and 'password2'
        # Let's try sending 'password' and 'password2' first, as that's more common.
        # If the error was "Password1: This field is required", it means the backend
        # specifically wants 'password1' for the main password.
        payload = {
            'username': username,
            'email': email,
            'password': password, # This is the main password
            'password2': password2, # This is the confirmation
            'role':role
        }
        
        # Based on your error "Password1: This field is required.",
        # it seems dj-rest-auth's RegisterSerializer is expecting 'password1' and 'password2'.
        # This can happen depending on versions or specific allauth configurations.
        # Let's adjust to what the error message implies:
        payload_for_backend = {
            'username': username,
            'email': email,
            'password1': password,  # Send the main password value under the key 'password1'
            'password2': password2,  # Send the confirmation password value under the key 'password2'
            'role': role  # Send the selected role (e.g., "Student" or "Educator")
        }
        
        print(f"DEBUG: Registration payload being sent: {payload_for_backend}") # Log the payload

        response = st.session_state.api_session.post(
            REGISTRATION_URL,
            data=payload_for_backend # Use the adjusted payload
        )
        return response 
    except requests.exceptions.RequestException as e:
        st.session_state.error_message = f"Network error during registration: {e}"
        return None


def fetch_protected_data(url, params=None):
    print(f"DEBUG: Fetching protected data from: {url}")
    try:
        response = st.session_state.api_session.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            logout_user(silent=True, error_msg="Session expired or invalid. Please log in.")
            return None
        elif response.status_code == 403:
             st.error(f"Access Denied: You do not have permission to view this resource.")
             return None
        else:
             st.error(f"Error fetching data from {url} (Status: {response.status_code})")
             try: print(f"Error details for {url}: {response.json()}")
             except: print(f"Error details for {url} (raw): {response.text}")
             return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching data from {url}: {e}")
        return None

# --- UI Page Rendering Functions ---

def show_login_page():
    # Check for and display logout message first
    if st.session_state.get('logout_message'):
        st.success(st.session_state.logout_message)
        st.session_state.logout_message = None # Clear after displaying

    st.subheader("Login to CourseCompanionAI")

    with st.form("login_form_ui"):
        username_or_email = st.text_input("Username or Email", key="login_username_ui")
        password = st.text_input("Password", type="password", key="login_password_ui")
        submitted = st.form_submit_button("Login")
        if submitted:
            if not username_or_email or not password:
                st.error("Username/Email and Password are required.")
            else:
                login_user(username_or_email, password) # This will rerun on success

    if st.session_state.get('error_message'): # Display errors from login_user or other actions
        st.error(st.session_state.error_message)
        st.session_state.error_message = None # Clear after display
    
    col1, col2 = st.columns([0.3, 0.7]) # Adjust column width ratios if needed
    with col1:
        if st.button("New User? Sign Up", key="nav_to_signup"):
            st.session_state.current_page = "signup"
            st.rerun()
    # with col2: # Placeholder for forgot password
        # if st.button("Forgot Password?", key="nav_to_forgot"):
        #     st.session_state.current_page = "forgot_password"
        #     st.rerun()

def show_signup_page():
    st.subheader("Create New Account")
    with st.form("signup_form_ui_with_role"): # Use a new unique key for the form
        role_options = ["Student", "Educator"] # "Educator" maps to "Teachers" group
        selected_role = st.radio("I am a:", role_options, key="signup_role_selection") # Add this
        
        username = st.text_input("Username", key="signup_username_role")
        email = st.text_input("Email", key="signup_email_role")
        password = st.text_input("Password", type="password", key="signup_password1_role")
        password2 = st.text_input("Confirm Password", type="password", key="signup_password2_role")
        submitted = st.form_submit_button("Create Account")

        if submitted:
            if not all([username, email, password, password2, selected_role]):
                st.error("All fields, including role selection, are required.")
            elif password != password2:
                st.error("Passwords do not match.")
            else:
                # Map Streamlit role selection to backend expected role/group name
                # Let's send the selected_role string directly to the backend.
                # The backend will handle mapping "Educator" to the "Teachers" group.
                with st.spinner("Creating account..."):
                    response = api_register_user(username, email, password, password2, selected_role) # Pass selected_role
                
                if response is None: 
                    st.error(st.session_state.get('error_message', "Registration failed due to network issue."))
                elif response.status_code == 201: 
                    st.success("Registration successful! You can now log in.")
                    st.session_state.current_page = "login"
                    st.rerun()
                elif response.status_code == 400: 
                    try:
                        errors = response.json()
                        for field, messages in errors.items():
                            # Handle the 'role' field error if backend sends it
                            if field == 'role' or field == 'non_field_errors':
                                 st.error(f"{', '.join(messages)}")
                            else:
                                 st.error(f"{field.capitalize()}: {', '.join(messages)}")
                    except json.JSONDecodeError:
                        st.error("Registration failed: Invalid data or server error.")
                else:
                    st.error(f"Registration failed (Status: {response.status_code}). Please try again.")
                    try: print(f"Registration error details: {response.json()}")
                    except: print(f"Registration error details (raw): {response.text}")

    if st.button("Already have an account? Login", key="nav_to_login_from_signup_role"):
        st.session_state.current_page = "login"
        st.rerun()

def show_dashboard_page():
    # This is where your existing student/teacher dashboard logic will go
    # (Copied from your provided app.py, with minor adjustments for new auth flow)
    role = st.session_state.get('user_role') 
    user_display_name = st.session_state.get('user_info', {}).get('username', 'User') 

    st.sidebar.success(f"Logged in as: {user_display_name} ({role or 'Unknown Role'})")
    st.sidebar.button("Logout", on_click=logout_user, key="dashboard_sidebar_logout_button")
    st.sidebar.markdown("---") 

    if role == "Student":
        st.header("Student Dashboard")
        st.subheader("My Courses")
        courses_data = fetch_protected_data(MY_COURSES_URL)
        if courses_data:
            try:
                # Ensure courses_data is a list of dicts, and each dict has 'course'
                valid_course_entries = [c.get('course') for c in courses_data if isinstance(c, dict) and 'course' in c and isinstance(c['course'], dict)]
                if valid_course_entries:
                    df_courses = pd.DataFrame(valid_course_entries)
                    if not df_courses.empty and all(col in df_courses for col in ['code', 'name', 'teacher_username']):
                        df_display = df_courses[['code', 'name', 'teacher_username']]
                        df_display.columns = ['Course Code', 'Course Name', 'Teacher']
                        st.dataframe(df_display, use_container_width=True)
                    else: st.info("Course data format is missing expected columns (code, name, teacher_username).")
                else: st.info("You are not currently enrolled in any courses or course data is malformed.")
            except Exception as e: st.error(f"Error displaying courses: {e}")
        
        st.subheader("My Upcoming Assignments")
        assignments_data = fetch_protected_data(MY_ASSIGNMENTS_URL)
        if assignments_data:
            try:
                if assignments_data: # Check if list is not empty
                    df = pd.DataFrame(assignments_data)
                    if not df.empty and all(col in df for col in ['course_code', 'title', 'due_date', 'total_points']):
                        df['due_date'] = pd.to_datetime(df['due_date']).dt.strftime('%Y-%m-%d %H:%M')
                        df_display_assignments = df[['course_code', 'title', 'due_date', 'total_points']]
                        df_display_assignments.columns = ['Course', 'Title', 'Due Date', 'Points']
                        st.dataframe(df_display_assignments.sort_values(by='Due Date'), use_container_width=True)
                    else: st.info("Assignments data format is missing expected columns.")
                else: st.info("No upcoming assignments found.")
            except Exception as e: st.error(f"Error displaying assignments: {e}")

        st.subheader("My Grades")
        grades_data = fetch_protected_data(MY_GRADES_URL)
        if grades_data:
            try:
                if grades_data:
                    df = pd.DataFrame(grades_data)
                    if not df.empty and all(col in df for col in ['course_code', 'assignment_title', 'submission_status']):
                        df['score'] = df['score'].apply(lambda x: float(x) if x is not None else None)
                        df['display_score'] = df.apply(lambda row: f"{row['score']:.2f}" if row['score'] is not None else 'N/A', axis=1)
                        df['submitted_at_str'] = pd.to_datetime(df.get('submitted_at'), errors='coerce').dt.strftime('%Y-%m-%d %H:%M') if 'submitted_at' in df else 'N/A'
                        display_cols = ['course_code', 'assignment_title', 'display_score', 'submission_status', 'submitted_at_str']
                        df_grades_display = df[display_cols]
                        df_grades_display.columns = ['Course', 'Assignment', 'Score', 'Status', 'Submitted']
                        st.dataframe(df_grades_display, use_container_width=True)
                    else: st.info("Grades data format is missing expected columns.")
                else: st.info("No grades found for you yet.")
            except Exception as e: st.error(f"Error displaying grades: {e}")
        
        st.sidebar.header("Course Chatbot")
        user_query = st.sidebar.text_input("Ask about course content or your data:", key="student_chat_query_input")
        if st.sidebar.button("Ask Chatbot", key="student_chat_submit_button"):
            if user_query:
                with st.sidebar.spinner("Sending query..."):
                    try:
                        resp = st.session_state.api_session.post(CHATBOT_URL, json={"query": user_query})
                        if resp.status_code == 200:
                            st.sidebar.success("Chatbot Response:")
                            st.sidebar.markdown(resp.json().get('response', 'Received empty response.'))
                        elif resp.status_code == 401:
                             logout_user(silent=True, error_msg="Session expired. Please log in to use chatbot.")
                        else: st.sidebar.error(f"Chatbot error: Status {resp.status_code}")
                    except requests.exceptions.RequestException as e:
                        st.sidebar.error(f"Network error with chatbot: {e}")
            else: st.sidebar.warning("Please enter a question.")

    elif role == "Teacher":
        st.header("Teacher Dashboard")
        st.subheader("My Courses & Content Upload")
        teacher_courses = fetch_protected_data(TEACHER_COURSES_URL)
        if teacher_courses:
            if teacher_courses: # Check list not empty
                for course in teacher_courses:
                    course_id = course.get('id')
                    course_code = course.get('code', 'N/A')
                    course_name = course.get('name', 'N/A')
                    with st.expander(f"**{course_code} - {course_name}** (ID: {course_id})"):
                        if course_id:
                            st.write("Upload new content (PDF, DOCX, TXT):")
                            uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx', 'txt'], key=f"upload_teacher_{course_id}_{course_code}")
                            if uploaded_file:
                                files_payload = {'file': (uploaded_file.name, uploaded_file, uploaded_file.type)}
                                data_payload = {'course_id': str(course_id)}
                                
                                if st.button(f"Upload {uploaded_file.name} for {course_code}", key=f"btn_upload_teacher_{course_id}_{course_code}"):
                                    with st.spinner(f"Uploading {uploaded_file.name}..."):
                                        try:
                                            resp_upload = st.session_state.api_session.post(UPLOAD_CONTENT_URL, files=files_payload, data=data_payload)
                                            if resp_upload.status_code == 201:
                                                st.success(f"Uploaded and processed '{uploaded_file.name}'!")
                                            elif resp_upload.status_code == 401:
                                                logout_user(silent=True, error_msg="Session expired during upload. Please log in.")
                                            else:
                                                error_detail = "Upload failed."
                                                try: error_detail = resp_upload.json().get('detail', resp_upload.json().get('error', f'Status {resp_upload.status_code}'))
                                                except: pass 
                                                st.error(f"Upload failed: {error_detail}")
                                        except requests.exceptions.RequestException as e: st.error(f"Network error during upload: {e}")
                        else: st.warning("Course ID missing for this entry.")
            else: st.info("You are not currently assigned to teach any courses.")

    else: # Logged in but role is None or unexpected
        st.error("Your user role is not recognized or could not be determined. Please log out and try again or contact support.")
        print(f"DEBUG: Invalid or undetermined role '{role}' for logged-in user {st.session_state.get('user_info', {}).get('username')}")
        if st.button("Logout (Role Issue)", key="role_issue_logout_button"):
            logout_user(silent=True)


# --- Main App Logic for Page Navigation ---
def run_app():
    st.set_page_config(page_title="Synapse AI", layout="wide", initial_sidebar_state="expanded")
    st.title("Synapse AI")
    st.markdown("---")

    is_effectively_logged_out_this_run = not st.session_state.get('logged_in', False)

    if st.session_state.logged_in and st.session_state.current_page == "dashboard":
        show_dashboard_page()
    elif st.session_state.current_page == "signup":
        show_signup_page()
    # elif st.session_state.current_page == "forgot_password":
        # show_forgot_password_page() # Placeholder
    else: # Default to login if not logged in or unknown page
        st.session_state.current_page = "login" # Ensure current page is set to login
        show_login_page()

if __name__ == "__main__":
    run_app()