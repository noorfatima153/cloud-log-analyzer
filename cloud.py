import os
import json
from flask import Flask, render_template, request, redirect, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import check_password_hash

from mapreduce import run_mapreduce
from database import (
    save_results,
    save_history,
    get_history,
    get_user,
    create_user,
    init_db
)

app = Flask(__name__)
app.secret_key = "my_secret_key"

# ---------------- LOGIN SETUP ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

# ---------------- INIT DB ----------------
init_db()

# ---------------- HOME ----------------
@app.route("/")
def index():
    return redirect("/login")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_data = get_user(username)

        if user_data and check_password_hash(user_data["password"], password):
            user = User()
            user.id = username
            login_user(user)
            return redirect("/upload")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# ---------------- REGISTER (FIXED - NO CRASH) ----------------
@app.route("/register", methods=["POST"])
def register():
    try:
        username = request.form["username"]
        password = request.form["password"]

        success = create_user(username, password)

        if success:
            user = User()
            user.id = username
            login_user(user)
            return redirect("/upload")

        return render_template("login.html", error="Username already exists.")

    except Exception as e:
        print("REGISTER ERROR:", e)
        return render_template("login.html", error="Server error")

# ---------------- UPLOAD ----------------
@app.route("/upload")
@login_required
def upload_page():
    return render_template("upload.html")

@app.route("/upload-file", methods=["POST"])
@login_required
def upload_file():
    file = request.files["file"]

    if file.filename == "":
        return "No file selected"

    path = os.path.join("uploads", file.filename)
    file.save(path)

    with open(path, "r", errors="ignore") as f:
        lines = f.readlines()

    result = run_mapreduce(lines)

    save_results(result)
    save_history(file.filename, result)

    return render_template("dashboard.html", data=result)

# ---------------- HISTORY ----------------
@app.route("/history")
@login_required
def history():
    rows = get_history()
    return render_template("history.html", rows=rows)

# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)