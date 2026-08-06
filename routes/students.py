import os
import re
import pandas as pd
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required
from models import db, Student, Payment, get_setting

students_bp = Blueprint('students', __name__, url_prefix='/students')

FLOOR_OPTIONS = ["1st Floor", "2nd Floor", "3rd Floor"]
HALL_OPTIONS = ["1st Hall", "2nd Hall", "3rd Hall"]

def ensure_july_paid(student):
    """Auto-mark July 2026 as Paid for students with admission month <= 2026-07"""
    if (student.join_month or "2026-07") <= "2026-07":
        existing_p = Payment.query.filter_by(
            student_id=student.id,
            month="Jul",
            year=2026
        ).first()
        if not existing_p:
            pay = Payment(
                student_id=student.id,
                month="Jul",
                year=2026,
                amount=student.monthly_fee,
                payment_method="Cash",
                status="Paid"
            )
            db.session.add(pay)
        else:
            existing_p.status = "Paid"
            if not existing_p.amount or existing_p.amount == 0:
                existing_p.amount = student.monthly_fee
            if not existing_p.payment_method:
                existing_p.payment_method = "Cash"

@students_bp.route('/')
@login_required
def list_students():
    students = Student.query.order_by(Student.name.asc()).all()
    return render_template(
        'students.html', 
        students=students, 
        floor_options=FLOOR_OPTIONS, 
        hall_options=HALL_OPTIONS
    )

@students_bp.route('/add', methods=['POST'])
@login_required
def add_student():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    floor_number = request.form.get('floor_number', '').strip() or "1st Floor"
    room_number = request.form.get('room_number', '').strip() or "1st Hall"
    monthly_fee = float(request.form.get('monthly_fee', 0.0) or 0.0)
    join_month = request.form.get('join_month', '').strip() or "2026-07"
    
    try:
        fee_collection_day = int(request.form.get('fee_collection_day', 2))
        fee_collection_day = max(1, min(31, fee_collection_day))
    except Exception:
        fee_collection_day = 2

    if not name or not phone or not room_number:
        flash('Name, Phone Number, Floor, and Hall are required.', 'error')
        return redirect(url_for('students.list_students'))

    if Student.query.filter_by(phone=phone).first():
        flash('Student with this phone number already exists.', 'error')
        return redirect(url_for('students.list_students'))

    try:
        student = Student(
            name=name, 
            phone=phone, 
            floor_number=floor_number, 
            room_number=room_number, 
            monthly_fee=monthly_fee,
            fee_collection_day=fee_collection_day,
            join_month=join_month, 
            status="Active"
        )
        db.session.add(student)
        db.session.flush() # get student.id

        ensure_july_paid(student)

        db.session.commit()
        flash(f'Student "{name}" added successfully (July 2026 marked as Paid)!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding student: {str(e)}', 'error')

    return redirect(url_for('students.list_students'))

