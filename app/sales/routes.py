from datetime import date
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from ..models import db, GoldSale, GoldItem, ARPayment
from ..cashbook.utils import post_cashbook
from . import sales_bp


def _generate_invoice_no():
    today_str = date.today().strftime('%Y%m%d')
    prefix = f'INV-{today_str}-'
    count = GoldSale.query.filter(GoldSale.invoice_no.like(f'{prefix}%')).count()
    return f'{prefix}{count + 1:04d}'


@sales_bp.route('/')
@login_required
def list_sales():
    start_date = request.args.get('start_date', date.today().replace(day=1).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    sales = GoldSale.query.filter(
        GoldSale.sale_date >= start_date,
        GoldSale.sale_date <= end_date
    ).order_by(GoldSale.sale_date.desc()).all()
    total = sum(float(s.total_amount) for s in sales)
    return render_template('sales/list.html', sales=sales, total=total,
                           start_date=start_date, end_date=end_date)


@sales_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_sale():
    if request.method == 'POST':
        item_id = int(request.form.get('item_id'))
        quantity = float(request.form.get('quantity') or 0)
        rate_per_unit = float(request.form.get('rate_per_unit') or 0)
        making_charge = float(request.form.get('making_charge') or 0)
        total_amount = (quantity * rate_per_unit) + making_charge
        paid_amount = float(request.form.get('paid_amount') or 0)
        balance_due = total_amount - paid_amount
        payment_mode = request.form.get('payment_mode', 'cash')
        sale_date = date.fromisoformat(request.form.get('sale_date'))

        sale = GoldSale(
            sale_date=sale_date,
            invoice_no=_generate_invoice_no(),
            customer_name=request.form.get('customer_name', '').strip(),
            customer_phone=request.form.get('customer_phone', '').strip(),
            item_id=item_id,
            quantity=quantity,
            rate_per_unit=rate_per_unit,
            making_charge=making_charge,
            total_amount=total_amount,
            paid_amount=paid_amount,
            balance_due=balance_due,
            payment_mode=payment_mode,
            created_by=current_user.id
        )
        db.session.add(sale)
        db.session.flush()

        # Deduct stock
        item = GoldItem.query.get(item_id)
        if float(item.current_stock_qty) < quantity:
            flash('Insufficient stock for this sale!', 'danger')
            db.session.rollback()
            return redirect(url_for('sales.add_sale'))

        # Calculate COGS (weighted average cost)
        if float(item.current_stock_qty) > 0:
            avg_cost = float(item.current_stock_value) / float(item.current_stock_qty)
            cogs = avg_cost * quantity
        else:
            cogs = 0

        item.current_stock_qty = float(item.current_stock_qty) - quantity
        item.current_stock_value = max(0, float(item.current_stock_value) - cogs)

        # Auto-cashbook posting for cash received
        if paid_amount > 0 and payment_mode == 'cash':
            post_cashbook(
                txn_date=sale_date,
                txn_type='receipt',
                particulars=f'Sale {sale.invoice_no} - {sale.customer_name}',
                ref_type='sale',
                ref_id=sale.id,
                amount=paid_amount
            )

        db.session.commit()
        flash(f'Sale recorded! Invoice: {sale.invoice_no}', 'success')
        return redirect(url_for('sales.invoice', id=sale.id))

    items = GoldItem.query.filter(GoldItem.current_stock_qty > 0).all()
    return render_template('sales/add.html', items=items, today=date.today())


@sales_bp.route('/receive/<int:id>', methods=['GET', 'POST'])
@login_required
def receive_payment(id):
    sale = GoldSale.query.get_or_404(id)

    if request.method == 'POST':
        amount = float(request.form.get('amount') or 0)
        payment_mode = request.form.get('payment_mode', 'cash')
        payment_date = date.fromisoformat(request.form.get('payment_date'))

        if amount > float(sale.balance_due):
            flash('Amount exceeds balance due!', 'danger')
            return redirect(url_for('sales.receive_payment', id=id))

        payment = ARPayment(
            sale_id=sale.id,
            payment_date=payment_date,
            amount_received=amount,
            payment_mode=payment_mode,
            remarks=request.form.get('remarks', ''),
            created_by=current_user.id
        )
        db.session.add(payment)

        sale.paid_amount = float(sale.paid_amount) + amount
        sale.balance_due = float(sale.balance_due) - amount

        if payment_mode == 'cash':
            post_cashbook(
                txn_date=payment_date,
                txn_type='receipt',
                particulars=f'AR Receipt: {sale.invoice_no} - {sale.customer_name}',
                ref_type='ar_payment',
                ref_id=sale.id,
                amount=amount
            )

        db.session.commit()
        flash(f'Payment of ৳{amount:,.2f} received!', 'success')
        return redirect(url_for('sales.ar_list'))

    return render_template('sales/receive.html', sale=sale, today=date.today())


@sales_bp.route('/ar')
@login_required
def ar_list():
    sales = GoldSale.query.filter(GoldSale.balance_due > 0).order_by(GoldSale.sale_date).all()
    total_ar = sum(float(s.balance_due) for s in sales)
    return render_template('sales/ar.html', sales=sales, total_ar=total_ar)


@sales_bp.route('/ar-aging')
@login_required
def ar_aging():
    today = date.today()
    sales = GoldSale.query.filter(GoldSale.balance_due > 0).all()

    buckets = {'0_30': [], '31_60': [], '61_90': [], '90_plus': []}
    for s in sales:
        days = (today - s.sale_date).days
        if days <= 30:
            buckets['0_30'].append(s)
        elif days <= 60:
            buckets['31_60'].append(s)
        elif days <= 90:
            buckets['61_90'].append(s)
        else:
            buckets['90_plus'].append(s)

    totals = {k: sum(float(s.balance_due) for s in v) for k, v in buckets.items()}
    return render_template('sales/ar_aging.html', buckets=buckets, totals=totals, today=today)


@sales_bp.route('/invoice/<int:id>')
@login_required
def invoice(id):
    sale = GoldSale.query.get_or_404(id)
    from ..models import ShowroomSetup
    showroom = ShowroomSetup.query.first()
    return render_template('sales/invoice.html', sale=sale, showroom=showroom)


@sales_bp.route('/invoice/<int:id>/pdf')
@login_required
def invoice_pdf(id):
    from flask import make_response
    sale = GoldSale.query.get_or_404(id)
    from ..models import ShowroomSetup
    showroom = ShowroomSetup.query.first()
    html = render_template('sales/invoice_print.html', sale=sale, showroom=showroom)
    try:
        from weasyprint import HTML
        pdf = HTML(string=html).write_pdf()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=invoice_{sale.invoice_no}.pdf'
        return response
    except Exception:
        flash('PDF generation unavailable. Please print from browser.', 'warning')
        return redirect(url_for('sales.invoice', id=id))
