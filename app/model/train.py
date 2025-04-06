import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split,cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error,mean_squared_error
import pandas as pd
import numpy as np
import joblib
model_path= './app/model/stock_price_model.joblib'

def train_and_save():
    
    # List of stock tickers
    tickers = ['TSLA', 'AAPL', 'GOOG', 'AMZN', 'MSFT', 'META', 'NVDA', 'NFLX', 'TSM']
    # tickers = ['AMZN']

    # Empty list to store processed data for all stocks
    all_data = []

    # Download and preprocess data for each stock
    for ticker in tickers:
        data = yf.download(ticker, period='60d', interval='15m')

        # Drop MultiIndex if it exists
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        # # Add stock ticker as a feature
        data['ticker'] = ticker

        data = pd.DataFrame(data, columns=data.columns, index=data.index)
        data['day_of_week'] = data.index.dayofweek  # Monday=0, Sunday=6
        data['hour_of_day'] = data.index.hour  # Hour from 0 to 23
        data['month'] = data.index.month - 1  # 0 for Jan, 11 for Dec
        data['year'] = data.index.year  # 2023, 2024
        data['quarter'] = data.index.quarter  # 1, 2, 3, 4
        data['days_since_start'] = (data.index - data.index[0]).days  # Days from start
        
         # Check if the last date is a weekend (Saturday or Sunday)
        last_date = data.index[-1]
        if last_date.weekday() == 5:  # Saturday
        # Adjust to Friday
           data = data[data.index < last_date]
        elif last_date.weekday() == 6:  # Sunday
        # Adjust to Friday
           data = data[data.index < last_date - pd.Timedelta(days=2)]

        # Define the target (next hour's closing price)
        data['target'] = data['Close'].shift(-1)

        X = data.drop(columns=['target'])
        y = data['target']

        # Store in list
        all_data.append(data)
        
    # Combine all stock data into a single DataFrame
    full_data = pd.concat(all_data)

    # Define feature columns
    features = ['Open', 'High', 'Low', 'Close', 'Volume',
                'day_of_week', 'hour_of_day', 'month', 'quarter']

    # Encode stock ticker (convert categorical data to numerical values)
    full_data['ticker'] = full_data['ticker'].astype('category').cat.codes  # Convert tickers to numeric values

    full_data = full_data.dropna(subset=['target'])

    X = full_data.drop(columns=['target'])
    y = full_data['target']

    # Convert to numpy arrays
    X = np.array(X)
    y = np.array(y)

    # Split data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    reg = LinearRegression().fit(X_train, y_train)
    train_score = reg.score(X_train, y_train)
    test_score = reg.score(X_test, y_test)

    print(f"Train Score: {train_score:.4f}")
    print(f"Test Score: {test_score:.4f}")

    cv_scores = cross_val_score(reg, X, y, cv=5)
    print(f"Cross-validation mean score: {np.mean(cv_scores):.4f}")


    y_pred_list = reg.predict(X_test) 
    

    mae = mean_absolute_error(y_test, y_pred_list)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred_list))

    print(f'Mean Absolute Error: {mae:.4f}')
    print(f'Root Mean Squared Error: {rmse:.4f}')

    # Save the trained model (including weights) to a file
    joblib.dump(reg, model_path)

    print("Model saved successfully!")

    ## Sample data
    client_dict={
        "2025-04-01 09:30:00-04:00": {
            "Close": 264.7550048828125,
            "High": 268.1199951171875,
            "Low": 259.25,
            "Open": 263.7349853515625,
            "Volume": 18642264,
            "day_of_week": 1,
            "hour_of_day": 13,
            "month": 3,
            "year": 2025,
            "quarter": 2,
            "days_since_start": 1,
            "ticker": 7,
            "predictions": 23.578555580272592
        },
        "2025-04-01 09:45:00-04:00": {
            "Close": 263.82000732421875,
            "High": 266.4700012207031,
            "Low": 262.16009521484375,
            "Open": 264.7550048828125,
            "Volume": 6434412,
            "day_of_week": 1,
            "hour_of_day": 13,
            "month": 3,
            "year": 2025,
            "quarter": 2,
            "days_since_start": 1,
            "ticker": 7,
            "predictions": 22.663544253319202
        },
    }

    featurelist= full_data.columns
    featurelist = featurelist[:-1]
    featurelist


    for k, v in client_dict.items():
        if 'predictions' in v:
            del v['predictions']

        feature_values = [v[f] for f in featurelist]

        feature_array = np.array(feature_values).reshape(1, -1)

        prediction = reg.predict(feature_array)
        print(f"Prediction for {k}: {prediction}")