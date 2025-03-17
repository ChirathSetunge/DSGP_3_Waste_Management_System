from flask import Blueprint

# hospital blueprint
hospital_bp = Blueprint('hospital', __name__, template_folder='templates', static_folder='static')

from Hospital_Waste_Prediction_Dharani import routes