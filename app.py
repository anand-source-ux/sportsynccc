from flask import Flask, request, redirect, url_for, render_template_string, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import uuid
import qrcode
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sportsync123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sportsync.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# --------------------------
# DATABASE MODELS
# --------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport = db.Column(db.String(100))
    slot = db.Column(db.String(100))
    booking_code = db.Column(db.String(50))
    qr_file = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Performance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_code = db.Column(db.String(50))
    metric = db.Column(db.String(100))
    score = db.Column(db.String(100))
    coach_comment = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------------
# HTML TEMPLATE
# --------------------------

BASE_STYLE = """
<style>
body{
font-family:Arial;
background:#f4f4f4;
padding:20px;
}
.container{
background:white;
padding:20px;
border-radius:10px;
max-width:800px;
margin:auto;
}
input,select,textarea{
width:100%;
padding:10px;
margin:8px 0;
}
button{
padding:10px 20px;
background:#0d6efd;
color:white;
border:none;
cursor:pointer;
}
a{
text-decoration:none;
margin-right:10px;
}
.card{
border:1px solid #ddd;
padding:10px;
margin-top:10px;
border-radius:8px;
}
</style>
"""

# --------------------------
# HOME
# --------------------------

@app.route("/")
def home():
    return redirect("/login")

# --------------------------
# REGISTER
# --------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        user = User(
            username=request.form["username"],
            password=request.form["password"],
            role=request.form["role"]
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template_string(BASE_STYLE + """

    <div class="container">

    <h1>SportSync Registration</h1>

    <form method="POST">

    <input name="username" placeholder="Username" required>

    <input type="password"
           name="password"
           placeholder="Password"
           required>

    <select name="role">
        <option value="student">Student</option>
        <option value="coach">Coach</option>
    </select>

    <button type="submit">Register</button>

    </form>

    <a href="/login">Login</a>

    </div>
    """)

# --------------------------
# LOGIN
# --------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()

        if user:
            login_user(user)
            return redirect("/dashboard")

    return render_template_string(BASE_STYLE + """

    <div class="container">

    <h1>SportSync Login</h1>

    <form method="POST">

    <input name="username"
           placeholder="Username"
           required>

    <input type="password"
           name="password"
           placeholder="Password"
           required>

    <button type="submit">
    Login
    </button>

    </form>

    <a href="/register">
    Create Account
    </a>

    </div>
    """)

# --------------------------
# DASHBOARD
# --------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    bookings = Booking.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template_string(BASE_STYLE + """

    <div class="container">

    <h1>SportSync Dashboard</h1>

    <h3>
    Welcome {{user.username}}
    ({{user.role}})
    </h3>

    <a href="/book">Book Slot</a>
    <a href="/performance">Track Performance</a>
    <a href="/progress">View Progress</a>
    <a href="/logout">Logout</a>

    <hr>

    <h2>Your Bookings</h2>

    {% for b in bookings %}

    <div class="card">

    <b>Sport:</b> {{b.sport}} <br>

    <b>Slot:</b> {{b.slot}} <br>

    <b>Booking Code:</b> {{b.booking_code}} <br>

    <img src="/{{b.qr_file}}" width="150">

    </div>

    {% endfor %}

    </div>

    """, user=current_user, bookings=bookings)

# --------------------------
# BOOK SLOT
# --------------------------

@app.route("/book", methods=["GET", "POST"])
@login_required
def book():

    if request.method == "POST":

        sport = request.form["sport"]
        slot = request.form["slot"]

        booking_code = str(uuid.uuid4())[:8]

        os.makedirs("static/qr", exist_ok=True)

        qr_path = f"static/qr/{booking_code}.png"

        qr = qrcode.make(booking_code)
        qr.save(qr_path)

        booking = Booking(
            sport=sport,
            slot=slot,
            booking_code=booking_code,
            qr_file=qr_path,
            user_id=current_user.id
        )

        db.session.add(booking)
        db.session.commit()

        return redirect("/dashboard")

    return render_template_string(BASE_STYLE + """

    <div class="container">

    <h1>Book Sports Facility</h1>

    <form method="POST">

    <select name="sport">

        <option>Basketball</option>
        <option>Football</option>
        <option>Cricket</option>
        <option>Gym</option>
        <option>Swimming</option>
        <option>Table Tennis</option>
        <option>Tennis</option>
        <option>Snooker</option>

    </select>

    <input name="slot"
           placeholder="Example: 4PM-5PM"
           required>

    <button type="submit">
    Book Now
    </button>

    </form>

    <a href="/dashboard">
    Dashboard
    </a>

    </div>
    """)

# --------------------------
# PERFORMANCE ENTRY
# --------------------------

@app.route("/performance", methods=["GET", "POST"])
@login_required
def performance():

    if request.method == "POST":

        record = Performance(
            booking_code=request.form["booking_code"],
            metric=request.form["metric"],
            score=request.form["score"],
            coach_comment=request.form["coach_comment"],
            user_id=current_user.id
        )

        db.session.add(record)
        db.session.commit()

        return redirect("/progress")

    return render_template_string(BASE_STYLE + """

    <div class="container">

    <h1>Performance Tracking</h1>

    <form method="POST">

    <input name="booking_code"
           placeholder="Booking Code"
           required>

    <input name="metric"
           placeholder="Metric"
           required>

    <input name="score"
           placeholder="Score"
           required>

    <textarea
    name="coach_comment"
    placeholder="Coach Feedback">
    </textarea>

    <button type="submit">
    Save Performance
    </button>

    </form>

    </div>
    """)

# --------------------------
# VIEW PROGRESS
# --------------------------

@app.route("/progress")
@login_required
def progress():

    records = Performance.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template_string(BASE_STYLE + """

    <div class="container">

    <h1>Performance Progress</h1>

    <a href="/dashboard">
    Dashboard
    </a>

    {% for r in records %}

    <div class="card">

    <b>Booking Code:</b>
    {{r.booking_code}}<br>

    <b>Metric:</b>
    {{r.metric}}<br>

    <b>Score:</b>
    {{r.score}}<br>

    <b>Coach Comment:</b>
    {{r.coach_comment}}<br>

    </div>

    {% endfor %}

    </div>

    """, records=records)

# --------------------------
# LOGOUT
# --------------------------

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# --------------------------
# START APP
# --------------------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)