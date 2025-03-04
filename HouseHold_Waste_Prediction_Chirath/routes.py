from flask import render_template, request, jsonify
import numpy as np
import pandas as pd
import sqlite3
from tensorflow.keras.models import load_model
import joblib
from HouseHold_Waste_Prediction_Chirath import household_bp

# Load model, scaler, and label encoder
model = load_model('HouseHold_Waste_Prediction_Chirath/ml_model/MSW_model.h5', compile=False)
scaler = joblib.load('HouseHold_Waste_Prediction_Chirath/ml_model/scaler.pkl')
label_encoder = joblib.load('HouseHold_Waste_Prediction_Chirath/ml_model/label_encoder.pkl')

# Prediction Route in the Household component
@household_bp.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    print(data)
    Route = data['route']
    Dump_Date = data['dump_date']
    MSW_Collected = data['msw_collected']

    # Extract date features
    Year = pd.to_datetime(Dump_Date).year
    Month = pd.to_datetime(Dump_Date).month
    Day_of_the_Week = pd.to_datetime(Dump_Date).dayofweek
    Week_Number = pd.to_datetime(Dump_Date).week

    # Connect to DB
    conn = sqlite3.connect('instance/database.db')

    # Get the values from the AvgWeek table
    query_avgweek = f"SELECT [MSW Avg Weekly Waste Percentage] FROM AvgWeek WHERE [Week Number] = {Week_Number}"
    MSW_Average_Weekly_Waste_Percentage = pd.read_sql_query(query_avgweek, conn).iloc[0, 0]

    # Get the values from the RouteWeek table
    query_routeweek = f"SELECT [msw_route_week] FROM RouteWeek WHERE [Route] = '{Route}' AND [Week Number] = {Week_Number}"
    msw_route_week = pd.read_sql_query(query_routeweek, conn).iloc[0, 0]

    # Read the data from the WasteData table
    query_wastedata = f"SELECT * FROM WasteData WHERE [Route] = '{Route}' ORDER BY [Dump Date] DESC"
    waste_data = pd.read_sql_query(query_wastedata, conn)

    # Convert the 'Dump Date' column to datetime
    waste_data['Dump Date'] = pd.to_datetime(waste_data['Dump Date'])

    # Filter for the route and sort by Dump Date
    waste_data = waste_data[waste_data['Route'] == Route].sort_values(by='Dump Date', ascending=True)

    # Apply shift safely
    MSW_lag_1 = waste_data['MSW Wastage Amount (Kg)'].iloc[-1] if not waste_data.empty else np.nan
    MSW_lag_7 = waste_data['MSW Wastage Amount (Kg)'].iloc[-7] if len(waste_data) >= 7 else np.nan

    # Calculate rolling features
    MSW_rolling_mean_7 = waste_data['MSW Wastage Amount (Kg)'].rolling(window=7, min_periods=1).mean().iloc[-1]
    MSW_rolling_min_7 = waste_data['MSW Wastage Amount (Kg)'].rolling(window=7, min_periods=1).min().iloc[-1]
    MSW_rolling_max_7 = waste_data['MSW Wastage Amount (Kg)'].rolling(window=7, min_periods=1).max().iloc[-1]

    MSW_rolling_mean_14 = waste_data['MSW Wastage Amount (Kg)'].rolling(window=14, min_periods=1).mean().iloc[-1]
    MSW_rolling_min_14 = waste_data['MSW Wastage Amount (Kg)'].rolling(window=14, min_periods=1).min().iloc[-1]
    MSW_rolling_max_14 = waste_data['MSW Wastage Amount (Kg)'].rolling(window=14, min_periods=1).max().iloc[-1]

    MSW_rolling_mean_30 = waste_data['MSW Wastage Amount (Kg)'].rolling(window=30, min_periods=1).mean().iloc[-1]
    MSW_rolling_min_30 = waste_data['MSW Wastage Amount (Kg)'].rolling(window=30, min_periods=1).min().iloc[-1]
    MSW_rolling_max_30 = waste_data['MSW Wastage Amount (Kg)'].rolling(window=30, min_periods=1).max().iloc[-1]

    # Close the database connection
    conn.close()

    # Create data frame for prediction
    new_data = pd.DataFrame([{
        'Route': Route,
        'Year': Year,
        'Month': Month,
        'Day of the Week': Day_of_the_Week,
        'Week Number': Week_Number,
        'MSW_Collected': MSW_Collected,
        'MSW Average Weekly Waste Percentage': MSW_Average_Weekly_Waste_Percentage,
        'msw_route_week': msw_route_week,
        'MSW_Lag_1': MSW_lag_1,
        'MSW_Lag_7': MSW_lag_7,
        'MSW_rolling_mean_7': MSW_rolling_mean_7,
        'MSW_rolling_min_7': MSW_rolling_min_7,
        'MSW_rolling_max_7': MSW_rolling_max_7,
        'MSW_rolling_mean_14': MSW_rolling_mean_14,
        'MSW_rolling_min_14': MSW_rolling_min_14,
        'MSW_rolling_max_14': MSW_rolling_max_14,
        'MSW_rolling_mean_30': MSW_rolling_mean_30,
        'MSW_rolling_min_30': MSW_rolling_min_30,
        'MSW_rolling_max_30': MSW_rolling_max_30
    }])

    # Preprocess the new data
    new_data['Route'] = label_encoder.transform(new_data['Route'])
    new_data['Month_sin'] = np.sin(2 * np.pi * new_data['Month'] / 12)
    new_data['Month_cos'] = np.cos(2 * np.pi * new_data['Month'] / 12)
    new_data['Day_of_Week_sin'] = np.sin(2 * np.pi * new_data['Day of the Week'] / 7)
    new_data['Day_of_Week_cos'] = np.cos(2 * np.pi * new_data['Day of the Week'] / 7)
    new_data['Week_Number_sin'] = np.sin(2 * np.pi * new_data['Week Number'] / 52)
    new_data['Week_Number_cos'] = np.cos(2 * np.pi * new_data['Week Number'] / 52)
    X_new = new_data.drop(columns=['Month', 'Day of the Week', 'Week Number'])
    X_new_route = X_new['Route'].values
    X_new_other = scaler.transform(X_new.drop(columns=['Route']).values)

    # Make prediction
    predictions = model.predict([X_new_route, X_new_other]).flatten()
    print(predictions)

    return jsonify({'prediction': round(float(predictions[0]), 2)})
