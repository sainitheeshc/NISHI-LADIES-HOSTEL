from datetime import datetime, date
import calendar
from flask import Blueprint, render_template
from flask_login import login_required
from models import db, Student, Payment

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def get_due_notifications():
    today = date.today()
    current_year = today.year
    current_month_idx = today.month # 1-12
    current_month_str = MONTH_NAMES[current_month_idx - 1]

    students = Student.query.filter_by(status='Active').order_by(Student.name.asc()).all()
    notifications = []

    for student in students:
        fee_day = student.fee_collection_day or 2
        
        # Check current month payment
        curr_payment = Payment.query.filter_by(
            student_id=student.id, 
            month=current_month_str, 
            year=current_year, 
            status='Paid'
        ).first()

        if curr_payment:
            # Current month is PAID -> Check NEXT month due date
            next_month_idx = current_month_idx + 1
            next_year = current_year
            if next_month_idx > 12:
                next_month_idx = 1
                next_year += 1

            max_days = calendar.monthrange(next_year, next_month_idx)[1]
            due_day = min(fee_day, max_days)
            due_date = date(next_year, next_month_idx, due_day)
            target_month_name = MONTH_NAMES[next_month_idx - 1]

            delta_days = (due_date - today).days

            if delta_days <= 10:
                notifications.append({
                    'id': student.id,
                    'name': student.name,
                    'phone': student.phone,
                    'floor': student.floor_number or '1st Floor',
                    'room': student.room_number or '1st Hall',
                    'due_date': due_date.strftime('%d %b %Y'),
                    'target_month': f"{target_month_name} {next_year}",
                    'status_text': f"Due in {delta_days} day(s)",
                    'badge_color': "warning",
                    'days_left': delta_days
                })

        else:
            # Current month is PENDING -> Check CURRENT month due date
            max_days = calendar.monthrange(current_year, current_month_idx)[1]
            due_day = min(fee_day, max_days)
            due_date = date(current_year, current_month_idx, due_day)

            delta_days = (due_date - today).days

            if delta_days > 0:
                if delta_days <= 10:
                    status_text = f"Due in {delta_days} day(s)"
                    badge_color = "warning"
                else:
                    status_text = f"Due on {due_date.strftime('%d %b')}"
                    badge_color = "info"
            elif delta_days == 0:
                status_text = "Due Today!"
                badge_color = "danger"
            else:
                status_text = f"Overdue by {abs(delta_days)} day(s)"
                badge_color = "danger"

            # Always notify if current month is pending & due date is within 10 days or overdue
            if delta_days <= 10:
                notifications.append({
                    'id': student.id,
                    'name': student.name,
                    'phone': student.phone,
                    'floor': student.floor_number or '1st Floor',
                    'room': student.room_number or '1st Hall',
                    'due_date': due_date.strftime('%d %b %Y'),
                    'target_month': f"{current_month_str} {current_year}",
                    'status_text': status_text,
                    'badge_color': badge_color,
                    'days_left': delta_days
                })

    notifications.sort(key=lambda x: x['days_left'])
    return notifications

@notifications_bp.route('/')
@login_required
def index():
    notifications = get_due_notifications()
    return render_template('notifications.html', notifications=notifications)
