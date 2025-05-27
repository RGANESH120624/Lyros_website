import streamlit as st
from supabase import create_client, Client
from gotrue.errors import AuthApiError

# --- Supabase Configuration ---
SUPABASE_URL = "https://mtsezzuxftuxfsjxgyoz.supabase.co"   # Replace with your Supabase URL
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im10c2V6enV4ZnR1eGZzanhneW96Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Nzk4NTI0MCwiZXhwIjoyMDYzNTYxMjQwfQ.IvN-sRroTnD5X94HZ2KwOCBu6Yp95ss_Kkw1KIfvtvI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Ensure 'users' table exists via RPC ---
def ensure_table_exists():
    query = """
    create table if not exists users (
        id uuid primary key references auth.users(id),
        username text unique,
        created_at timestamp with time zone default timezone('utc'::text, now())
    );
    """
    try:
        supabase.rpc("execute_sql", {"sql": query}).execute()
    except Exception as e:
        st.warning(f"Table creation check failed: {e}")

# --- Create user with email verification ---
def create_user_with_email_verification(email, password, username):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            user_id = response.user.id
            supabase.table("users").insert({"id": user_id, "username": username}).execute()
            return True, "📩 Check your email for verification."
        else:
            return False, "Sign-up failed."
    except AuthApiError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

# --- Login user ---
def login_user(email, password):
    try:
        result = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = result.user
        if user and user.email_confirmed_at:
            return True, user
        elif user:
            return False, "❌ Email not verified. Please verify your email before logging in."
        else:
            return False, "Login failed."
    except AuthApiError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

# --- Streamlit App ---
def main():
    st.set_page_config(page_title="Secure Login", layout="centered")

    ensure_table_exists()

    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.page == "home":
        st.title("Welcome to the App")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login"):
                st.session_state.page = "login"
        with col2:
            if st.button("Sign Up"):
                st.session_state.page = "signup"

    elif st.session_state.page == "signup":
        st.header("🔐 Sign Up")
        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            if not email or not password or not username:
                st.warning("⚠️ Please fill all fields.")
            else:
                success, message = create_user_with_email_verification(email, password, username)
                if success:
                    st.success(message)
                    st.info("Return to login after email verification.")
                else:
                    st.error(message)

        st.button("Back", on_click=lambda: st.session_state.update({"page": "home"}))

    elif st.session_state.page == "login":
        st.header("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if not email or not password:
                st.warning("⚠️ Please enter email and password.")
            else:
                success, result = login_user(email, password)
                if success:
                    st.success("✅ Logged in!")
                    st.session_state.user = result
                    st.session_state.page = "dashboard"
                else:
                    st.error(result)

        st.button("Back", on_click=lambda: st.session_state.update({"page": "home"}))

    elif st.session_state.page == "dashboard":
        st.success(f"Welcome, {st.session_state.user.email}")
        st.write("🎉 You are verified and logged in.")
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.page = "home"
            st.session_state.user = None

if __name__ == "__main__":
    main()
