from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, ShowroomSetup
from ..auth.decorators import owner_required
from . import showroom_bp


@showroom_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    showroom = ShowroomSetup.query.first()

    if request.method == 'POST':
        if not current_user.is_owner:
            flash('Only the owner can edit showroom settings.', 'danger')
            return redirect(url_for('showroom.index'))

        if showroom is None:
            showroom = ShowroomSetup()
            db.session.add(showroom)

        showroom.showroom_name = request.form.get('showroom_name', '').strip()
        showroom.ownership_type = request.form.get('ownership_type', 'owned')
        showroom.monthly_rent = float(request.form.get('monthly_rent') or 0)
        showroom.advance_rent_paid = float(request.form.get('advance_rent_paid') or 0)
        showroom.decoration_cost = float(request.form.get('decoration_cost') or 0)
        showroom.address = request.form.get('address', '').strip()
        showroom.phone = request.form.get('phone', '').strip()
        showroom.trade_license_no = request.form.get('trade_license_no', '').strip()
        db.session.commit()
        flash('Showroom settings saved successfully!', 'success')
        return redirect(url_for('showroom.index'))

    return render_template('showroom/index.html', showroom=showroom)
