from flask import Blueprint
cashbook_bp = Blueprint('cashbook', __name__)
from . import routes  # noqa
