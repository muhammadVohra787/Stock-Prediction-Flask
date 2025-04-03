# app/controllers/user_controller.py
from flask import jsonify, request, render_template
from app import mongo
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from flask import jsonify
import json
import pytz
import datetime as dt
import joblib
import os

try:
    model_path="./app/controllers/stock_model.joblib"
    model = joblib.load(model_path)
    print(model)
except Exception as e:
    print("Current Working Directory:", os.getcwd())
    print(e)

def home():
    stock_names = {
        'TSLA': ('Tesla, Inc. - #E31937'),
        'AAPL': ('Apple Inc. - #A2AAAD'),
        'GOOG': ('Alphabet Inc. (Class C) - #4285F4'),
        'AMZN': ('Amazon.com, Inc.- #FF9900'),
        'MSFT': ('Microsoft Corporation - #F25022'),
        'META': ('Meta Platforms, Inc. - #1877F2'),
        'NVDA': ('NVIDIA Corporation- #76B900'),
        'NFLX': ('Netflix, Inc.- #E50914'),
        'TSM': ('Taiwan Semiconductor Manufacturing Company Limited - #8B0000')
    }

    current_date = datetime.today()

    #We do not have live data in this app..
    yesterday_date = (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
    return render_template("dashboard.html", stock_names=stock_names, current_date=yesterday_date)

def add_user():
    # Get form data from the request
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    password = request.form.get('password')
    amount = request.form.get('amount')  # The selected trading amount

    # Optionally: Validate the form data (e.g., check if required fields are empty)
    if not full_name or not email or not password or not amount:
        return jsonify({"message": "All fields are required!"}), 400

    # Insert data into MongoDB
    user_data = {
        "full_name": full_name,
        "email": email,
        "password": password,  # You may want to hash the password before storing it
        "amount": amount
    }

    mongo.db.users.insert_one(user_data)  # Insert data into 'users' collection

    return jsonify({"message": "User registered successfully!"}), 201

def get_users():
    users = list(mongo.db.users.find({}))  # Get all users, exclude _id
    for user in users:
        user['_id'] = str(user['_id'])  # Convert ObjectId to string
    return jsonify(users)

def get_day_before(today):
    end_date = datetime.strptime(today, '%Y-%m-%d').date()
    day_before = end_date - timedelta(days=1)

    if day_before.weekday() == 6:  # Sunday (Monday is 0, Sunday is 6)
        return day_before - timedelta(days=2)  # Return Friday
    elif day_before.weekday() == 5:  # Saturday
        return day_before + timedelta(days=2)  # Return Monday
    else:
        return day_before

def fetch_stock_data(ticker, start_date, end_date, color):
    data = yf.download(tickers=ticker, start=start_date, end=end_date, interval="15m")

    if data.empty:
        return None

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)

    if data.index.tz is None:
        data.index = data.index.tz_localize('UTC')
    else:
        data.index = data.index.tz_convert('UTC')

    # Convert index to Eastern Time for labels
    eastern_tz = pytz.timezone('America/New_York')
    data.index = data.index.tz_convert(eastern_tz)

    labels = data.index.strftime('%I:%M %p')
    data.index = data.index.strftime('%Y-%m-%d %H:%M:%S')  # Convert index back to string for JSON
    data_dict = data.to_dict(orient="index")

    return {'data': data_dict, 'labels': labels, 'color': color}

def stock_selected():
    if request.method == 'POST':
        selected_stock = request.form.get('stock_symbol')
        current_date_str = request.form.get('current_date')

        if not selected_stock:
            return jsonify({'status': 'error', 'message': 'No stock symbol received'}), 400

        try:
            end_date = datetime.strptime(current_date_str, '%Y-%m-%d').date()
            start_date = get_day_before(current_date_str)

            # Get today's date in Toronto timezone
            toronto_tz = pytz.timezone('America/Toronto')
            now_toronto = datetime.now(toronto_tz)

            # Calculate yesterday's date in Toronto
            yesterday_toronto = now_toronto.date() - timedelta(days=1)

            # Check if the current_date from the request is yesterday
            if current_date_str == yesterday_toronto.strftime('%Y-%m-%d'):
                # Get current Toronto time in UTC for comparison
                now_utc = now_toronto.astimezone(pytz.utc)

                # Create the cutoff datetime for yesterday with today's time
                cutoff_yesterday_utc = datetime(yesterday_toronto.year, yesterday_toronto.month, yesterday_toronto.day,
                                                 now_utc.hour, now_utc.minute, now_utc.second, tzinfo=pytz.utc)

                ticker, stock_name, color = selected_stock.split("-")
                data = fetch_stock_data(ticker, start_date, end_date, color)

                if not data:
                    return jsonify({'status': 'error', 'message': 'No data found for the given stock symbol'}), 400

                # Filter data up to the cutoff time
                data['data'] = {k: v for k, v in data['data'].items() if k <= cutoff_yesterday_utc.strftime('%Y-%m-%d %H:%M:%S')}

                return jsonify({'status': 'success', 'message': 'sending data', 'stockName': stock_name, 'stockSymbol': ticker, 'data': data['data'], 'labels': data['labels'], 'color': data['color']})

            else:
                ticker, stock_name, color = selected_stock.split("-")
                data = fetch_stock_data(ticker, start_date, end_date, color)

                if not data:
                    return jsonify({'status': 'error', 'message': 'No data found for the given stock symbol'}), 400

                return jsonify({'status': 'success', 'message': 'sending data', 'stockName': stock_name, 'stockSymbol': ticker, 'data': data['data'], 'labels': data['labels'], 'color': data['color']})

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    return jsonify({'status': 'error', 'message': 'Invalid request method'}), 405