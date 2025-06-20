import streamlit as st
from supabase import create_client, Client

# --- Supabase Configuration ---
SUPABASE_URL = "https://mtsezzuxftuxfsjxgyoz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im10c2V6enV4ZnR1eGZzanhneW96Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Nzk4NTI0MCwiZXhwIjoyMDYzNTYxMjQwfQ.IvN-sRroTnD5X94HZ2KwOCBu6Yp95ss_Kkw1KIfvtvI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Ensure 'users' table exists ---
def ensure_users_table():
    try:
        response = supabase.table("users").select("*").limit(1).execute()
    except Exception:
        query = """
        create table if not exists public.users (
            id uuid primary key references auth.users(id) on delete cascade,
            username text unique,
            created_at timestamp with time zone default timezone('utc'::text, now())
        );
        """
        supabase.rpc("execute_sql", {"sql": query}).execute()

# --- Sign up with email verification ---
def create_user_with_email_verification(email, password):
    response = supabase.auth.sign_up({
        "email": email,
        "password": password
    })

    if "user" in response and response["user"] is not None:
        return True, "📩 Check your email for verification."
    elif "error" in response:
        return False, response["error"]["message"]
    return False, "Unknown error."

# --- Login user and insert into 'users' table if verified ---
def login_user(email, password):
    result = supabase.auth.sign_in_with_password({"email": email, "password": password})
    user = result.get("user", None)

    if user and user.get("email_confirmed_at", None):
        user_id = user["id"]
        username = email.split("@")[0]

        existing = supabase.table("users").select("id").eq("id", user_id).execute()
        if not existing.data:
            supabase.table("users").insert({"id": user_id, "username": username}).execute()

        return True, user
    elif user:
        return False, "❌ Email not verified. Please verify your email before logging in."
    else:
        return False, result.get("error", {}).get("message", "Login failed.")

# --- Streamlit App ---
def main():
    st.set_page_config(page_title="Login App", layout="centered")
    ensure_users_table()

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
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            if not email or not password:
                st.warning("⚠️ Please fill all fields.")
            else:
                success, message = create_user_with_email_verification(email, password)
                if success:
                    st.success(message)
                    st.info("Return to login after verifying your email.")
                else:
                    st.error(message)

        st.button("Back", on_click=lambda: st.session_state.update({"page": "home"}))

    elif st.session_state.page == "login":
        st.header("🔑 Login")
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
        st.success(f"Welcome, {st.session_state.user.get('email')}")
        st.write("🎉 You are verified and logged in.")
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.page = "home"
            st.session_state.user = None

if __name__ == "__main__":
    main()
