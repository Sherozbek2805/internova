from flask import Flask, jsonify, redirect, request, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"


# -------------------
# DATABASE
# -------------------

def get_db():
    conn = sqlite3.connect("internova.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()
    cur = conn.cursor()

    # ensure internships.approved exists
    cur.execute("PRAGMA table_info(internships)")
    cols = {r["name"] for r in cur.fetchall()}

    if "approved" not in cols:
        cur.execute("ALTER TABLE internships ADD COLUMN approved INTEGER DEFAULT 0")

    # ensure companies.verified exists
    cur.execute("PRAGMA table_info(companies)")
    cols = {r["name"] for r in cur.fetchall()}

    if "verified" not in cols:
        cur.execute("ALTER TABLE companies ADD COLUMN verified INTEGER DEFAULT 0")

    # ensure users.banned exists
    cur.execute("PRAGMA table_info(users)")
    cols = {r["name"] for r in cur.fetchall()}

    if "banned" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0")

    # ensure admin exists
    cur.execute("SELECT id FROM users WHERE role='admin'")
    admin = cur.fetchone()

    if not admin:

        password = generate_password_hash("admin123")

        cur.execute("""
        INSERT INTO users (name,email,password,role)
        VALUES (?,?,?,?)
        """,("Admin","admin@internova.local",password,"admin"))

    conn.commit()
    conn.close()


init_db()


# -------------------
# AUTH DECORATORS
# -------------------

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect("/login")

        return f(*args, **kwargs)

    return wrapper


def role_required(role):
    def decorator(f):

        @wraps(f)
        def wrapper(*args, **kwargs):

            if session.get("role") != role:
                return "Unauthorized"

            return f(*args, **kwargs)

        return wrapper

    return decorator


@app.route("/")
def index():
    return render_template("index.html")
# -------------------
# LOGIN
# -------------------

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    ).fetchone()

    conn.close()

    if not user:
        return "User not found"

    if user["role"] != role:
        return "Incorrect role"

    if user["banned"] == 1:
        return "Account banned"

    if not check_password_hash(user["password"], password):
        return "Wrong password"

    session["user_id"] = user["id"]
    session["role"] = user["role"]

    if role == "student":
        return redirect("/student-dashboard")

    if role == "company":
        return redirect("/company-dashboard")

    if role == "admin":
        return redirect("/admin")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/student-dashboard")
@login_required
@role_required("student")
def student_dashboard():
    return render_template("student-dashboard.html")

@app.route("/company-dashboard")
@login_required
@role_required("company")
def company_dashboard():
    conn = get_db()

    company = conn.execute("""
    SELECT id FROM companies
    WHERE user_id=?
    """,(session["user_id"],)).fetchone()

    internships = conn.execute("""
    SELECT * FROM internships
    WHERE company_id=?
    """,(company["id"],)).fetchall()

    conn.close()

    return render_template("company-dashboard.html", internships=internships)

@app.route("/applications")
@login_required
@role_required("company")
def applications():
    conn = get_db()

    company = conn.execute("""
    SELECT id FROM companies
    WHERE user_id=?
    """,(session["user_id"],)).fetchone()

    rows = conn.execute("""
    SELECT applications.*, users.name AS student, internships.title AS internship
    FROM applications
    LEFT JOIN users ON users.id=applications.student_id
    LEFT JOIN internships ON internships.id=applications.internship_id
    WHERE internships.company_id=?
    """,(company["id"],)).fetchall()

    conn.close()

    return render_template("applications.html", applications=rows)

@app.route("/application/<int:id>")
@login_required
@role_required("company")
def application_detail(id):
    conn = get_db()

    company = conn.execute("""
    SELECT id FROM companies
    WHERE user_id=?
    """,(session["user_id"],)).fetchone()

    application = conn.execute("""
    SELECT applications.*, users.name AS student, users.email AS email, users.school AS school, users.skills AS skills, internships.title AS internship
    FROM applications
    LEFT JOIN users ON users.id=applications.student_id
    LEFT JOIN internships ON internships.id=applications.internship_id
    WHERE applications.id=? AND internships.company_id=?
    """,(id,company["id"])).fetchone()

    conn.close()

    if not application:
        return "Application not found"

    return render_template("application-detail.html", application=application)

@app.route("/apply")
@login_required
@role_required("student")
def apply_page():
    conn = get_db()

    internships = conn.execute("""
    SELECT internships.*,companies.name AS company
    FROM internships
    LEFT JOIN companies
    ON companies.id=internships.company_id
    WHERE internships.approved=1
    """).fetchall()

    conn.close()

    return render_template("apply.html", internships=internships)
# -------------------
# SIGNUP
# -------------------
@app.route("/application/company")
@login_required
@role_required("company")
def company_applications():
    return render_template("applicants.html")

