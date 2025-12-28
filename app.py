from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

from config import Config
from extensions import db, login_manager
from models import User, Complaint
from forms import RegisterForm, LoginForm, ComplaintForm

app = Flask(__name__)
app.config.from_object(Config)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///local.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
login_manager.init_app(app)

# ---------------- LOGIN MANAGER ----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already exists", "danger")
            return redirect(url_for("login"))

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()

        flash("Registration successful", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)

            if user.is_admin:
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("dashboard"))

        flash("Invalid credentials", "danger")

    return render_template("login.html", form=form)

# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------- USER DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    complaints = Complaint.query.filter_by(user_id=current_user.id).all()

    total = len(complaints)
    pending = len([c for c in complaints if c.status == "Pending"])
    in_progress = len([c for c in complaints if c.status == "In Progress"])
    resolved = len([c for c in complaints if c.status == "Resolved"])

    return render_template(
        "dashboard.html",
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved
    )

# ---------------- NEW COMPLAINT ----------------
@app.route("/complaint/new", methods=["GET", "POST"])
@login_required
def new_complaint():
    form = ComplaintForm()

    if form.validate_on_submit():
        complaint = Complaint(
            title=form.title.data,
            description=form.description.data,
            user_id=current_user.id
        )
        db.session.add(complaint)
        db.session.commit()

        flash("Complaint submitted", "success")
        return redirect(url_for("my_complaints"))

    return render_template("new_complaint.html", form=form)

# ---------------- MY COMPLAINTS ----------------
@app.route("/complaints")
@login_required
def my_complaints():
    complaints = Complaint.query.filter_by(
        user_id=current_user.id
    ).order_by(Complaint.created_at.desc()).all()

    return render_template("complaints.html", complaints=complaints)

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Admin only", "danger")
        return redirect(url_for("dashboard"))

    return render_template(
        "admin_dashboard.html",
        complaints=Complaint.query.order_by(Complaint.created_at.desc()).all(),
        total_users=User.query.count(),
        total_complaints=Complaint.query.count(),
        pending=Complaint.query.filter_by(status="Pending").count(),
        in_progress=Complaint.query.filter_by(status="In Progress").count(),
        resolved=Complaint.query.filter_by(status="Resolved").count()
    )

# ---------------- ADMIN ACTIONS ----------------
@app.route("/admin/complaint/<int:id>/progress")
@login_required
def mark_in_progress(id):
    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    c = Complaint.query.get_or_404(id)
    c.status = "In Progress"
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/complaint/<int:id>/resolve", methods=["POST"])
@login_required
def resolve_complaint(id):
    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    c = Complaint.query.get_or_404(id)
    c.status = "Resolved"
    c.resolve_note = request.form.get("note")
    c.resolved_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/complaint/<int:id>/in-progress")
@login_required
def mark_in_progress(id):
    if not current_user.is_admin:
        abort(403)

    complaint = Complaint.query.get_or_404(id)
    complaint.status = "In Progress"
    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/complaint/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_complaint(id):
    complaint = Complaint.query.get_or_404(id)

    if complaint.user_id != current_user.id:
        abort(403)

    form = ComplaintForm(obj=complaint)
    if form.validate_on_submit():
        complaint.title = form.title.data
        complaint.description = form.description.data
        db.session.commit()
        return redirect(url_for("my_complaints"))

    return render_template("edit_complaint.html", form=form)


@app.route("/complaint/<int:id>/delete")
@login_required
def delete_complaint(id):
    complaint = Complaint.query.get_or_404(id)

    if complaint.user_id != current_user.id:
        abort(403)

    db.session.delete(complaint)
    db.session.commit()
    return redirect(url_for("my_complaints"))




