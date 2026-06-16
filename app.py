import streamlit as st
import sqlite3
import pandas as pd
import uuid
import qrcode
import os
from datetime import datetime

# ==========================
# DATABASE
# ==========================

conn = sqlite3.connect("sportsync.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
email TEXT UNIQUE,
password TEXT,
role TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS bookings(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_email TEXT,
sport TEXT,
booking_date TEXT,
time_slot TEXT,
booking_code TEXT UNIQUE
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS performance(
id INTEGER PRIMARY KEY AUTOINCREMENT,
booking_code TEXT,
distance REAL,
speed REAL,
accuracy REAL,
coach_notes TEXT
)
""")

conn.commit()

# ==========================
# FUNCTIONS
# ==========================

def register_user(name,email,password,role):
    try:
        c.execute(
            "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
            (name,email,password,role)
        )
        conn.commit()
        return True
    except:
        return False

def login_user(email,password):
    c.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email,password)
    )
    return c.fetchone()

def generate_booking_code():
    return str(uuid.uuid4())[:8].upper()

def create_qr(code):
    if not os.path.exists("qrcodes"):
        os.mkdir("qrcodes")

    path=f"qrcodes/{code}.png"

    qr=qrcode.make(code)
    qr.save(path)

    return path

# ==========================
# SESSION
# ==========================

if "logged_in" not in st.session_state:
    st.session_state.logged_in=False

if "user" not in st.session_state:
    st.session_state.user=None

# ==========================
# HEADER
# ==========================

st.set_page_config(
    page_title="SportsSync",
    page_icon="🏆",
    layout="wide"
)

st.title("🏆 SportsSync")
st.caption("Smart Sports Facility Booking & Performance Tracking")

# ==========================
# LOGIN PAGE
# ==========================

if not st.session_state.logged_in:

    tab1,tab2=st.tabs(["Login","Register"])

    with tab1:

        st.subheader("Login")

        email=st.text_input("Email")
        password=st.text_input("Password",type="password")

        if st.button("Login"):

            user=login_user(email,password)

            if user:
                st.session_state.logged_in=True
                st.session_state.user=user
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:

        st.subheader("Register")

        name=st.text_input("Full Name")
        reg_email=st.text_input("Email Address")
        reg_password=st.text_input("Password",type="password")

        role=st.selectbox(
            "Role",
            ["Student","Coach"]
        )

        if st.button("Register"):

            success=register_user(
                name,
                reg_email,
                reg_password,
                role
            )

            if success:
                st.success("Account created")
            else:
                st.error("Email already exists")

# ==========================
# DASHBOARD
# ==========================

else:

    user=st.session_state.user

    username=user[1]
    email=user[2]
    role=user[4]

    st.sidebar.success(f"Welcome {username}")
    st.sidebar.write(f"Role: {role}")

    page=st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Book Slot",
            "Track Performance",
            "Bookings",
            "Coach Panel"
        ]
    )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in=False
        st.rerun()

    # ==========================
    # DASHBOARD
    # ==========================

    if page=="Dashboard":

        st.header("📊 Dashboard")

        bookings_df=pd.read_sql_query(
            f"""
            SELECT * FROM bookings
            WHERE user_email='{email}'
            """,
            conn
        )

        st.metric(
            "Total Bookings",
            len(bookings_df)
        )

        perf_df=pd.read_sql_query(
            "SELECT * FROM performance",
            conn
        )

        if len(perf_df)>0:

            st.subheader("Performance Trend")

            chart_df=perf_df[
                ["distance","speed","accuracy"]
            ]

            st.line_chart(chart_df)

        else:
            st.info("No performance records yet")

    # ==========================
    # BOOK SLOT
    # ==========================

    elif page=="Book Slot":

        st.header("🏟 Book Sports Facility")

        sports=[
            "Basketball",
            "Football",
            "Cricket",
            "Gym",
            "Swimming",
            "Table Tennis",
            "Tennis",
            "Snooker"
        ]

        sport=st.selectbox(
            "Sport",
            sports
        )

        booking_date=st.date_input(
            "Booking Date"
        )

        slot=st.selectbox(
            "Time Slot",
            [
                "06:00-07:00",
                "07:00-08:00",
                "08:00-09:00",
                "17:00-18:00",
                "18:00-19:00",
                "19:00-20:00"
            ]
        )

        if st.button("Book Now"):

            code=generate_booking_code()

            c.execute(
                """
                INSERT INTO bookings(
                user_email,
                sport,
                booking_date,
                time_slot,
                booking_code
                )
                VALUES(?,?,?,?,?)
                """,
                (
                    email,
                    sport,
                    str(booking_date),
                    slot,
                    code
                )
            )

            conn.commit()

            qr_path=create_qr(code)

            st.success("Booking Successful")

            st.write(
                f"Booking Code: {code}"
            )

            st.image(qr_path,width=250)

    # ==========================
    # TRACK PERFORMANCE
    # ==========================

    elif page=="Track Performance":

        st.header("📈 Performance Tracking")

        booking_code=st.text_input(
            "Booking Code"
        )

        distance=st.number_input(
            "Distance Covered (m)",
            min_value=0.0
        )

        speed=st.number_input(
            "Average Speed",
            min_value=0.0
        )

        accuracy=st.slider(
            "Accuracy %",
            0,
            100
        )

        if st.button("Save Performance"):

            c.execute(
                """
                INSERT INTO performance(
                booking_code,
                distance,
                speed,
                accuracy,
                coach_notes
                )
                VALUES(?,?,?,?,?)
                """,
                (
                    booking_code,
                    distance,
                    speed,
                    accuracy,
                    ""
                )
            )

            conn.commit()

            st.success(
                "Performance Added"
            )

    # ==========================
    # BOOKINGS
    # ==========================

    elif page=="Bookings":

        st.header("📋 Booking History")

        df=pd.read_sql_query(
            f"""
            SELECT *
            FROM bookings
            WHERE user_email='{email}'
            """,
            conn
        )

        st.dataframe(
            df,
            use_container_width=True
        )

    # ==========================
    # COACH PANEL
    # ==========================

    elif page=="Coach Panel":

        if role!="Coach":
            st.warning(
                "Only coaches can access this page"
            )

        else:

            st.header("🧑‍🏫 Coach Insights")

            booking_code=st.text_input(
                "Booking Code"
            )

            coach_note=st.text_area(
                "Feedback"
            )

            if st.button(
                "Save Feedback"
            ):

                c.execute(
                    """
                    UPDATE performance
                    SET coach_notes=?
                    WHERE booking_code=?
                    """,
                    (
                        coach_note,
                        booking_code
                    )
                )

                conn.commit()

                st.success(
                    "Feedback Added"
                )

            st.subheader(
                "All Performance Records"
            )

            df=pd.read_sql_query(
                """
                SELECT *
                FROM performance
                """,
                conn
            )

            st.dataframe(
                df,
                use_container_width=True
            )