@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "GET":
        return render_template("signup.html")

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")

    school = request.form.get("school")
    skills = request.form.get("skills")

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM users WHERE email=?",
        (email,)
    ).fetchone()

    if existing:
        return "Email already registered"

    hashed = generate_password_hash(password)

    cur = conn.execute("""
    INSERT INTO users (name,email,password,role,school,skills)
    VALUES (?,?,?,?,?,?)
    """,(name,email,hashed,role,school,skills))

    user_id = cur.lastrowid

    if role == "company":

        conn.execute("""
        INSERT INTO companies (name,user_id)
        VALUES (?,?)
        """,(name,user_id))

    conn.commit()
    conn.close()

    return redirect("/login")

@app.route("/category")
def category():
    return render_template("category.html")

@app.route("/dashboard")
@login_required
def dashboard():
    role = session.get("role")

    if role == "student":
        return redirect("/student-dashboard")

    if role == "company":
        return redirect("/company-dashboard")

    if role == "admin":
        return redirect("/admin")
# -------------------
# APPLY
# -------------------

@app.route("/apply/<int:internship_id>", methods=["POST"])
@login_required
@role_required("student")
def apply(internship_id):

    conn = get_db()

    internship = conn.execute("""
    SELECT id FROM internships
    WHERE id=? AND approved=1
    """,(internship_id,)).fetchone()

    if not internship:
        return jsonify({"success":False})

    conn.execute("""
    INSERT INTO applications (student_id,internship_id)
    VALUES (?,?)
    """,(session["user_id"],internship_id))

    conn.execute("""
    UPDATE analytics
    SET applications = applications + 1
    WHERE internship_id = ?
    """,(internship_id,))

    conn.commit()
    conn.close()

    return jsonify({"success":True})


# -------------------
# COMPANY POST
# -------------------

@app.route("/post", methods=["GET","POST"])
@login_required
@role_required("company")
def post():

    if request.method == "GET":
        return render_template("post-internship.html")

    title = request.form.get("title")
    description = request.form.get("description")
    location = request.form.get("location")
    duration = request.form.get("duration")
    deadline = request.form.get("deadline")

    conn = get_db()

    company = conn.execute("""
    SELECT id,verified
    FROM companies
    WHERE user_id=?
    """,(session["user_id"],)).fetchone()

    if company["verified"] == 0:
        return "Company must be verified by admin first"

    cur = conn.execute("""
    INSERT INTO internships
    (title,description,company_id,location,duration,deadline)
    VALUES (?,?,?,?,?,?)
    """,(title,description,company["id"],location,duration,deadline))

    internship_id = cur.lastrowid

    conn.execute("""
    INSERT INTO analytics (internship_id)
    VALUES (?)
    """,(internship_id,))

    conn.commit()
    conn.close()

    return redirect("/company-dashboard")


# -------------------
# VIEW TRACKING
# -------------------

@app.route("/api/internship/<int:id>/view")
def track_view(id):

    conn = get_db()

    conn.execute("""
    UPDATE analytics
    SET views = views + 1
    WHERE internship_id = ?
    """,(id,))

    conn.commit()
    conn.close()

    return jsonify({"success":True})


# -------------------
# DISCOVER
# -------------------

@app.route("/discover")
def discover():

    conn = get_db()

    rows = conn.execute("""
    SELECT internships.*,companies.name AS company
    FROM internships
    LEFT JOIN companies
    ON companies.id=internships.company_id
    WHERE internships.approved=1
    """).fetchall()

    conn.close()

    return render_template("internships.html", internships=rows)


# -------------------
# ADMIN
# -------------------

@app.route("/admin")
@login_required
@role_required("admin")
def admin():

    conn = get_db()

    users = conn.execute("SELECT * FROM users").fetchall()

    companies = conn.execute("""
    SELECT * FROM companies
    """).fetchall()

    internships = conn.execute("""
    SELECT internships.*,companies.name AS company
    FROM internships
    LEFT JOIN companies
    ON companies.id=internships.company_id
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        companies=companies,
        internships=internships
    )

@app.route("/companies")
def companies():
    conn = get_db()

    rows = conn.execute("""
    SELECT * FROM companies
    """).fetchall()

    conn.close()

    return render_template("companies.html", companies=rows)

@app.route("/admin/verify-company/<int:id>", methods=["POST"])
@login_required
@role_required("admin")
def verify_company(id):

    conn = get_db()

    conn.execute("""
    UPDATE companies
    SET verified = 1
    WHERE id=?
    """,(id,))

    conn.commit()
    conn.close()

    return redirect("/admin")


# -------------------
# RUN
# -------------------

if __name__ == "__main__":
    app.run()