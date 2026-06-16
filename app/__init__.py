from flask import Flask
from flask_login import LoginManager
from .models import db, User
from config import config
import os


login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        if config_name not in config:
            config_name = 'default'

    app.config.from_object(config[config_name])

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    from .showroom import showroom_bp
    app.register_blueprint(showroom_bp, url_prefix='/showroom')

    from .expenses import expenses_bp
    app.register_blueprint(expenses_bp, url_prefix='/expenses')

    from .inventory import inventory_bp
    app.register_blueprint(inventory_bp, url_prefix='/inventory')

    from .sales import sales_bp
    app.register_blueprint(sales_bp, url_prefix='/sales')

    from .mortgage import mortgage_bp
    app.register_blueprint(mortgage_bp, url_prefix='/mortgage')

    from .staff import staff_bp
    app.register_blueprint(staff_bp, url_prefix='/staff')

    from .cashbook import cashbook_bp
    app.register_blueprint(cashbook_bp, url_prefix='/cashbook')

    from .reports import reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')

    from .usermgmt import usermgmt_bp
    app.register_blueprint(usermgmt_bp, url_prefix='/users')

    from .dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    # Context processor — inject `now` into all templates
    from datetime import datetime

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    # Create tables
    with app.app_context():
        db.create_all()
        _seed_initial_data()

    return app


def _seed_initial_data():
    """Seed the initial owner account if no users exist, and seed expense types."""
    import bcrypt
    from .models import ExpenseType
    
    if User.query.count() == 0:
        pw = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
        owner = User(
            username='admin',
            password_hash=pw,
            full_name='System Owner',
            role='owner',
            is_active=True
        )
        db.session.add(owner)
        db.session.commit()
        print("Default owner account created: admin / admin123")

    # Seed Expense Types if empty
    if ExpenseType.query.count() == 0:
        default_types = ['Electricity Bill', 'Salary & Wages', 'Daily Showroom Expense', 'Office Rent', 'Repair & Maintenance', 'Others']
        for t in default_types:
            db.session.add(ExpenseType(name=t))
        db.session.commit()
        
        # Migrate old values so old records still map correctly
        try:
            db.session.execute(db.text("UPDATE expenses SET expense_type = 'Electricity Bill' WHERE expense_type = 'electricity'"))
            db.session.execute(db.text("UPDATE expenses SET expense_type = 'Salary & Wages' WHERE expense_type = 'salary'"))
            db.session.execute(db.text("UPDATE expenses SET expense_type = 'Daily Showroom Expense' WHERE expense_type = 'daily'"))
            db.session.execute(db.text("UPDATE expenses SET expense_type = 'Office Rent' WHERE expense_type = 'rent'"))
            db.session.execute(db.text("UPDATE expenses SET expense_type = 'Repair & Maintenance' WHERE expense_type = 'repair'"))
            db.session.execute(db.text("UPDATE expenses SET expense_type = 'Others' WHERE expense_type = 'other'"))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
