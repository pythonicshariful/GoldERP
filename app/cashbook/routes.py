from datetime import date
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from ..models import db, Cashbook
from ..auth.decorators import manager_required
from ..cashbook.utils import post_cashbook
from . import cashbook_bp


@cashbook_bp.route('/')
@login_required
def daily():
    filter_date = request.args.get('date', date.today().isoformat())

    entries = Cashbook.query.filter(
        Cashbook.txn_date == filter_date
    ).order_by(Cashbook.id).all()

    total_in = sum(float(e.amount) for e in entries if e.txn_type == 'receipt')
    total_out = sum(float(e.amount) for e in entries if e.txn_type == 'payment')

    # Opening balance: last entry before this date
    prev = Cashbook.query.filter(Cashbook.txn_date < filter_date).order_by(Cashbook.id.desc()).first()
    opening_balance = float(prev.running_balance) if prev else 0.0

    closing_balance = entries[-1].running_balance if entries else opening_balance

    return render_template('cashbook/daily.html',
                           entries=entries,
                           filter_date=filter_date,
                           total_in=total_in,
                           total_out=total_out,
                           opening_balance=opening_balance,
                           closing_balance=float(closing_balance))


@cashbook_bp.route('/manual', methods=['GET', 'POST'])
@login_required
@manager_required
def manual_entry():
    if request.method == 'POST':
        txn_date = date.fromisoformat(request.form.get('txn_date'))
        txn_type = request.form.get('txn_type')
        particulars = request.form.get('particulars', '').strip()
        amount = float(request.form.get('amount') or 0)

        post_cashbook(
            txn_date=txn_date,
            txn_type=txn_type,
            particulars=particulars,
            ref_type='manual',
            ref_id=None,
            amount=amount,
            is_manual=True
        )
        db.session.commit()
        flash('Manual cashbook entry added!', 'success')
        return redirect(url_for('cashbook.daily', date=txn_date.isoformat()))

    return render_template('cashbook/manual.html', today=date.today())
