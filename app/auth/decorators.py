from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user


def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'owner':
            flash('Owner access required.', 'danger')
            return abort(403)
        return f(*args, **kwargs)
    return decorated


def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('owner', 'manager'):
            flash('Manager or Owner access required.', 'danger')
            return abort(403)
        return f(*args, **kwargs)
    return decorated


def report_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('owner', 'manager'):
            flash('You do not have permission to view reports.', 'danger')
            return abort(403)
        return f(*args, **kwargs)
    return decorated
