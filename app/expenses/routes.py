from datetime import date
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from ..models import db, Expense, Cashbook, ExpenseType
from ..auth.decorators import manager_required
from . import expenses_bp
from ..cashbook.utils import post_cashbook


@expenses_bp.route('/')
@login_required
def list_expenses():
    start_date = request.args.get('start_date', date.today().replace(day=1).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    expense_type = request.args.get('expense_type', '')

    query = Expense.query.filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    )
    if expense_type:
        query = query.filter(Expense.expense_type == expense_type)

    expenses = query.order_by(Expense.expense_date.desc()).all()
    total = sum(float(e.amount) for e in expenses)
    expense_types = [(t.name, t.name) for t in ExpenseType.query.order_by(ExpenseType.name).all()]
    return render_template('expenses/list.html', expenses=expenses, total=total,
                           start_date=start_date, end_date=end_date, expense_type=expense_type,
                           expense_types=expense_types)


@expenses_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        expense = Expense(
            expense_date=date.fromisoformat(request.form.get('expense_date')),
            expense_type=request.form.get('expense_type'),
            description=request.form.get('description', '').strip(),
            amount=float(request.form.get('amount') or 0),
            paid_by=request.form.get('paid_by', 'cash'),
            created_by=current_user.id
        )
        db.session.add(expense)
        db.session.flush()

        # Auto-cashbook posting
        if expense.paid_by == 'cash':
            post_cashbook(
                txn_date=expense.expense_date,
                txn_type='payment',
                particulars=f'Expense: {expense.description or expense.expense_type}',
                ref_type='expense',
                ref_id=expense.id,
                amount=float(expense.amount)
            )

        db.session.commit()
        flash('Expense recorded successfully!', 'success')
        return redirect(url_for('expenses.list_expenses'))

    expense_types = [(t.name, t.name) for t in ExpenseType.query.order_by(ExpenseType.name).all()]
    return render_template('expenses/add.html', expense_types=expense_types, today=date.today())


@expenses_bp.route('/add_type', methods=['POST'])
@login_required
def add_expense_type():
    new_type_name = request.form.get('new_type_name', '').strip()
    if new_type_name:
        existing = ExpenseType.query.filter(func.lower(ExpenseType.name) == new_type_name.lower()).first()
        if not existing:
            db.session.add(ExpenseType(name=new_type_name))
            db.session.commit()
            flash(f'Expense type "{new_type_name}" added successfully.', 'success')
        else:
            flash(f'Expense type "{new_type_name}" already exists.', 'warning')
    return redirect(request.referrer or url_for('expenses.list_expenses'))


@expenses_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    if request.method == 'POST':
        expense.expense_date = date.fromisoformat(request.form.get('expense_date'))
        expense.expense_type = request.form.get('expense_type')
        expense.description = request.form.get('description', '').strip()
        expense.amount = float(request.form.get('amount') or 0)
        expense.paid_by = request.form.get('paid_by', 'cash')
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expenses.list_expenses'))

    expense_types = [(t.name, t.name) for t in ExpenseType.query.order_by(ExpenseType.name).all()]
    return render_template('expenses/edit.html', expense=expense, expense_types=expense_types)


@expenses_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    if not current_user.can_delete:
        flash('Only the owner can delete records.', 'danger')
        return redirect(url_for('expenses.list_expenses'))
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('expenses.list_expenses'))


@expenses_bp.route('/report')
@login_required
def monthly_report():
    year = int(request.args.get('year', date.today().year))
    month = int(request.args.get('month', date.today().month))

    expenses = Expense.query.filter(
        extract('year', Expense.expense_date) == year,
        extract('month', Expense.expense_date) == month
    ).all()

    by_type = {}
    for e in expenses:
        by_type.setdefault(e.expense_type, 0)
        by_type[e.expense_type] += float(e.amount)

    total = sum(by_type.values())
    expense_types = [(t.name, t.name) for t in ExpenseType.query.order_by(ExpenseType.name).all()]
    return render_template('expenses/report.html', by_type=by_type, total=total,
                           year=year, month=month, expense_types=expense_types)
