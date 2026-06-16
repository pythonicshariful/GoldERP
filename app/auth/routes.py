import bcrypt
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from ..models import db, User
from . import auth_bp


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').encode('utf-8')

        user = User.query.filter_by(username=username).first()
        if user and user.is_active and bcrypt.checkpw(password, user.password_hash.encode('utf-8')):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password', '').encode('utf-8')
        new_pw = request.form.get('new_password', '').encode('utf-8')
        confirm_pw = request.form.get('confirm_password', '').encode('utf-8')

        user = User.query.get(current_user.id)
        if not bcrypt.checkpw(current_pw, user.password_hash.encode('utf-8')):
            flash('Current password is incorrect.', 'danger')
        elif new_pw != confirm_pw:
            flash('New passwords do not match.', 'danger')
        elif len(new_pw) < 6:
            flash('Password must be at least 6 characters.', 'warning')
        else:
            user.password_hash = bcrypt.hashpw(new_pw, bcrypt.gensalt()).decode('utf-8')
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('dashboard.index'))

    return render_template('auth/change_password.html')
