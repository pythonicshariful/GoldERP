from flask import Blueprint
usermgmt_bp = Blueprint('usermgmt', __name__)
from . import routes  # noqa
