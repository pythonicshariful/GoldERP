from datetime import date, timedelta
from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from ..models import db, GoldSale, Cashbook, GoldItem, GoldMortgage, ShowroomSetup, ARPayment, GoldPurchase, Expense
from . import dashboard_bp


@dashboard_bp.route('/')
@login_required
def index():
    today = date.today()
    seven_days_ago = today - timedelta(days=6)

    # Today's cash balance (last running balance)
    last_cb = Cashbook.query.order_by(Cashbook.id.desc()).first()
    cash_balance = float(last_cb.running_balance) if last_cb else 0.0

    # Today's sales total
    today_sales = db.session.query(func.sum(GoldSale.total_amount)).filter(
        GoldSale.sale_date == today
    ).scalar() or 0

    # Total AR outstanding
    ar_outstanding = db.session.query(func.sum(GoldSale.balance_due)).filter(
        GoldSale.balance_due > 0
    ).scalar() or 0

    # Active mortgages
    active_mortgages = GoldMortgage.query.filter_by(status='active').count()
    total_loan_outstanding = db.session.query(func.sum(GoldMortgage.loan_amount)).filter(
        GoldMortgage.status == 'active'
    ).scalar() or 0

    # Total stock value
    total_stock_value = db.session.query(func.sum(GoldItem.current_stock_value)).scalar() or 0

    # 7-day sales chart data
    sales_labels = []
    sales_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_sales = db.session.query(func.sum(GoldSale.total_amount)).filter(
            GoldSale.sale_date == day
        ).scalar() or 0
        sales_labels.append(day.strftime('%d %b'))
        sales_data.append(float(day_sales))

    # Calculate Bank Balance dynamically
    # Inflows
    sales_bank = db.session.query(func.sum(GoldSale.paid_amount)).filter(GoldSale.payment_mode == 'bank').scalar() or 0
    ar_bank = db.session.query(func.sum(ARPayment.amount_received)).filter(ARPayment.payment_mode == 'bank').scalar() or 0
    # Outflows
    purchases_bank = db.session.query(func.sum(GoldPurchase.total_amount)).filter(GoldPurchase.payment_mode == 'bank').scalar() or 0
    expenses_bank = db.session.query(func.sum(Expense.amount)).filter(Expense.paid_by == 'bank').scalar() or 0

    bank_balance = (float(sales_bank) + float(ar_bank)) - (float(purchases_bank) + float(expenses_bank))

    # Fetch stock items for the Stock System view
    stock_items = GoldItem.query.order_by(GoldItem.item_code).all()

    showroom = ShowroomSetup.query.first()

    return render_template('dashboard.html',
                           cash_balance=cash_balance,
                           bank_balance=bank_balance,
                           stock_items=stock_items,
                           today_sales=float(today_sales),
                           ar_outstanding=float(ar_outstanding),
                           active_mortgages=active_mortgages,
                           total_loan_outstanding=float(total_loan_outstanding),
                           total_stock_value=float(total_stock_value),
                           sales_labels=sales_labels,
                           sales_data=sales_data,
                           showroom=showroom,
                           today=today)


@dashboard_bp.route('/manual')
@login_required
def manual():
    return render_template('manual.html')
