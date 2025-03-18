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
@hospital_bp.route('/predict', methods=['POST'])
def predict_waste():

    data = request.get_json()
    try:
        processed_data = preprocess_input(data)
        if isinstance(processed_data, str):
            return jsonify({"error": processed_data}), 400

        prediction = float(model.predict(processed_data)[0])
        return jsonify({'predicted_waste_weight': prediction})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@hospital_bp.route('/hospital_prediction')
def hospital_prediction():
    return render_template('hospital_predict.html')