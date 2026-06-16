from datetime import date
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, GoldItem, GoldPurchase
from ..auth.decorators import manager_required
from ..cashbook.utils import post_cashbook
from . import inventory_bp


@inventory_bp.route('/items')
@login_required
def list_items():
    items = GoldItem.query.order_by(GoldItem.item_code).all()
    return render_template('inventory/items.html', items=items)


@inventory_bp.route('/items/add', methods=['GET', 'POST'])
@login_required
@manager_required
def add_item():
    if request.method == 'POST':
        item = GoldItem(
            item_code=request.form.get('item_code', '').strip().upper(),
            item_name=request.form.get('item_name', '').strip(),
            category=request.form.get('category', 'finished'),
            unit=request.form.get('unit', 'gram')
        )
        db.session.add(item)
        db.session.commit()
        flash(f'Item "{item.item_name}" added successfully!', 'success')
        return redirect(url_for('inventory.list_items'))
    return render_template('inventory/add_item.html')


@inventory_bp.route('/items/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_item(id):
    item = GoldItem.query.get_or_404(id)
    if request.method == 'POST':
        item.item_code = request.form.get('item_code', '').strip().upper()
        item.item_name = request.form.get('item_name', '').strip()
        item.category = request.form.get('category', 'finished')
        item.unit = request.form.get('unit', 'gram')
        db.session.commit()
        flash('Item updated!', 'success')
        return redirect(url_for('inventory.list_items'))
    return render_template('inventory/edit_item.html', item=item)


@inventory_bp.route('/purchases')
@login_required
def list_purchases():
    start_date = request.args.get('start_date', date.today().replace(day=1).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    item_id = request.args.get('item_id', '')

    query = GoldPurchase.query.filter(
        GoldPurchase.purchase_date >= start_date,
        GoldPurchase.purchase_date <= end_date
    )
    if item_id:
        query = query.filter(GoldPurchase.item_id == int(item_id))

    purchases = query.order_by(GoldPurchase.purchase_date.desc()).all()
    items = GoldItem.query.all()
    total = sum(float(p.total_amount) for p in purchases)
    return render_template('inventory/purchases.html', purchases=purchases, items=items,
                           total=total, start_date=start_date, end_date=end_date, item_id=item_id)


@inventory_bp.route('/purchases/add', methods=['GET', 'POST'])
@login_required
@manager_required
def add_purchase():
    if request.method == 'POST':
        item_id = int(request.form.get('item_id'))
        quantity = float(request.form.get('quantity') or 0)
        rate_per_unit = float(request.form.get('rate_per_unit') or 0)
        total_amount = quantity * rate_per_unit
        payment_mode = request.form.get('payment_mode', 'cash')
        purchase_date = date.fromisoformat(request.form.get('purchase_date'))

        purchase = GoldPurchase(
            purchase_date=purchase_date,
            purchase_type=request.form.get('purchase_type', 'finished'),
            item_id=item_id,
            supplier_name=request.form.get('supplier_name', '').strip(),
            quantity=quantity,
            rate_per_unit=rate_per_unit,
            total_amount=total_amount,
            payment_mode=payment_mode,
            created_by=current_user.id
        )
        db.session.add(purchase)
        db.session.flush()

        # Update stock
        item = GoldItem.query.get(item_id)
        old_qty = float(item.current_stock_qty)
        old_val = float(item.current_stock_value)
        item.current_stock_qty = old_qty + quantity
        item.current_stock_value = old_val + total_amount

        # Auto-cashbook posting (cash purchases only)
        if payment_mode == 'cash':
            post_cashbook(
                txn_date=purchase_date,
                txn_type='payment',
                particulars=f'Gold Purchase: {item.item_name} from {purchase.supplier_name}',
                ref_type='purchase',
                ref_id=purchase.id,
                amount=total_amount
            )

        db.session.commit()
        flash('Purchase recorded and stock updated!', 'success')
        return redirect(url_for('inventory.list_purchases'))

    items = GoldItem.query.all()
    return render_template('inventory/add_purchase.html', items=items, today=date.today())


@inventory_bp.route('/stock')
@login_required
def stock_report():
    category = request.args.get('category', '')
    query = GoldItem.query
    if category:
        query = query.filter(GoldItem.category == category)
    items = query.order_by(GoldItem.item_code).all()
    total_value = sum(float(i.current_stock_value) for i in items)
    return render_template('inventory/stock.html', items=items, total_value=total_value, category=category)
