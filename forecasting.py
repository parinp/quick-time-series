import pandas as pd
import numpy as np
import yfinance as yf
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import datetime

# Step 1: Load Data (Stock Prices & Google Trends)
def get_stock_data(ticker, start_date, end_date):
    stock = yf.download(ticker, start=start_date, end=end_date)
    stock = stock[['Adj Close']]
    stock = stock.rename(columns={'Adj Close': 'close'})
    stock['date'] = stock.index
    return stock

# Replace with actual Google Trends data retrieval
def get_google_trends_data():
    dates = pd.date_range(start='2023-01-01', end=datetime.date.today())
    trends = np.random.randint(50, 100, len(dates))  # Placeholder data
    return pd.DataFrame({'date': dates, 'google_trends': trends})

# Step 2: Feature Engineering
def create_features(df):
    df['day_of_week'] = df['date'].dt.weekday
    df['month'] = df['date'].dt.month
    df['lag_1'] = df['close'].shift(1)
    df['lag_2'] = df['close'].shift(2)
    df['lag_7'] = df['close'].shift(7)
    df['ma_7'] = df['close'].rolling(7).mean()
    return df.dropna()

# Step 3: Train Model
def train_xgboost(df):
    X = df[['day_of_week', 'month', 'lag_1', 'lag_2', 'lag_7', 'ma_7', 'google_trends']]
    y = df['close']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    error = mean_absolute_error(y_test, predictions)
    print(f'Model MAE: {error:.2f}')
    return model

# Step 4: Forecast Next N Days
def forecast_next_n_days(model, last_data, n=7):
    future_dates = [last_data['date'].max() + datetime.timedelta(days=i) for i in range(1, n+1)]
    future_data = pd.DataFrame({'date': future_dates})
    future_data['day_of_week'] = future_data['date'].dt.weekday
    future_data['month'] = future_data['date'].dt.month
    future_data['lag_1'] = last_data['close'].iloc[-1]
    future_data['lag_2'] = last_data['close'].iloc[-2]
    future_data['lag_7'] = last_data['close'].iloc[-7]
    future_data['ma_7'] = last_data['ma_7'].iloc[-1]
    future_data['google_trends'] = last_data['google_trends'].iloc[-1]
    future_prices = model.predict(future_data[['day_of_week', 'month', 'lag_1', 'lag_2', 'lag_7', 'ma_7', 'google_trends']])
    return pd.DataFrame({'date': future_dates, 'predicted_close': future_prices})

# Run pipeline
ticker = 'AAPL'
start_date = '2023-01-01'
end_date = datetime.date.today().strftime('%Y-%m-%d')

stock_data = get_stock_data(ticker, start_date, end_date)
google_trends = get_google_trends_data()
data = stock_data.merge(google_trends, on='date', how='left')
data = create_features(data)

model = train_xgboost(data)
forecast = forecast_next_n_days(model, data, n=7)
print(forecast)
