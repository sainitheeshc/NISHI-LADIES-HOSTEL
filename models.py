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
    floor_number = db.Column(db.String(50), nullable=False, default="1st Floor")
    room_number = db.Column(db.String(50), nullable=False, default="1st Hall") # Room / Hall
    fee_collection_day = db.Column(db.Integer, nullable=False, default=2)     # Day of month (1-31)
    join_month = db.Column(db.String(20), nullable=False, default="2026-07")   # Base reference month YYYY-MM
    monthly_fee = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), default="Active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payments = db.relationship('Payment', backref='student', lazy='dynamic', cascade="all, delete-orphan")

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    month = db.Column(db.String(20), nullable=False) # e.g. "Jul", "Aug" or "2026-07"
    year = db.Column(db.Integer, nullable=False)     # e.g. 2026
    amount = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(20), nullable=True) # "PhonePe", "Cash"
    status = db.Column(db.String(20), default="Pending") # "Paid", "Pending", "N/A"
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Setting(db.Model):
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(256))

def get_setting(key, default_value=""):
    setting = Setting.query.get(key)
    return setting.value if setting else default_value

def set_setting(key, value):
    setting = Setting.query.get(key)
    if not setting:
        setting = Setting(key=key, value=str(value))
        db.session.add(setting)
    else:
        setting.value = str(value)
    db.session.commit()
