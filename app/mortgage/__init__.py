from flask import Blueprint
mortgage_bp = Blueprint('mortgage', __name__)
from . import routes  # noqa
