from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


# ─── Table 1: Users ────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='staff')  # owner/manager/staff
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    @property
    def is_owner(self):
        return self.role == 'owner'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_staff(self):
        return self.role == 'staff'

    @property
    def can_delete(self):
        return self.role == 'owner'

    @property
    def can_manage_users(self):
        return self.role == 'owner'

    @property
    def can_view_reports(self):
        return self.role in ('owner', 'manager')

    @property
    def can_enter_purchases(self):
        return self.role in ('owner', 'manager')

    @property
    def can_manual_cashbook(self):
        return self.role in ('owner', 'manager')


# ─── Table 2: Showroom Setup ───────────────────────────────────────────────────
class ShowroomSetup(db.Model):
    __tablename__ = 'showroom_setup'

    id = db.Column(db.Integer, primary_key=True)
    showroom_name = db.Column(db.String(100), nullable=False)
    ownership_type = db.Column(db.String(10), nullable=False, default='owned')  # owned/rented
    monthly_rent = db.Column(db.Numeric(12, 2), default=0)
    advance_rent_paid = db.Column(db.Numeric(12, 2), default=0)
    decoration_cost = db.Column(db.Numeric(12, 2), default=0)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    trade_license_no = db.Column(db.String(50))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─── Table 3: Expenses ─────────────────────────────────────────────────────────
class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    expense_date = db.Column(db.Date, nullable=False, default=date.today)
    expense_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    paid_by = db.Column(db.String(50), nullable=False, default='cash')  # cash/bank
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='expenses')


class ExpenseType(db.Model):
    __tablename__ = 'expense_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Table 4: Gold Items (Stock Master) ───────────────────────────────────────
class GoldItem(db.Model):
    __tablename__ = 'gold_items'

    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(20), unique=True, nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='finished')  # raw/finished
    unit = db.Column(db.String(10), nullable=False, default='gram')  # gram/piece/tola
    current_stock_qty = db.Column(db.Numeric(10, 3), default=0)
    current_stock_value = db.Column(db.Numeric(14, 2), default=0)

    purchases = db.relationship('GoldPurchase', backref='item', lazy='dynamic')
    sales = db.relationship('GoldSale', backref='item', lazy='dynamic')


# ─── Table 5: Gold Purchases ───────────────────────────────────────────────────
class GoldPurchase(db.Model):
    __tablename__ = 'gold_purchases'

    id = db.Column(db.Integer, primary_key=True)
    purchase_date = db.Column(db.Date, nullable=False, default=date.today)
    purchase_type = db.Column(db.String(10), nullable=False, default='finished')  # raw/finished
    item_id = db.Column(db.Integer, db.ForeignKey('gold_items.id'), nullable=False)
    supplier_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    rate_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False)
    payment_mode = db.Column(db.String(20), nullable=False, default='cash')  # cash/bank/credit
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='purchases')


# ─── Table 6: Gold Mortgage ────────────────────────────────────────────────────
class GoldMortgage(db.Model):
    __tablename__ = 'gold_mortgage'

    id = db.Column(db.Integer, primary_key=True)
    mortgage_date = db.Column(db.Date, nullable=False, default=date.today)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20))
    gold_description = db.Column(db.Text)
    gold_weight_gram = db.Column(db.Numeric(8, 3), nullable=False)
    gold_value_estimated = db.Column(db.Numeric(12, 2), nullable=False)
    loan_amount = db.Column(db.Numeric(12, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)  # monthly %
    status = db.Column(db.String(20), nullable=False, default='active')  # active/redeemed/defaulted
    redemption_date = db.Column(db.Date, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='mortgages')
    interest_records = db.relationship('MortgageInterest', backref='mortgage', lazy='dynamic')

    @property
    def monthly_interest(self):
        return float(self.loan_amount) * float(self.interest_rate) / 100


# ─── Table 7: Mortgage Interest ────────────────────────────────────────────────
class MortgageInterest(db.Model):
    __tablename__ = 'mortgage_interest'

    id = db.Column(db.Integer, primary_key=True)
    mortgage_id = db.Column(db.Integer, db.ForeignKey('gold_mortgage.id'), nullable=False)
    interest_month = db.Column(db.Date, nullable=False)  # first day of the month
    interest_amount = db.Column(db.Numeric(10, 2), nullable=False)
    received = db.Column(db.Boolean, default=False)
    received_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Table 8: Gold Sales ───────────────────────────────────────────────────────
class GoldSale(db.Model):
    __tablename__ = 'gold_sales'

    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.Date, nullable=False, default=date.today)
    invoice_no = db.Column(db.String(30), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20))
    item_id = db.Column(db.Integer, db.ForeignKey('gold_items.id'), nullable=False)
    quantity = db.Column(db.Numeric(8, 3), nullable=False)
    rate_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    making_charge = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    balance_due = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    payment_mode = db.Column(db.String(20), nullable=False, default='cash')  # cash/bank/credit
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='sales')
    payments = db.relationship('ARPayment', backref='sale', lazy='dynamic')


# ─── AR Payment (Accounts Receivable Payments) ────────────────────────────────
class ARPayment(db.Model):
    __tablename__ = 'ar_payments'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('gold_sales.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    amount_received = db.Column(db.Numeric(14, 2), nullable=False)
    payment_mode = db.Column(db.String(20), default='cash')
    remarks = db.Column(db.String(200))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Table 9: Salary Staff ─────────────────────────────────────────────────────
class SalaryStaff(db.Model):
    __tablename__ = 'salary_staff'

    id = db.Column(db.Integer, primary_key=True)
    staff_name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(50))
    join_date = db.Column(db.Date, nullable=False)
    basic_salary = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship('SalaryTransaction', backref='staff', lazy='dynamic')


# ─── Table 10: Salary Transactions ────────────────────────────────────────────
class SalaryTransaction(db.Model):
    __tablename__ = 'salary_transactions'

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('salary_staff.id'), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False, default=date.today)
    transaction_type = db.Column(db.String(20), nullable=False)  # advance/adjustment/payment/service_charge
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    remarks = db.Column(db.String(200))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='salary_txns')


# ─── Table 11: Cashbook ────────────────────────────────────────────────────────
class Cashbook(db.Model):
    __tablename__ = 'cashbook'

    id = db.Column(db.Integer, primary_key=True)
    txn_date = db.Column(db.Date, nullable=False, default=date.today)
    txn_type = db.Column(db.String(10), nullable=False)  # receipt/payment
    particulars = db.Column(db.String(200), nullable=False)
    ref_type = db.Column(db.String(30))  # sale/purchase/expense/mortgage/salary
    ref_id = db.Column(db.Integer, nullable=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    running_balance = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    is_manual = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='cashbook_entries')
