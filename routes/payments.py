import os
import pandas as pd
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, current_app, send_file, redirect, url_for
from flask_login import login_required
from models import db, Student, Payment

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/')
@login_required
def index():
    students = Student.query.order_by(Student.name.asc()).all()
    # Fetch all payment records into a lookup dictionary for quick template access
    payments_list = Payment.query.all()
    payment_map = {}
    for p in payments_list:
        key = f"{p.student_id}_{p.month}_{p.year}"
        payment_map[key] = p.status
        
    return render_template('fee_payments.html', students=students, payment_map=payment_map)

@payments_bp.route('/update_status', methods=['POST'])
@login_required
def update_status():
    data = request.get_json() or {}
    student_id = data.get('student_id')
    month = data.get('month')
    year = data.get('year', datetime.now().year)
    status = data.get('status') # "Paid" or "Pending"
    amount = float(data.get('amount', 0.0))
    
    if not student_id or not month or not status:
        return jsonify({'success': False, 'error': 'Invalid arguments'}), 400
        
    try:
        payment = Payment.query.filter_by(student_id=student_id, month=month, year=year).first()
        if not payment:
            payment = Payment(student_id=student_id, month=month, year=year, status=status, amount=amount)
            db.session.add(payment)
        else:
            payment.status = status
            if amount > 0:
                payment.amount = amount
                
        db.session.commit()
        return jsonify({'success': True, 'status': payment.status})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/export')
@login_required
def export_payments():
    format_type = request.args.get('format', 'excel')
    students = Student.query.order_by(Student.name.asc()).all()
    payments = Payment.query.all()
    
    pay_map = {f"{p.student_id}_{p.month}_{p.year}": p.status for p in payments}
    
    # We can output a clean matrix table
    current_year = datetime.now().year
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    data = []
    for s in students:
        row = {
            'Name': s.name,
            'Room': s.room_number,
            'Phone': s.phone
        }
        for m in months:
            status = pay_map.get(f"{s.id}_{m}_{current_year}", "Pending")
            row[f"{m} {current_year}"] = status
        data.append(row)
        
    df = pd.DataFrame(data)
    
    if format_type == 'csv':
        filepath = os.path.join(current_app.config['EXPORT_FOLDER'], 'fee_payments.csv')
        df.to_csv(filepath, index=False)
        return send_file(filepath, as_attachment=True, download_name='nishi_fee_payments.csv')
    else:
        filepath = os.path.join(current_app.config['EXPORT_FOLDER'], 'fee_payments.xlsx')
        df.to_excel(filepath, index=False)
        return send_file(filepath, as_attachment=True, download_name='nishi_fee_payments.xlsx')
