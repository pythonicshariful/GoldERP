import bcrypt
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, User
from ..auth.decorators import owner_required
from . import usermgmt_bp


@usermgmt_bp.route('/')
@login_required
@owner_required
def list_users():
    users = User.query.order_by(User.username).all()
    return render_template('usermgmt/list.html', users=users)


@usermgmt_bp.route('/add', methods=['GET', 'POST'])
@login_required
@owner_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').encode('utf-8')
        role = request.form.get('role', 'staff')
        full_name = request.form.get('full_name', '').strip()

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('usermgmt.add_user'))

        pw_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
        user = User(username=username, password_hash=pw_hash,
                    role=role, full_name=full_name, is_active=True)
        db.session.add(user)
        db.session.commit()
        flash(f'User "{username}" created!', 'success')
        return redirect(url_for('usermgmt.list_users'))

    return render_template('usermgmt/add.html')


@usermgmt_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@owner_required
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', '').strip()
        user.role = request.form.get('role', 'staff')
        user.is_active = request.form.get('is_active') == 'on'

        new_pw = request.form.get('new_password', '').strip()
        if new_pw:
            user.password_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode('utf-8')

        db.session.commit()
        flash('User updated!', 'success')
        return redirect(url_for('usermgmt.list_users'))

    return render_template('usermgmt/edit.html', user=user)


@usermgmt_bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
@owner_required
def toggle_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Cannot deactivate your own account.', 'danger')
        return redirect(url_for('usermgmt.list_users'))
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} {status}.', 'success')
    return redirect(url_for('usermgmt.list_users'))
