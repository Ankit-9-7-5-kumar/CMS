from flask import Flask, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    login_user, logout_user, login_required, current_user
)
from datetime import datetime

from config import Config
from extensions import db, login_manager
from models import User, Complaint
from forms import RegisterForm, LoginForm, ComplaintForm

app = Flask(__name__)
app.config.from_object(Config)

# init extensions
db.init_app(app)
login_manager.init_app(app)

# -------------------------
# LOGIN MANAGER
# -------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------------
# HELPERS
# -------------------------
def admin_required():
    if not current_user.is_admin:
        flash("Admin access only!", "danger")
        return False
    return True


# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return render_template("home.html")


# -------------------------
# REGISTER
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        # username check
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists", "danger")
            return redirect(url_for("register"))

        # email check
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("login"))

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            is_admin=False
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Login successful", "success")
            
            # AGAR ADMIN HAI TOH ADMIN DASHBOARD PAR BHEJO
            if user.is_admin:
                return redirect(url_for("admin_dashboard"))
            
            # AGAR NORMAL USER HAI TOH USER DASHBOARD PAR
            return redirect(url_for("dashboard"))

        flash("Invalid email or password", "danger")
    return render_template("login.html", form=form)


# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))


# -------------------------
# USER DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    # 1. Current user ki saari complaints database se ek saath le aao
    user_complaints = Complaint.query.filter_by(user_id=current_user.id).all()
    
    # 2. Total count (List ki length)
    total = len(user_complaints)
    
    # 3. Alag-alag status count karo (Space aur Capital letters ka issue khatam karne ke liye)
    # Hum .strip() use kar rahe hain taaki extra space hat jaye
    pending = len([c for c in user_complaints if c.status.strip() == "Pending"])
    in_progress = len([c for c in user_complaints if c.status.strip() == "In Progress"])
    resolved = len([c for c in user_complaints if c.status.strip() == "Resolved"])

    # 4. Latest complaint (Dashboard ke liye)
    latest = Complaint.query.filter_by(user_id=current_user.id)\
                     .order_by(Complaint.created_at.desc()).first()

    return render_template(
        "dashboard.html",
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved,
        latest=latest
    )

# -------------------------
# CREATE COMPLAINT
# -------------------------
@app.route("/complaint/new", methods=["GET", "POST"])
@login_required
def new_complaint():
    form = ComplaintForm()

    if form.validate_on_submit():
        complaint = Complaint(
            title=form.title.data,
            description=form.description.data,
            status="Pending",
            user_id=current_user.id
        )
        db.session.add(complaint)
        db.session.commit()

        flash("Complaint submitted successfully", "success")
        return redirect(url_for("my_complaints"))

    return render_template("new_complaint.html", form=form)


# -------------------------
# USER COMPLAINT LIST
# -------------------------
@app.route("/complaints")
@login_required
def my_complaints():
    complaints = Complaint.query.filter_by(
        user_id=current_user.id
    ).order_by(Complaint.created_at.desc()).all()

    return render_template("complaints.html", complaints=complaints)


# -------------------------
# EDIT COMPLAINT
# -------------------------
@app.route("/complaint/<int:complaint_id>/edit", methods=["GET", "POST"])
@login_required
def edit_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.user_id != current_user.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("my_complaints"))

    form = ComplaintForm(
        title=complaint.title,
        description=complaint.description
    )

    if form.validate_on_submit():
        complaint.title = form.title.data
        complaint.description = form.description.data
        db.session.commit()

        flash("Complaint updated", "success")
        return redirect(url_for("my_complaints"))

    return render_template("edit_complaint.html", form=form)


# -------------------------
# DELETE COMPLAINT
# -------------------------
@app.route("/complaint/<int:complaint_id>/delete")
@login_required
def delete_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.user_id != current_user.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("my_complaints"))

    db.session.delete(complaint)
    db.session.commit()

    flash("Complaint deleted", "success")
    return redirect(url_for("my_complaints"))


# -------------------------
# ADMIN DASHBOARD
# -------------------------
@app.route("/admin")
@login_required
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("home"))

    total_users = User.query.count()
    total_complaints = Complaint.query.count()
    pending = Complaint.query.filter_by(status="Pending").count()
    in_progress = Complaint.query.filter_by(status="In Progress").count()
    resolved = Complaint.query.filter_by(status="Resolved").count()

    complaints = Complaint.query.order_by(
        Complaint.status != "Resolved"
    ).all()

    return render_template(
        "admin_dashboard.html",
        complaints=complaints,
        total_users=total_users,
        total_complaints=total_complaints,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved
    )


# -------------------------
# ADMIN → IN PROGRESS
# -------------------------
@app.route("/admin/complaint/<int:complaint_id>/progress")
@login_required
def mark_in_progress(complaint_id):
    if not admin_required():
        return redirect(url_for("home"))

    complaint = Complaint.query.get_or_404(complaint_id)
    complaint.status = "In Progress"
    db.session.commit()

    flash("Marked as In Progress", "success")
    return redirect(url_for("admin_dashboard"))


# -------------------------
# ADMIN → RESOLVE WITH NOTE
# -------------------------
@app.route("/admin/complaint/<int:complaint_id>/resolve", methods=["POST"])
@login_required
def resolve_complaint(complaint_id):
    if not admin_required():
        return redirect(url_for("home"))

    complaint = Complaint.query.get_or_404(complaint_id)
    complaint.status = "Resolved"
    complaint.resolve_note = request.form.get("note")
    complaint.resolved_at = datetime.utcnow()

    db.session.commit()
    flash("Complaint resolved", "success")
    return redirect(url_for("admin_dashboard"))


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)




