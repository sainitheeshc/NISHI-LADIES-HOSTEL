from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=True, nullable=False)
    phone = db.Column(db.String(20), index=True, unique=True, nullable=False)
    room_number = db.Column(db.String(20), nullable=False, default="101")
    monthly_fee = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), default="Active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payments = db.relationship('Payment', backref='student', lazy='dynamic', cascade="all, delete-orphan")

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    month = db.Column(db.String(20), nullable=False) # e.g. "Aug", "Sep"
    year = db.Column(db.Integer, nullable=False)     # e.g. 2026
    amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="Pending") # "Paid" or "Pending"
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Setting(db.Model):
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(256))
