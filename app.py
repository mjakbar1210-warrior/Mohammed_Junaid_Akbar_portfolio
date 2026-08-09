import os
import sqlite3
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "portfolio.db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "projects"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deploying")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me-now")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            year TEXT,
            description TEXT NOT NULL,
            technologies TEXT,
            github TEXT,
            image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    if count == 0:
        seed = [
            ("Line Follower Robot","ROBOTICS","2026",
             "Arduino-based autonomous line following robot using two IR sensors and an L298N motor driver.",
             "Arduino, C++, IR Sensors, L298N","https://github.com/mjakbar1210-warrior",""),
            ("CNC 2D Plotter","CNC / MOTION CONTROL","2026",
             "Computer-controlled plotting machine using Arduino, GRBL concepts and stepper motor motion.",
             "Arduino, GRBL, Stepper Motors, CNC","https://github.com/mjakbar1210-warrior",""),
            ("AI Examination Evaluator","AI / MACHINE LEARNING","2026",
             "AI-based examination paper evaluation system using NLP and machine learning with Django and MySQL.",
             "Python, Django, NLP, ML, MySQL","https://github.com/mjakbar1210-warrior","")
        ]
        conn.executemany("""INSERT INTO projects
            (title,category,year,description,technologies,github,image)
            VALUES (?,?,?,?,?,?,?)""", seed)
    conn.commit()
    conn.close()

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

def allowed(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_globals():
    return {"github": "https://github.com/mjakbar1210-warrior",
            "linkedin": "https://www.linkedin.com/in/mohammed-junaid-akbar"}

@app.route("/")
def index():
    conn = db()
    projects = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", projects=projects)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","")
        password = request.form.get("password","")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session["admin"] = True
            return redirect(request.args.get("next") or url_for("admin"))
        flash("Invalid admin credentials.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin")
@admin_required
def admin():
    conn = db()
    projects = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", projects=projects)

@app.route("/admin/add", methods=["GET","POST"])
@admin_required
def add_project():
    if request.method == "POST":
        title = request.form.get("title","").strip()
        category = request.form.get("category","").strip()
        year = request.form.get("year","").strip()
        description = request.form.get("description","").strip()
        technologies = request.form.get("technologies","").strip()
        github_url = request.form.get("github","").strip()
        image = request.files.get("image")
        if not title or not category or not description:
            flash("Title, category and description are required.", "error")
            return render_template("project_form.html", project=None)
        image_name = ""
        if image and image.filename:
            if not allowed(image.filename):
                flash("Allowed images: PNG, JPG, JPEG, WEBP, GIF.", "error")
                return render_template("project_form.html", project=None)
            safe = secure_filename(image.filename)
            image_name = f"{os.urandom(8).hex()}_{safe}"
            image.save(UPLOAD_DIR / image_name)
        conn = db()
        conn.execute("""INSERT INTO projects
            (title,category,year,description,technologies,github,image)
            VALUES (?,?,?,?,?,?,?)""",
            (title,category,year,description,technologies,github_url,image_name))
        conn.commit(); conn.close()
        flash("Project added successfully.", "success")
        return redirect(url_for("admin"))
    return render_template("project_form.html", project=None)

@app.route("/admin/edit/<int:project_id>", methods=["GET","POST"])
@admin_required
def edit_project(project_id):
    conn = db()
    project = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not project:
        conn.close(); abort(404)
    if request.method == "POST":
        title = request.form.get("title","").strip()
        category = request.form.get("category","").strip()
        year = request.form.get("year","").strip()
        description = request.form.get("description","").strip()
        technologies = request.form.get("technologies","").strip()
        github_url = request.form.get("github","").strip()
        image_name = project["image"]
        image = request.files.get("image")
        if image and image.filename:
            if not allowed(image.filename):
                flash("Invalid image format.", "error")
                conn.close()
                return render_template("project_form.html", project=project)
            if image_name:
                old = UPLOAD_DIR / image_name
                if old.exists(): old.unlink()
            safe = secure_filename(image.filename)
            image_name = f"{os.urandom(8).hex()}_{safe}"
            image.save(UPLOAD_DIR / image_name)
        conn.execute("""UPDATE projects SET title=?,category=?,year=?,description=?,
                        technologies=?,github=?,image=? WHERE id=?""",
                     (title,category,year,description,technologies,github_url,image_name,project_id))
        conn.commit(); conn.close()
        flash("Project updated.", "success")
        return redirect(url_for("admin"))
    conn.close()
    return render_template("project_form.html", project=project)

@app.post("/admin/delete/<int:project_id>")
@admin_required
def delete_project(project_id):
    conn = db()
    project = conn.execute("SELECT image FROM projects WHERE id=?", (project_id,)).fetchone()
    if project and project["image"]:
        img = UPLOAD_DIR / project["image"]
        if img.exists(): img.unlink()
    conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit(); conn.close()
    flash("Project deleted.", "success")
    return redirect(url_for("admin"))

@app.route("/health")
def health():
    return {"status":"ok"}

init_db()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
