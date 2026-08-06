from flask import Flask, render_template, redirect, url_for, flash, request
from config import Config
from models import db, User, Student, Payment
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload/export directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Register Blueprints
from routes.students import students_bp
app.register_blueprint(students_bp)

from routes.payments import payments_bp
app.register_blueprint(payments_bp)

from routes.reports import reports_bp
app.register_blueprint(reports_bp)

from routes.settings import settings_bp
app.register_blueprint(settings_bp)

from routes.notifications import notifications_bp, get_due_notifications
app.register_blueprint(notifications_bp)

@app.context_processor
def inject_notifications_count():
    if current_user.is_authenticated:
        try:
            reminders = get_due_notifications()
            return dict(notification_count=len(reminders))
        except Exception:
            return dict(notification_count=0)
    return dict(notification_count=0)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid Username or Password', 'error')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now()
    current_month = today.strftime('%b') # e.g. "Aug"
    current_year = today.year
    current_month_str = today.strftime('%Y-%m') # e.g. "2026-08"
    
    # Active students count
    active_students = Student.query.filter_by(status='Active').all()
    total_students = len(active_students)
    
    # Calculate Monthly Collection (sum of amounts for paid status in current month)
    paid_payments = Payment.query.filter_by(month=current_month, year=current_year, status='Paid').all()
    monthly_collection = sum(p.amount for p in paid_payments)
    
    # Calculate Pending Students (active students whose join_month <= current_month_str and haven't paid)
    paid_student_ids = {p.student_id for p in paid_payments}
    pending_students = 0
    for s in active_students:
        s_join = s.join_month or "2026-01"
        if s_join <= current_month_str and s.id not in paid_student_ids:
            pending_students += 1
        
    return render_template('dashboard.html',
                           total_students=total_students,
                           monthly_collection=monthly_collection,
                           pending_students=pending_students,
                           current_month=current_month,
                           current_year=current_year)

def create_admin():
    with app.app_context():
        db.create_all()
        if User.query.filter_by(username='admin').first() is None:
            user = User(username='admin')
            user.set_password('admin123')
            db.session.add(user)
            db.session.commit()

if __name__ == '__main__':
    create_admin()
    app.run(debug=True)
