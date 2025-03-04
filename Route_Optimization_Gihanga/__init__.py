from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
route_optimization_bp = Blueprint('routeOptimization', __name__, template_folder='templates', static_folder='static')

