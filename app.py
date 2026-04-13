import streamlit as st
import pandas as pd
from pathlib import Path

# =========================================================
# CONFIG — ONE DRIVE STORAGE (WINDOWS)
# =========================================================
DATA_DIR = Path(
    r"C:\Users\10019784\OneDrive - Maruti Suzuki India Limited\Parking_Slot\Data"
)
USERS_FILE = DATA_DIR / "users.csv"
STATUS_FILE = DATA_DIR / "parking_status.csv"
TOTAL_SLOTS = 10

# Ensure OneDrive directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# CSV LOADERS (AUTO-REPAIR)
# =========================================================
def load_users():
    df = pd.read_csv(USERS_FILE)
    df.columns = df.columns.str.strip()

    # Auto-fix broken single-column CSV
    if len(df.columns) == 1 and "," in df.columns[0]:
        df = df[df.columns[0]].str.split(",", expand=True)
        df.columns = ["username", "password"]
        df.to_csv(USERS_FILE, index=False)

    return df


def load_status():
    df = pd.read_csv(STATUS_FILE)
    df.columns = df.columns.str.strip()

    # Auto-fix broken single-column CSV
    if len(df.columns) == 1 and "," in df.columns[0]:
        df = df[df.columns[0]].str.split(",", expand=True)
        df.columns = ["username", "parked"]
        df.to_csv(STATUS_FILE, index=False)

    return df


def save_status(df):
    # ✅ Correct: no flush parameter
    df.to_csv(STATUS_FILE, index=False)


def authenticate(username, password):
    users = load_users()
    return not users[
        (users["username"] == username) &
        (users["password"] == password)
    ].empty

# =========================================================
# INITIAL FILE CREATION (FIRST RUN)
# =========================================================
if not USERS_FILE.exists():
    pd.DataFrame({
        "username": ["admin", "user1", "user2"],
        "password": ["admin123", "pass123", "pass456"]
    }).to_csv(USERS_FILE, index=False)

if not STATUS_FILE.exists():
    pd.DataFrame({
        "username": ["admin", "user1", "user2"],
        "parked": ["No", "No", "No"]
    }).to_csv(STATUS_FILE, index=False)

# =========================================================
# SESSION STATE
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# =========================================================
# LOGIN PAGE
# =========================================================
if not st.session_state.logged_in:
    st.title("🚗 Parking Slot Management System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# =========================================================
# DASHBOARD
# =========================================================
else:
    st.sidebar.title("User Panel")
    st.sidebar.write(f"👤 **{st.session_state.username}**")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.title("🅿 Parking Dashboard")

    status_df = load_status()

    # -----------------------------------------------------
    # UPDATE PARKING STATUS
    # -----------------------------------------------------
    st.subheader("Update Your Parking Status")

    current_status = status_df.loc[
        status_df["username"] == st.session_state.username,
        "parked"
    ].values[0]

    new_status = st.radio(
        "Is your car parked?",
        ["Yes", "No"],
        index=0 if current_status == "Yes" else 1
    )

    if st.button("Save Status"):
        status_df.loc[
            status_df["username"] == st.session_state.username,
            "parked"
        ] = new_status

        save_status(status_df)

        st.success("✅ Status saved to OneDrive")
        st.code(str(STATUS_FILE))
        st.rerun()

    st.divider()

    # -----------------------------------------------------
    # LIVE SLOT AVAILABILITY
    # -----------------------------------------------------
    st.subheader("Live Parking Slot Availability")

    occupied = status_df[status_df["parked"] == "Yes"].shape[0]
    available = TOTAL_SLOTS - occupied

    c1, c2 = st.columns(2)
    c1.metric("🚘 Occupied Slots", occupied)
    c2.metric("✅ Available Slots", available)

    st.divider()

    st.subheader("Current Parking Status (All Users)")
    st.dataframe(status_df, use_container_width=True)
