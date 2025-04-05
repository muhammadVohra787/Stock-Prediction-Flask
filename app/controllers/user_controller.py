from flask import jsonify, request, render_template, redirect, session
from app import mongo
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import joblib
import os
import numpy as np
import sys
from bson.objectid import ObjectId
from ..model.train import train_and_save

# ------------------ Load Model ------------------

def load_model():
    try:
        model_path = './app/model/stock_price_model.joblib'
        if not os.path.exists(model_path):
            print("Training and saving model... Might take a moment")
            train_and_save()
        model = joblib.load(model_path)
        print("Model loaded successfully")
        return model
    except Exception as e:
        print("Error loading model:", e)
        return None

model = load_model()

# ------------------ Constants ------------------

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

# ------------------ Home/Dashboard ------------------

def home():
    if 'user_id' not in session:
        return redirect('/login')
    current_date = datetime.today().strftime('%Y-%m-%d')
    return render_template("dashboard.html", stock_names=STOCK_NAMES, current_date=current_date, userId=session.get('user_id'))

def home_page():
    return render_template("home.html", now=datetime.now)

# ------------------ User Management ------------------

def add_user():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        amount = request.form.get('amount')

        if not all([full_name, email, password, amount]):
            return "All fields are required!", 400

        mongo.db.users.insert_one({
            "full_name": full_name,
            "email": email,
            "password": password,
            "amount": amount
        })

        return redirect('/login')

    return render_template("register.html")


def get_users():
    users = list(mongo.db.users.find({}))
    for user in users:
        user['_id'] = str(user['_id'])
    return jsonify(users)

# ------------------ Stock Logic ------------------

def get_day_before(today):
    end_date = datetime.strptime(today, '%Y-%m-%d').date()
    day_before = end_date - timedelta(days=1)
    if day_before.weekday() == 6:
        return day_before - timedelta(days=2)
    elif day_before.weekday() == 5:
        return day_before + timedelta(days=2)
    return day_before

def fetch_stock_data(ticker, start_date, end_date, color):
    get_ticker = {'AAPL': 0, 'AMZN': 1, 'GOOG': 2, 'META': 3, 'MSFT': 4, 'NFLX': 5, 'NVDA': 6, 'TSLA': 7, 'TSM': 8}
    try:
        data = yf.download(ticker, start=start_date, end=end_date + timedelta(days=1), interval='15m')
        if data.empty: return None
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.droplevel(1)

        data['ticker'] = get_ticker[ticker.strip()]
        data['day_of_week'] = data.index.dayofweek
        data['hour_of_day'] = data.index.hour
        data['month'] = data.index.month - 1
        data['year'] = data.index.year
        data['quarter'] = data.index.quarter
        data['days_since_start'] = (data.index - data.index[0]).days

        data['predictions'] = model.predict(data)

        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC')
        data.index = data.index.tz_convert('America/New_York')
        data = data[data.index.date == pd.to_datetime(end_date).date()]
        labels = data.index.strftime('%I:%M %p')
        print(data)
        if len(data) < 26 and len(data) != 0:
            last_data = data.iloc[-1:].drop(columns='predictions')
            pred_arr_last = np.array(last_data)
            prediction_next = model.predict(pred_arr_last)
            next_time = data.index[-1] + timedelta(minutes=15)
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
            }, index=[next_time])

            data = pd.concat([data, next_data_point])
            labels = np.append(labels, next_time.strftime('%I:%M %p'))

        data_dict = {str(k): v for k, v in data.to_dict(orient='index').items()}
        return {'data': data_dict, 'labels': labels.tolist(), 'color': color}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(exc_type, os.path.split(exc_tb.tb_frame.f_code.co_filename)[1], exc_tb.tb_lineno, e)
        return None

def stock_selected():
    if request.method != 'POST':
        return jsonify({'status': 'error', 'message': 'Invalid request method'}), 405

    selected_stock = request.form.get('stock_symbol')
    current_date_str = request.form.get('current_date')

    if not selected_stock or not current_date_str:
        return jsonify({'status': 'error', 'message': 'Missing inputs'}), 400

    try:
        end_date = datetime.strptime(current_date_str, '%Y-%m-%d').date()
        start_date = get_day_before(current_date_str)
        ticker, stock_name, color = selected_stock.split("-")

        data = fetch_stock_data(ticker, start_date, end_date, color)
        if not data:
            return jsonify({'status': 'error', 'message': 'No data found'}), 400

        return jsonify({
            'status': 'success',
            'message': 'Sending data',
            'stockName': stock_name,
            'stockSymbol': ticker,
            'data': data['data'],
            'labels': data['labels'],
            'color': data['color'],
            'current_date_str': current_date_str
        })

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(exc_type, os.path.split(exc_tb.tb_frame.f_code.co_filename)[1], exc_tb.tb_lineno, e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ------------------ BUY STOCK ------------------

def buy_stock():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    stock_symbol = request.form.get('stock_symbol')
    stock_name = request.form.get('stock_name')
    current_price = float(request.form.get('current_price'))
    quantity = int(request.form.get('quantity'))

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"message": "User not found"}), 404

    total_cost = current_price * quantity
    balance = float(user.get("amount", 0))

    if total_cost > balance:
        return jsonify({"message": "Insufficient funds"}), 400

    mongo.db.holdings.insert_one({
        "user_id": ObjectId(user_id),
        "stock_symbol": stock_symbol,
        "stock_name": stock_name,
        "quantity": quantity,
        "purchase_price": current_price,
        "purchase_date": datetime.now().strftime('%Y-%m-%d')
    })

    mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"amount": balance - total_cost}})
    return redirect('/')

# ------------------ SELL STOCK ------------------

def sell_stock():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    holding_id = request.form.get('holding_id')
    quantity_to_sell = int(request.form.get('quantity'))
    sell_price = float(request.form.get('current_price'))

    holding = mongo.db.holdings.find_one({"_id": ObjectId(holding_id)})

    if not holding or holding["user_id"] != ObjectId(user_id):
        return jsonify({"message": "Holding not found"}), 404

    total_earnings = sell_price * quantity_to_sell

    if quantity_to_sell >= holding['quantity']:
        mongo.db.holdings.delete_one({"_id": ObjectId(holding_id)})
    else:
        mongo.db.holdings.update_one({"_id": ObjectId(holding_id)}, {"$inc": {"quantity": -quantity_to_sell}})

    mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$inc": {"amount": total_earnings}})
    return redirect('/')

# ------------------ GET HOLDINGS ------------------

def get_holdings(user_id):
    holdings = list(mongo.db.holdings.find({"user_id": ObjectId(user_id)}))
    for h in holdings:
        h['_id'] = str(h['_id'])
    return jsonify(holdings)

# ------------------ LOGIN / LOGOUT ------------------

def login_user():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = mongo.db.users.find_one({"email": email, "password": password})
        if user:
            session['user_id'] = str(user['_id'])
            return redirect('/')
        return "Invalid credentials", 401
    return render_template('login.html')

def logout_user():
    session.clear()
    return redirect('/login')
