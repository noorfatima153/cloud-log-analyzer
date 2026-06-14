import os
from flask import Flask, render_template, request, redirect, session
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user
)
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


# ---------------- UPLOAD FOLDER ----------------

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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

        if user_data and check_password_hash(
            user_data["password"],
            password
        ):

            user = User()
            user.id = username

            login_user(user, remember=False)

            return redirect("/upload")

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        success = create_user(username, password)

        if success:
            return redirect("/login")

        return render_template(
            "register.html",
            error="Username already exists."
        )

    return render_template("register.html")


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

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    with open(filepath, "r", errors="ignore") as f:
        lines = f.readlines()

    result = run_mapreduce(lines)

    save_results(result)

    save_history(
        file.filename,
        result
    )

    return render_template(
        "dashboard.html",
        data=result
    )


# ---------------- HISTORY ----------------

@app.route("/history")
@login_required
def history():

    rows = get_history()

    return render_template(
        "history.html",
        rows=rows
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
@login_required
def logout():

    logout_user()

    session.clear()

    return redirect("/login")


# ---------------- START APP ----------------

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )