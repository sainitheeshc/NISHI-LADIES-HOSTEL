import os
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required
from models import db, Student

students_bp = Blueprint('students', __name__, url_prefix='/students')

@students_bp.route('/')
@login_required
def list_students():
    students = Student.query.order_by(Student.name.asc()).all()
    return render_template('students.html', students=students)

@students_bp.route('/add', methods=['POST'])
@login_required
def add_student():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    room_number = request.form.get('room_number', '').strip()
    
    if not name or not phone or not room_number:
        flash('Name, Phone Number, and Room Number are required.', 'error')
        return redirect(url_for('students.list_students'))
        
    if Student.query.filter_by(phone=phone).first():
        flash('Student with this phone number already exists.', 'error')
        return redirect(url_for('students.list_students'))
        
    try:
        student = Student(name=name, phone=phone, room_number=room_number, status="Active")
        db.session.add(student)
        db.session.commit()
        flash('Student added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding student: {str(e)}', 'error')
        
    return redirect(url_for('students.list_students'))

@students_bp.route('/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    try:
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
    return redirect(url_for('students.list_students'))

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
            # Flexible column header mapping
            name_val = row.get('Name') or row.get('Student Name') or row.get('name')
            phone_val = row.get('Phone') or row.get('Phone Number') or row.get('phone')
            room_val = row.get('Room') or row.get('Room Number') or row.get('room') or row.get('room_number') or "101"
            
            name = str(name_val).strip() if pd.notna(name_val) else ''
            phone = str(phone_val).strip() if pd.notna(phone_val) else ''
            room = str(room_val).strip() if pd.notna(room_val) else '101'
            
            if '.' in phone:
                phone = phone.split('.')[0]
            if '.' in room:
                room = room.split('.')[0]
                
            if not name or not phone or name == 'nan' or phone == 'nan':
                continue
                
            if Student.query.filter_by(phone=phone).first():
                continue
                
            student = Student(name=name, phone=phone, room_number=room, status="Active")
            db.session.add(student)
            count += 1
            
        db.session.commit()
        flash(f'Successfully imported {count} students!', 'success')
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
        'Room': s.room_number,
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
