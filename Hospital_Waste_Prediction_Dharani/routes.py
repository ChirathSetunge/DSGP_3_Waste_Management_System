from flask import request, jsonify, render_template
import numpy as np
import pandas as pd
import joblib
from  Hospital_Waste_Prediction_Dharani import hospital_bp
from datetime import datetime


model = joblib.load("Hospital_Waste_Prediction_Dharani/ml_model/best_XGB_model.pkl")
le = joblib.load("Hospital_Waste_Prediction_Dharani/ml_model/label encoder.pkl")

def categorize_rain(precipitation):

    if precipitation < 2.5:
        return 'no'
    elif precipitation < 7.5:
        return 'light'
    elif precipitation < 15:
        return 'moderate'
    else:
        return 'heavy'