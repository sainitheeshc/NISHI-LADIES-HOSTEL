import os
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required
from models import db, Student, Payment

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    return render_template('reports.html')

@reports_bp.route('/import', methods=['POST'])
@login_required
def import_data():
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('reports.index'))
        
    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('reports.index'))
        
    filename = file.filename.lower()
    if not (filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.csv')):
        flash('Please upload a valid CSV or Excel file.', 'error')
        return redirect(url_for('reports.index'))
        
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
            room_val = row.get('Room') or row.get('Room Number') or row.get('room') or '101'
            
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
        flash(f'Import completed successfully! {count} new student records added.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error importing file: {str(e)}', 'error')
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
            
    return redirect(url_for('reports.index'))

@reports_bp.route('/download')
@login_required
def download_data():
    file_format = request.args.get('format', 'excel')
    students = Student.query.order_by(Student.name.asc()).all()
    
    data = [{
        'Student Name': s.name,
        'Phone Number': s.phone,
        'Room Number': s.room_number,
        'Status': s.status
    } for s in students]
    
    df = pd.DataFrame(data)
    
    if file_format == 'csv':
        filepath = os.path.join(current_app.config['EXPORT_FOLDER'], 'nishi_hostel_data.csv')
        df.to_csv(filepath, index=False)
        return send_file(filepath, as_attachment=True, download_name='nishi_hostel_data.csv')
    else:
        filepath = os.path.join(current_app.config['EXPORT_FOLDER'], 'nishi_hostel_data.xlsx')
        df.to_excel(filepath, index=False)
        return send_file(filepath, as_attachment=True, download_name='nishi_hostel_data.xlsx')
