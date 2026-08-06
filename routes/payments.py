import os
import pandas as pd
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import login_required
from models import db, Student, Payment, get_setting

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

FLOOR_OPTIONS = ["1st Floor", "2nd Floor", "3rd Floor"]
HALL_OPTIONS = ["1st Hall", "2nd Hall", "3rd Hall"]

@payments_bp.route('/')
@login_required
def index():
    selected_floor = request.args.get('floor', '').strip()
    selected_room = request.args.get('room', '').strip()

    query = Student.query.order_by(Student.name.asc())
    if selected_floor and selected_floor != 'All':
        query = query.filter_by(floor_number=selected_floor)
    if selected_room and selected_room != 'All':
        query = query.filter_by(room_number=selected_room)

    students = query.all()

    payments_list = Payment.query.all()
    
    # Build lookup dictionary for quick template access
    payment_map = {}
    for p in payments_list:
        key = f"{p.student_id}_{p.month}_{p.year}"
        payment_map[key] = {
            'status': p.status,
            'amount': p.amount,
            'method': p.payment_method or ''
        }
        
    return render_template(
        'fee_payments.html', 
        students=students, 
        floors=FLOOR_OPTIONS, 
        rooms=HALL_OPTIONS, 
        selected_floor=selected_floor, 
        selected_room=selected_room,
        payment_map=payment_map,
        current_year=datetime.now().year
    )

@payments_bp.route('/update_status', methods=['POST'])
@login_required
def update_status():
    data = request.get_json() or {}
    student_id = data.get('student_id')
    month = data.get('month')
    year = int(data.get('year', datetime.now().year))
    status = data.get('status', 'Paid') # "Paid" or "Pending"
    amount = float(data.get('amount', 0.0))
    method = data.get('method', '')
    pin = str(data.get('pin', '')).strip()

    active_pin = get_setting('admin_pin', '1234')

    if pin != active_pin:
        return jsonify({'success': False, 'error': 'Invalid Security PIN'}), 400

    if not student_id or not month:
        return jsonify({'success': False, 'error': 'Invalid arguments'}), 400

    try:
        payment = Payment.query.filter_by(student_id=student_id, month=month, year=year).first()
        if not payment:
            payment = Payment(
                student_id=student_id, 
                month=month, 
                year=year, 
                status=status, 
                amount=amount,
                payment_method=method
            )
            db.session.add(payment)
        else:
            payment.status = status
            payment.amount = amount
            payment.payment_method = method
                
        db.session.commit()
        return jsonify({
            'success': True, 
            'status': payment.status,
            'amount': payment.amount,
            'method': payment.payment_method
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/export_monthly/<month>')
@login_required
def export_monthly(month):
    students = Student.query.order_by(Student.name.asc()).all()

    try:
        if '-' in month:
            dt = datetime.strptime(month, '%Y-%m')
            month_name = dt.strftime('%b')
            year_num = dt.year
            month_str_code = dt.strftime('%Y-%m')
            file_label = dt.strftime('%B_%Y')
        else:
            parts = month.split('_')
            month_name = parts[0]
            year_num = int(parts[1]) if len(parts) > 1 else datetime.now().year
            dt = datetime.strptime(f"{month_name} {year_num}", "%b %Y")
            month_str_code = dt.strftime('%Y-%m')
            file_label = dt.strftime('%B_%Y')
    except Exception:
        dt = datetime.now()
        month_name = dt.strftime('%b')
        year_num = dt.year
        month_str_code = dt.strftime('%Y-%m')
        file_label = dt.strftime('%B_%Y')

    payments = Payment.query.filter_by(month=month_name, year=year_num).all()
    pay_map = {p.student_id: p for p in payments}

    details_data = []
    paid_count = 0
    pending_count = 0
    total_collection = 0.0
    applicable_count = 0

    for s in students:
        s_join = s.join_month or "2026-01"
        is_applicable = s_join <= month_str_code

        p = pay_map.get(s.id)
        if not is_applicable:
            status = "N/A"
            amt = ""
            method = ""
        elif p and p.status == 'Paid':
            status = "PAID"
            amt = p.amount
            method = p.payment_method or ""
            paid_count += 1
            applicable_count += 1
            total_collection += amt
        else:
            status = "PENDING"
            amt = ""
            method = ""
            pending_count += 1
            applicable_count += 1

        details_data.append({
            'Name': s.name,
            'Floor': s.floor_number,
            'Hall': s.room_number,
            'Phone': s.phone,
            'Month': f"{month_name} {year_num}",
            'Amount': amt,
            'Payment Method': method,
            'Status': status
        })

    df_details = pd.DataFrame(details_data)

    summary_data = [{
        'Total Students': applicable_count,
        'Paid': paid_count,
        'Pending': pending_count,
        'Collection': total_collection
    }]
    df_summary = pd.DataFrame(summary_data)

    filename = f"{file_label}_Fee_Report.xlsx"
    filepath = os.path.join(current_app.config['EXPORT_FOLDER'], filename)

    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df_details.to_excel(writer, sheet_name='Payment Details', index=False)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)

    return send_file(filepath, as_attachment=True, download_name=filename)
