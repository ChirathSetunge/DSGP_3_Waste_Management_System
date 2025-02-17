from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
shared_bp = Blueprint('shared', __name__, template_folder='templates', static_folder='static')

from . import routes