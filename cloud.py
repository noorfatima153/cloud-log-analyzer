from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import os
from mapreduce import run_mapreduce
from database import save_results, save_history, cur

app = Flask(__name__)
app.secret_key = "my_secret_key"

# ---------------- LOGIN SETUP ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "home"

class User(UserMixin):
    pass

users = {
    "admin": "admin123"
}

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

# ---------------- UPLOAD FOLDER ----------------
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- LOGIN PAGE ----------------
@app.route("/")
def home():
    return render_template("login.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    if username in users and users[username] == password:
        user = User()
        user.id = username
        login_user(user)
        return redirect("/upload")

    return "Invalid login"

# ---------------- UPLOAD PAGE ----------------
@app.route("/upload")
@login_required
def upload_page():
    return render_template("upload.html")

# ---------------- FILE UPLOAD ----------------
@app.route("/upload-file", methods=["POST"])
@login_required
def upload_file():
    file = request.files["file"]

    if file.filename == "":
        return "No file selected"

    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(path)

    with open(path, "r", errors="ignore") as f:
        lines = f.readlines()

    # MapReduce
    result = run_mapreduce(lines)

    # Save to DB
    save_results(result)
    save_history(file.filename, result)

    return render_template("dashboard.html", data=result)

# ---------------- HISTORY PAGE ----------------
@app.route("/history")
@login_required
def history():
    cur.execute("SELECT filename, analyzed_at, result FROM analysis_history ORDER BY analyzed_at DESC")
    rows = cur.fetchall()

    return render_template("history.html", rows=rows)

# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)