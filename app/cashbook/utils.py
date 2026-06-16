from datetime import date as date_type
from ..models import db, Cashbook
from flask_login import current_user


def get_running_balance():
    """Get current running cash balance."""
    last = Cashbook.query.order_by(Cashbook.id.desc()).first()
    return float(last.running_balance) if last else 0.0


def post_cashbook(txn_date, txn_type, particulars, ref_type, ref_id, amount, is_manual=False):
    """
    Post a cashbook entry and update the running balance.
    txn_type: 'receipt' (cash in) or 'payment' (cash out)
    """
    current_balance = get_running_balance()

    if txn_type == 'receipt':
        new_balance = current_balance + float(amount)
    else:
        new_balance = current_balance - float(amount)

    created_by = current_user.id if current_user and current_user.is_authenticated else None

    entry = Cashbook(
        txn_date=txn_date if isinstance(txn_date, date_type) else date_type.fromisoformat(str(txn_date)),
        txn_type=txn_type,
        particulars=particulars,
        ref_type=ref_type,
        ref_id=ref_id,
        amount=float(amount),
        running_balance=new_balance,
        is_manual=is_manual,
        created_by=created_by
    )
    db.session.add(entry)
    return entry
