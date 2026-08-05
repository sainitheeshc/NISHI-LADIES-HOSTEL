from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, User

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
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
            
        return redirect(url_for('settings.index'))
        
    return render_template('settings.html')