@students_bp.route('/edit/<int:student_id>', methods=['POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    pin = request.form.get('pin', '').strip()
    active_pin = get_setting('admin_pin', '1234')

    if pin != active_pin:
        flash('Invalid Security PIN. Changes were not saved.', 'error')
        return redirect(url_for('students.list_students'))

    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    floor_number = request.form.get('floor_number', '').strip() or "1st Floor"
    room_number = request.form.get('room_number', '').strip() or "1st Hall"
    monthly_fee = float(request.form.get('monthly_fee', 0.0) or 0.0)
    join_month = request.form.get('join_month', '').strip() or student.join_month or "2026-07"
    
    try:
        fee_collection_day = int(request.form.get('fee_collection_day', 2))
        fee_collection_day = max(1, min(31, fee_collection_day))
    except Exception:
        fee_collection_day = student.fee_collection_day or 2

    existing = Student.query.filter(Student.phone == phone, Student.id != student_id).first()
    if existing:
        flash('Another student with this phone number already exists.', 'error')
        return redirect(url_for('students.list_students'))

    try:
        student.name = name
        student.phone = phone
        student.floor_number = floor_number
        student.room_number = room_number
        student.monthly_fee = monthly_fee
        student.fee_collection_day = fee_collection_day
        student.join_month = join_month

        ensure_july_paid(student)

        db.session.commit()
        flash(f'Student "{student.name}" updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating student: {str(e)}', 'error')

    return redirect(url_for('students.list_students'))

@students_bp.route('/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    pin = request.form.get('pin', '').strip()
    active_pin = get_setting('admin_pin', '1234')

    if pin != active_pin:
        flash('Invalid Security PIN. Student was not removed.', 'error')
        return redirect(url_for('students.list_students'))

    try:
        db.session.delete(student)
        db.session.commit()
        flash(f'Student "{student.name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')

    return redirect(url_for('students.list_students'))

@students_bp.route('/delete_all', methods=['POST'])
@login_required
def delete_all_students():
    pin = request.form.get('pin', '').strip()
    active_pin = get_setting('admin_pin', '1234')

    if pin != active_pin:
        flash('Invalid Security PIN. All students were NOT deleted.', 'error')
        return redirect(url_for('students.list_students'))

    try:
        Payment.query.delete()
        num_deleted = Student.query.delete()
        db.session.commit()
        flash(f'All {num_deleted} student records and fee history have been permanently deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting all students: {str(e)}', 'error')

    return redirect(url_for('students.list_students'))

def parse_day_from_val(val):
    if pd.isna(val) or val is None:
        return 2
    val_str = str(val).strip()
    if val_str.isdigit():
        d = int(val_str)
        return max(1, min(31, d))
    match = re.search(r'\b(\d{1,2})\b', val_str)
    if match:
        d = int(match.group(1))
        return max(1, min(31, d))
    return 2

@students_bp.route('/import', methods=['POST'])
@login_required
def import_students():
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('students.list_students'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('students.list_students'))

    filename = file.filename.lower()
    if not (filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.csv')):
        flash('Please upload a CSV or Excel file (.csv, .xlsx).', 'error')
        return redirect(url_for('students.list_students'))

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        count = 0
        for _, row in df.iterrows():
            name_val = row.get('Name') or row.get('Student Name') or row.get('name')
            phone_val = row.get('Phone') or row.get('Phone Number') or row.get('phone')
            fee_val = row.get('Fee') or row.get('Monthly Fee') or row.get('monthly_fee') or row.get('Amount') or 0.0
            
            day_val = (
                row.get('Date of Fee Collections') or 
                row.get('Date of Fee Collection') or 
                row.get('Date of fee collection') or 
                row.get('Fee Collection Date') or 
                row.get('Fee Collection Day') or 
                row.get('Collection Day') or 
                row.get('Day') or 
                row.get('Date') or 2
            )

            floor_val = row.get('Floor') or row.get('Floor Number') or row.get('floor') or "1st Floor"
            room_val = row.get('Hall') or row.get('Room') or row.get('Hall Number') or row.get('room') or "1st Hall"

            name = str(name_val).strip() if pd.notna(name_val) else ''
            phone = str(phone_val).strip() if pd.notna(phone_val) else ''
            floor = str(floor_val).strip() if pd.notna(floor_val) else '1st Floor'
            room = str(room_val).strip() if pd.notna(room_val) else '1st Hall'
            
            try:
                fee = float(fee_val) if pd.notna(fee_val) else 0.0
            except Exception:
                fee = 0.0

            f_day = parse_day_from_val(day_val)

            if '.' in phone:
                phone = phone.split('.')[0]
            if '.' in room:
                room = room.split('.')[0]

            if not name or not phone or name == 'nan' or phone == 'nan':
                continue

            if Student.query.filter_by(phone=phone).first():
                continue

            student = Student(
                name=name, 
                phone=phone, 
                floor_number=floor,
                room_number=room, 
                monthly_fee=fee,
                fee_collection_day=f_day,
                join_month="2026-07", 
                status="Active"
            )
            db.session.add(student)
            db.session.flush()

            ensure_july_paid(student)
            count += 1

        db.session.commit()
        flash(f'Successfully imported {count} students! July 2026 marked as Paid for all imported students.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error importing file: {str(e)}', 'error')
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

    return redirect(url_for('students.list_students'))

@students_bp.route('/export')
@login_required
def export_students():
    format_type = request.args.get('format', 'excel')
    students = Student.query.order_by(Student.name.asc()).all()

    data = [{
        'Name': s.name,
        'Phone': s.phone,
        'Floor': s.floor_number,
        'Hall': s.room_number,
        'Monthly Fee': s.monthly_fee,
        'Fee Collection Day': s.fee_collection_day,
        'Admission Month': s.join_month,
        'Status': s.status
    } for s in students]

    df = pd.DataFrame(data)

    if format_type == 'csv':
        filepath = os.path.join(current_app.config['EXPORT_FOLDER'], 'students.csv')
        df.to_csv(filepath, index=False)
        return send_file(filepath, as_attachment=True, download_name='nishi_students.csv')
    else:
        filepath = os.path.join(current_app.config['EXPORT_FOLDER'], 'students.xlsx')
        df.to_excel(filepath, index=False)
        return send_file(filepath, as_attachment=True, download_name='nishi_students.xlsx')
