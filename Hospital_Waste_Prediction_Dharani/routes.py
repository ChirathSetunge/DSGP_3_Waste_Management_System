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

def preprocess_input(data):

    try:
        date_obj = datetime.strptime(data['date'], "%Y-%m-%d")
        data['cat_rain'] = categorize_rain(data['precipitation_sum'])
        data['Day of the week'] = date_obj.weekday()
        data['Month'] = date_obj.month
        data['Day'] = date_obj.day
        data['cat_rain'] = le.transform([data['cat_rain']])[0]

        return [[data['Day of the week'], data['Month'], data['Day'], data['cat_rain'], data['daily_patients']]]
    except Exception as e:
        return str(e)
