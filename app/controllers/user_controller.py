from flask import jsonify, request, render_template
from app import mongo
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import joblib
import os
import numpy as np
import sys, os
from ..model.train import train_and_save
# Load the model

def load_model():
    try:
        model_path_save= './app/model/stock_price_model.joblib'
        if (os.path.exists(model_path_save)):
            print("model found, skipping training")
        else:
            #Training and saving model in app/model
            print("training and saving model... Might take a moment")
            train_and_save()
        # Load the trained model and scaler
        model_path_load = './app/model/stock_price_model.joblib'
        model = joblib.load(model_path_load)

        print(model)
        print("Model loaded successfully")
        return model
    except Exception as e:
        print("Error loading model:", e)
        print("Current Working Directory:", os.getcwd())
        return None, None


model = load_model()
# Define stock names
STOCK_NAMES = {
    'TSLA': ('Tesla, Inc. - #E31937'),
    'AAPL': ('Apple Inc. - #A2AAAD'),
    'GOOG': ('Alphabet Inc Class C. - #4285F4'),
    'AMZN': ('Amazon.com, Inc.- #FF9900'),
    'MSFT': ('Microsoft Corporation - #F25022'),
    'META': ('Meta Platforms, Inc. - #1877F2'),
    'NVDA': ('NVIDIA Corporation- #76B900'),
    'NFLX': ('Netflix, Inc.- #E50914'),
    'TSM': ('Taiwan Semiconductor Manufacturing Company Limited - #8B0000')
}

# Home route
def home():
    current_date = datetime.today().strftime('%Y-%m-%d')
    return render_template("dashboard.html", stock_names=STOCK_NAMES, current_date=current_date)

# Add user to MongoDB
def add_user():
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    password = request.form.get('password')
    amount = request.form.get('amount')

    if not all([full_name, email, password, amount]):
        return jsonify({"message": "All fields are required!"}), 400

    user_data = {
        "full_name": full_name,
        "email": email,
        "password": password,
        "amount": amount
    }

    mongo.db.users.insert_one(user_data)
    return jsonify({"message": "User registered successfully!"}), 201

# Get all users from MongoDB
def get_users():
    users = list(mongo.db.users.find({}))
    for user in users:
        user['_id'] = str(user['_id'])
    return jsonify(users)

# Get the day before today's date, adjusting for weekends
def get_day_before(today):
    end_date = datetime.strptime(today, '%Y-%m-%d').date()
    day_before = end_date - timedelta(days=1)

    # Adjust for weekends (Saturday -> Monday, Sunday -> Friday)
    if day_before.weekday() == 6:  # Sunday
        return day_before - timedelta(days=2)  # Return Friday
    elif day_before.weekday() == 5:  # Saturday
        return day_before + timedelta(days=2)  # Return Monday
    return day_before

def fetch_stock_data(ticker, start_date, end_date, color):
    print(f'Start Date: {start_date} - End Date: {end_date}')
    
    # Ticker values model was trained on
    get_ticker = {'AAPL': 0, 'AMZN': 1, 'GOOG': 2, 'META': 3, 'MSFT': 4, 'NFLX': 5, 'NVDA': 6, 'TSLA': 7, 'TSM': 8}
    
    #feature list of model when sending data to model makesure this matches!
    feature_list = ['Close', 'High', 'Low', 'Open', 'Volume', 'ticker', 'day_of_week',
       'hour_of_day', 'month', 'year', 'quarter', 'days_since_start']
    try:
        # Download stock data
        data = yf.download(ticker, start=start_date, end=end_date + timedelta(days=1), interval='15m')

        if data.empty:
            return None

        # Flatten multiindex columns if needed
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)

        # Feature engineering for model
        data['ticker'] = get_ticker[ticker.strip()]
        data['day_of_week'] = data.index.dayofweek  # Monday=0, Sunday=6
        data['hour_of_day'] = data.index.hour  # Hour from 0 to 23
        data['month'] = data.index.month - 1  # 0 for Jan, 11 for Dec
        data['year'] = data.index.year  # 2023, 2024
        data['quarter'] = data.index.quarter  # 1, 2, 3, 4
        data['days_since_start'] = (data.index - data.index[0]).days  # Days from start
    
            
        predictions = model.predict(data)
        
        data['predictions'] = predictions
        
        # Ensure the index is in UTC first, then convert it to 'America/New_York' (or your target timezone)
        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC')  # Localize to UTC if not already
        data.index = data.index.tz_convert('America/New_York')  # Convert to New York time zone
        
        # Filter to keep only the data for the end date
        data = data[data.index.date == pd.to_datetime(end_date).date()]
        
        labels = data.index.strftime('%I:%M %p')
        
        # Prediction block: If data length is less than 26, predict the next point
        if len(data) < 26:
            print("Condition met")
            # If the data length is less than 26, predict the next point
            last_data = data.iloc[-1:].drop(columns='predictions')  # Get the last data point
            pred_arr_last = np.array(last_data)
            
            prediction_next = model.predict(pred_arr_last)  # Predict the next value
            
            # Append the predicted point to the data
            next_time = data.index[-1] + timedelta(minutes=15)  # Assuming the data is every 15 minutes
            next_data_point = pd.DataFrame({
                'predictions': prediction_next,
                'day_of_week': [last_data['day_of_week'].values[0]],
                'hour_of_day': [last_data['hour_of_day'].values[0]],
                'month': [last_data['month'].values[0]],
                'year': [last_data['year'].values[0]],
                'quarter': [last_data['quarter'].values[0]],
                'days_since_start': [last_data['days_since_start'].values[0] + 1],
                'ticker': [last_data['ticker'].values[0]],
                'Close': None,
            }, index=[next_time])  # Ensuring correct DatetimeIndex here

            # Append the new data to the original data (ensuring matching indices)
            data = pd.concat([data, next_data_point])

            # Append the new label (next_time) to the labels
            labels = np.append(labels, next_time.strftime('%I:%M %p'))  # Format next_time as label and add to labels
            print(f"Updated labels: {labels}")  # Check the labels in the console

        # Return updated data and labels
        data_dict = data.to_dict(orient='index')
        data_dict = {str(k): v for k, v in data_dict.items()}  # Convert index to string

        return {'data': data_dict, 'labels': labels.tolist(), 'color': color}  # Convert labels to list if needed

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        return None

# Stock selection and data fetching
def stock_selected():
    if request.method != 'POST':
        return jsonify({'status': 'error', 'message': 'Invalid request method'}), 405

    selected_stock = request.form.get('stock_symbol')
    current_date_str = request.form.get('current_date')

    if not selected_stock or not current_date_str:
        return jsonify({'status': 'error', 'message': 'Missing inputs'}), 400

    try:
        # Parse date and get start
        end_date = datetime.strptime(current_date_str, '%Y-%m-%d').date()
        start_date = get_day_before(current_date_str)  # Ensure we get the previous day correctly

        # Get parts from selected stock string
        ticker, stock_name, color = selected_stock.split("-")

        # Fetch stock data
        data = fetch_stock_data(ticker, start_date, end_date, color)
        if not data:
            return jsonify({'status': 'error', 'message': 'No data found'}), 400

        # Skip the cutoff logic entirely for today
        # (Just return the data as it is)
        return jsonify({
            'status': 'success',
            'message': 'Sending data',
            'stockName': stock_name,
            'stockSymbol': ticker,
            'data': data['data'],
            'labels': data['labels'],
            'color': data['color'],
            'current_date_str':current_date_str
        })

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print("Error in stock_selected:", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500