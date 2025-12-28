from datetime import datetime
from flask_login import UserMixin
from extensions import db

# -------------------------
# USER MODEL (PostgreSQL-safe)
# -------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"   # 👈 IMPORTANT: 'user' nahi, 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    complaints = db.relationship("Complaint", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

# -------------------------
# COMPLAINT MODEL
# -------------------------
class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="Pending")

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolve_note = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Complaint {self.id} - {self.status}>"



