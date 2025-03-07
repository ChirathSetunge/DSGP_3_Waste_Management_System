from flask import Blueprint

household_bp = Blueprint('household', __name__, template_folder='templates', static_folder='static')

from HouseHold_Waste_Prediction_Chirath import routes
