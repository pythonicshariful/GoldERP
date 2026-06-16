from datetime import date
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from ..models import db, SalaryStaff, SalaryTransaction
from ..auth.decorators import manager_required
from ..cashbook.utils import post_cashbook
from . import staff_bp


@staff_bp.route('/')
@login_required
def list_staff():
    staff = SalaryStaff.query.order_by(SalaryStaff.staff_name).all()
    return render_template('staff/list.html', staff=staff)


@staff_bp.route('/add', methods=['GET', 'POST'])
@login_required
@manager_required
def add_staff():
    if request.method == 'POST':
        member = SalaryStaff(
            staff_name=request.form.get('staff_name', '').strip(),
            designation=request.form.get('designation', '').strip(),
            join_date=date.fromisoformat(request.form.get('join_date')),
            basic_salary=float(request.form.get('basic_salary') or 0),
            is_active=True
        )
        db.session.add(member)
        db.session.commit()
        flash(f'Staff member "{member.staff_name}" added!', 'success')
        return redirect(url_for('staff.list_staff'))
    return render_template('staff/add.html', today=date.today())


@staff_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_staff(id):
    member = SalaryStaff.query.get_or_404(id)
    if request.method == 'POST':
        member.staff_name = request.form.get('staff_name', '').strip()
        member.designation = request.form.get('designation', '').strip()
        member.basic_salary = float(request.form.get('basic_salary') or 0)
        member.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash('Staff details updated!', 'success')
        return redirect(url_for('staff.list_staff'))
    return render_template('staff/edit.html', member=member)


@staff_bp.route('/salary/add', methods=['GET', 'POST'])
@login_required
@manager_required
def add_salary_transaction():
    if request.method == 'POST':
        staff_id = int(request.form.get('staff_id'))
        txn_type = request.form.get('transaction_type')
        amount = float(request.form.get('amount') or 0)
        txn_date = date.fromisoformat(request.form.get('transaction_date'))

        txn = SalaryTransaction(
            staff_id=staff_id,
            transaction_date=txn_date,
            transaction_type=txn_type,
            amount=amount,
            remarks=request.form.get('remarks', '').strip(),
            created_by=current_user.id
        )
        db.session.add(txn)
        db.session.flush()

        # Cashbook posting for cash payments
        member = SalaryStaff.query.get(staff_id)
        if txn_type in ('advance', 'payment'):
            post_cashbook(
                txn_date=txn_date,
                txn_type='payment',
                particulars=f'Staff {txn_type.title()}: {member.staff_name}',
                ref_type='salary',
                ref_id=txn.id,
                amount=amount
            )

        db.session.commit()
        flash(f'Salary transaction recorded for {member.staff_name}!', 'success')
        return redirect(url_for('staff.list_staff'))

    staff = SalaryStaff.query.filter_by(is_active=True).all()
    return render_template('staff/salary.html', staff=staff, today=date.today())


@staff_bp.route('/summary')
@login_required
def salary_summary():
    year = int(request.args.get('year', date.today().year))
    month = int(request.args.get('month', date.today().month))

    staff = SalaryStaff.query.filter_by(is_active=True).all()
    summary = []
    for member in staff:
        txns = SalaryTransaction.query.filter(
            SalaryTransaction.staff_id == member.id,
            extract('year', SalaryTransaction.transaction_date) == year,
            extract('month', SalaryTransaction.transaction_date) == month
        ).all()

        advance = sum(float(t.amount) for t in txns if t.transaction_type == 'advance')
        payment = sum(float(t.amount) for t in txns if t.transaction_type == 'payment')
        service_charge = sum(float(t.amount) for t in txns if t.transaction_type == 'service_charge')

        summary.append({
            'member': member,
            'gross': float(member.basic_salary),
            'advance': advance,
            'service_charge': service_charge,
            'net_paid': payment
        })

    return render_template('staff/summary.html', summary=summary, year=year, month=month)
