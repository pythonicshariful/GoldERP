from flask import Blueprint
showroom_bp = Blueprint('showroom', __name__)
from . import routes  # noqa
