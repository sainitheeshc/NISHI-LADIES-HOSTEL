from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, User, get_setting, set_setting

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not current_password or not new_password or not confirm_password:
                flash('All password fields are required.', 'error')
                return redirect(url_for('settings.index'))

            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('settings.index'))

            if new_password != confirm_password:
                flash('New password and Confirm password do not match.', 'error')
                return redirect(url_for('settings.index'))

            if len(new_password) < 4:
                flash('New password must be at least 4 characters long.', 'error')
                return redirect(url_for('settings.index'))

            try:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password changed successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating password: {str(e)}', 'error')

        elif action == 'change_pin':
            current_pin = request.form.get('current_pin', '').strip()
            new_pin = request.form.get('new_pin', '').strip()
            confirm_pin = request.form.get('confirm_pin', '').strip()

            active_pin = get_setting('admin_pin', '1234')

            if current_pin != active_pin:
                flash('Current Security PIN is incorrect.', 'error')
                return redirect(url_for('settings.index'))

            if new_pin != confirm_pin:
                flash('New PIN and Confirm PIN do not match.', 'error')
                return redirect(url_for('settings.index'))

            if len(new_pin) != 4 or not new_pin.isdigit():
                flash('Security PIN must be exactly 4 digits.', 'error')
                return redirect(url_for('settings.index'))

            try:
                set_setting('admin_pin', new_pin)
                flash('Security PIN updated successfully!', 'success')
            except Exception as e:
                flash(f'Error updating Security PIN: {str(e)}', 'error')

        return redirect(url_for('settings.index'))

    active_pin = get_setting('admin_pin', '1234')
    return render_template('settings.html', active_pin=active_pin)
