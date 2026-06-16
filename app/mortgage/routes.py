from datetime import date
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from ..models import db, GoldMortgage, MortgageInterest
from ..cashbook.utils import post_cashbook
from . import mortgage_bp


@mortgage_bp.route('/')
@login_required
def register():
    status_filter = request.args.get('status', '')
    query = GoldMortgage.query
    if status_filter:
        query = query.filter(GoldMortgage.status == status_filter)
    mortgages = query.order_by(GoldMortgage.mortgage_date.desc()).all()
    return render_template('mortgage/register.html', mortgages=mortgages, status_filter=status_filter)


@mortgage_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_mortgage():
    if request.method == 'POST':
        mortgage_date = date.fromisoformat(request.form.get('mortgage_date'))
        loan_amount = float(request.form.get('loan_amount') or 0)
        interest_rate = float(request.form.get('interest_rate') or 0)

        mortgage = GoldMortgage(
            mortgage_date=mortgage_date,
            customer_name=request.form.get('customer_name', '').strip(),
            customer_phone=request.form.get('customer_phone', '').strip(),
            gold_description=request.form.get('gold_description', '').strip(),
            gold_weight_gram=float(request.form.get('gold_weight_gram') or 0),
            gold_value_estimated=float(request.form.get('gold_value_estimated') or 0),
            loan_amount=loan_amount,
            interest_rate=interest_rate,
            status='active',
            created_by=current_user.id
        )
        db.session.add(mortgage)
        db.session.flush()

        # Cashbook: loan given (payment)
        post_cashbook(
            txn_date=mortgage_date,
            txn_type='payment',
            particulars=f'Mortgage Loan: {mortgage.customer_name}',
            ref_type='mortgage',
            ref_id=mortgage.id,
            amount=loan_amount
        )

        db.session.commit()
        flash('Mortgage recorded successfully!', 'success')
        return redirect(url_for('mortgage.register'))

    return render_template('mortgage/add.html', today=date.today())


@mortgage_bp.route('/interest/<int:id>', methods=['GET', 'POST'])
@login_required
def record_interest(id):
    mortgage = GoldMortgage.query.get_or_404(id)

    if request.method == 'POST':
        interest_month_str = request.form.get('interest_month')
        interest_amount = float(request.form.get('interest_amount') or 0)
        received_date = date.fromisoformat(request.form.get('received_date'))

        # Check if already recorded for this month
        month_date = date.fromisoformat(interest_month_str + '-01')
        existing = MortgageInterest.query.filter_by(
            mortgage_id=id, interest_month=month_date
        ).first()

        if existing:
            existing.received = True
            existing.received_date = received_date
            existing.interest_amount = interest_amount
            interest_record = existing
        else:
            interest_record = MortgageInterest(
                mortgage_id=id,
                interest_month=month_date,
                interest_amount=interest_amount,
                received=True,
                received_date=received_date
            )
            db.session.add(interest_record)

        db.session.flush()

        # Cashbook: interest receipt
        post_cashbook(
            txn_date=received_date,
            txn_type='receipt',
            particulars=f'Mortgage Interest: {mortgage.customer_name} ({interest_month_str})',
            ref_type='mortgage_interest',
            ref_id=mortgage.id,
            amount=interest_amount
        )

        db.session.commit()
        flash('Interest payment recorded!', 'success')
        return redirect(url_for('mortgage.register'))

    return render_template('mortgage/interest.html', mortgage=mortgage, today=date.today())


@mortgage_bp.route('/redeem/<int:id>', methods=['POST'])
@login_required
def redeem(id):
    mortgage = GoldMortgage.query.get_or_404(id)
    redemption_date = date.fromisoformat(request.form.get('redemption_date', date.today().isoformat()))

    mortgage.status = 'redeemed'
    mortgage.redemption_date = redemption_date

    # Cashbook: redemption received
    post_cashbook(
        txn_date=redemption_date,
        txn_type='receipt',
        particulars=f'Mortgage Redemption: {mortgage.customer_name}',
        ref_type='mortgage_redemption',
        ref_id=mortgage.id,
        amount=float(mortgage.loan_amount)
    )

    db.session.commit()
    flash(f'Mortgage redeemed for {mortgage.customer_name}!', 'success')
    return redirect(url_for('mortgage.register'))


@mortgage_bp.route('/report')
@login_required
def interest_report():
    year = int(request.args.get('year', date.today().year))

    records = MortgageInterest.query.filter(
        func.extract('year', MortgageInterest.interest_month) == year,
        MortgageInterest.received == True
    ).all()

    monthly = {}
    for r in records:
        key = r.interest_month.strftime('%B %Y')
        monthly.setdefault(key, 0)
        monthly[key] += float(r.interest_amount)

    total = sum(monthly.values())
    return render_template('mortgage/report.html', monthly=monthly, total=total, year=year)
