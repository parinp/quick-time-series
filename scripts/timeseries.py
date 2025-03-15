import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
import xgboost as xgb
import shap
from causalimpact import CausalImpact
from prophet import Prophet
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')


def load_csv():
    """Loads a CSV file with error handling."""
    while True:
        file_path = input("Enter the path to your sales CSV file: ").strip()
        try:
            df = pd.read_csv(file_path, parse_dates=True, encoding='unicode_escape')
            print("File loaded successfully!")
            return df
        except FileNotFoundError:
            print("Error: File not found. Please check the path and try again.")
        except pd.errors.EmptyDataError:
            print("Error: The file is empty.")
        except pd.errors.ParserError:
            print("Error: File could not be parsed. Ensure it is a valid CSV.")


def select_columns(df):
    """Allows the user to select the date and sales column, with auto-detection for sales."""
    print("\nColumns in dataset:", df.columns.tolist())

    # Select date column
    while True:
        date_col = input("Enter the date column name: ").strip()
        if date_col in df.columns:
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                break
            except Exception as e:
                print(f"Error converting {date_col} to datetime: {e}")
        else:
            print("Error: Column not found. Please enter a valid column name.")

    # Auto-detect sales column (highest variance numerical column)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if date_col in num_cols:
        num_cols.remove(date_col)

    if num_cols:
        sales_col = max(num_cols, key=lambda col: df[col].var())
        print(f"Auto-detected sales column: {sales_col}")
        confirm = input(f"Use {sales_col} as the sales/target column? (y/n): ").lower()
        if confirm != 'y':
            while True:
                sales_col = input("Enter the sales column name: ").strip()
                if sales_col in df.columns and np.issubdtype(df[sales_col].dtype, np.number):
                    break
                print("Error: Column not found or not numeric. Please enter a valid sales column.")
    else:
        while True:
            sales_col = input("Enter the sales column name: ").strip()
            if sales_col in df.columns and np.issubdtype(df[sales_col].dtype, np.number):
                break
            print("Error: Column not found or not numeric. Please enter a valid sales column.")

    return df, date_col, sales_col


def perform_basic_eda(df, date_col, sales_col):
    """Performs basic EDA on the sales data."""
    print("\n===== Basic Exploratory Data Analysis =====")
    
    # Basic statistics
    print(f"\nSummary Statistics for {sales_col}:")
    print(df[sales_col].describe())
    
    # Check for missing values
    missing_values = df.isnull().sum()
    print("\nMissing Values:")
    print(missing_values[missing_values > 0] if any(missing_values > 0) else "No missing values found")
    
    # Check data frequency
    if len(df) > 1:
        date_diff = df[date_col].sort_values().diff().dropna()
        freq_seconds = date_diff.dt.total_seconds().value_counts().index[0]
        if freq_seconds % (24*60*60) == 0:
            days = int(freq_seconds / (24*60*60))
            if days == 1:
                freq = "Daily"
            elif days == 7:
                freq = "Weekly"
            elif days in [28, 29, 30, 31]:
                freq = "Monthly"
            else:
                freq = f"{days} Days"
        elif freq_seconds % (60*60) == 0:
            freq = f"{int(freq_seconds / (60*60))} Hours"
        else:
            freq = "Irregular"
        print(f"\nData Frequency: {freq}")
    
    # Plot time series
    plt.figure(figsize=(12, 6))
    plt.plot(df[date_col], df[sales_col])
    plt.title(f'{sales_col} Over Time')
    plt.xlabel('Date')
    plt.ylabel(sales_col)
    plt.grid(True)
    plt.show()
    
    # Distribution of sales
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    sns.histplot(df[sales_col], kde=True)
    plt.title(f'Distribution of {sales_col}')
    
    plt.subplot(1, 2, 2)
    sns.boxplot(y=df[sales_col])
    plt.title(f'Boxplot of {sales_col}')
    plt.tight_layout()
    plt.show()
    
    return df


def add_time_features(df, date_col):
    """Add time-based features to the dataset."""
    df['year'] = df[date_col].dt.year
    df['month'] = df[date_col].dt.month
    df['day_of_month'] = df[date_col].dt.day
    df['day_of_week'] = df[date_col].dt.dayofweek
    df['day_of_year'] = df[date_col].dt.dayofyear
    df['week_of_year'] = df[date_col].dt.isocalendar().week
    df['quarter'] = df[date_col].dt.quarter
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    df['is_month_start'] = df[date_col].dt.is_month_start.astype(int)
    df['is_month_end'] = df[date_col].dt.is_month_end.astype(int)
    df['is_quarter_start'] = df[date_col].dt.is_quarter_start.astype(int)
    df['is_quarter_end'] = df[date_col].dt.is_quarter_end.astype(int)
    df['is_year_start'] = df[date_col].dt.is_year_start.astype(int)
    df['is_year_end'] = df[date_col].dt.is_year_end.astype(int)
    
    print("\nAdded time-based features to dataset.")
    return df


def analyze_time_patterns(df, date_col, sales_col):
    """Analyzes sales patterns by different time periods."""
    print("\n===== Time-based Sales Patterns =====")
    
    # Set date as index
    df_time = df.copy()
    df_time.set_index(date_col, inplace=True)
    
    # Monthly pattern
    monthly_avg = df_time.groupby(df_time.index.month)[sales_col].mean()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_avg.index = [months[i-1] for i in monthly_avg.index]
    
    # Day of week pattern
    dow_avg = df_time.groupby(df_time.index.dayofweek)[sales_col].mean()
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dow_avg.index = [days[i] for i in dow_avg.index]
    
    # Plots
    plt.figure(figsize=(15, 10))
    
    plt.subplot(2, 2, 1)
    sns.barplot(x=monthly_avg.index, y=monthly_avg.values)
    plt.title('Average Sales by Month')
    plt.xticks(rotation=45)
    
    plt.subplot(2, 2, 2)
    sns.barplot(x=dow_avg.index, y=dow_avg.values)
    plt.title('Average Sales by Day of Week')
    
    # Yearly trend (if multiple years exist)
    if df_time.index.year.nunique() > 1:
        yearly_avg = df_time.groupby(df_time.index.year)[sales_col].mean()
        plt.subplot(2, 2, 3)
        sns.lineplot(x=yearly_avg.index, y=yearly_avg.values, marker='o')
        plt.title('Average Sales by Year')
        plt.xlabel('Year')
    
    # Time heatmap (month vs day of week)
    if len(df) >= 30:  # Ensure enough data
        plt.subplot(2, 2, 4)
        heatmap_data = df.pivot_table(
            index='day_of_week', 
            columns='month', 
            values=sales_col, 
            aggfunc='mean'
        )
        heatmap_data.index = days
        heatmap_data.columns = [months[i-1] for i in heatmap_data.columns]
        sns.heatmap(heatmap_data, cmap="YlGnBu", annot=True, fmt=".0f", linewidths=.5)
        plt.title('Sales Heatmap: Day of Week vs Month')
    
    plt.tight_layout()
    plt.show()
    
    # Interactive time analysis with Plotly
    try:
        # Monthly trend over years
        monthly_data = df.groupby([df[date_col].dt.year, df[date_col].dt.month])[sales_col].mean().reset_index()
        monthly_data['date'] = pd.to_datetime(monthly_data[date_col.name].astype(str) + '-' + monthly_data['month'].astype(str) + '-01')
        
        fig = px.line(monthly_data, x='date', y=sales_col, title=f'Monthly {sales_col} Trend')
        fig.update_xaxes(title_text='Date')
        fig.update_yaxes(title_text=sales_col)
        fig.show()
    except Exception as e:
        print(f"Couldn't create interactive plot: {e}")
    
    return df


def detect_anomalies(df, sales_col):
    """Performs anomaly detection using Isolation Forest and STL decomposition."""
    print("\n===== Anomaly Detection =====")
    
    try:    
        # Isolation Forest
        iso_forest = IsolationForest(contamination=0.05, random_state=42)
        df['anomaly_iso'] = iso_forest.fit_predict(df[[sales_col]])
        df['anomaly_iso'] = df['anomaly_iso'].map({1: 0, -1: 1})  # Convert to 0/1
        
        # STL Decomposition
        df_sorted = df.sort_index()
        stl = STL(df_sorted[sales_col], period=12, seasonal=13)
        res = stl.fit()
        df_sorted['trend'] = res.trend
        df_sorted['seasonal'] = res.seasonal
        df_sorted['residual'] = res.resid
        
        residual_threshold = 2.5 * df_sorted['residual'].std()
        df_sorted['anomaly_stl'] = (abs(df_sorted['residual']) > residual_threshold).astype(int)
        
        # Merge back
        df = df.merge(df_sorted[['trend', 'seasonal', 'residual', 'anomaly_stl']], 
                        left_index=True, right_index=True, how='left')
        
        # Combined anomaly flag
        df['is_anomaly'] = ((df['anomaly_iso'] == 1) | (df['anomaly_stl'] == 1)).astype(int)
        
        # Plot results
        fig = make_subplots(rows=3, cols=1,
                            subplot_titles=('Original Time Series with Anomalies', 
                                            'Trend and Seasonal Components', 
                                            'Residuals'))
        
        # Original series with anomalies
        fig.add_trace(
            go.Scatter(x=df.index, y=df[sales_col], mode='lines', name='Sales'),
            row=1, col=1
        )
        
        anomalies = df[df['is_anomaly'] == 1]
        fig.add_trace(
            go.Scatter(x=anomalies.index, y=anomalies[sales_col], 
                        mode='markers', name='Anomalies', marker=dict(color='red', size=10)),
            row=1, col=1
        )
        
        # Trend and seasonal
        fig.add_trace(
            go.Scatter(x=df.index, y=df['trend'], mode='lines', name='Trend'),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=df.index, y=df['seasonal'], mode='lines', name='Seasonal'),
            row=2, col=1
        )
        
        # Residuals
        fig.add_trace(
            go.Scatter(x=df.index, y=df['residual'], mode='lines', name='Residual'),
            row=3, col=1
        )
        
        fig.add_shape(
            type="line", line=dict(dash='dash', color='red'),
            x0=df.index.min(), y0=residual_threshold, 
            x1=df.index.max(), y1=residual_threshold,
            row=3, col=1
        )
        
        fig.add_shape(
            type="line", line=dict(dash='dash', color='red'),
            x0=df.index.min(), y0=-residual_threshold, 
            x1=df.index.max(), y1=-residual_threshold,
            row=3, col=1
        )
        
        fig.update_layout(height=800, title_text=f"Anomaly Detection for {sales_col}")
        fig.show()
        
        print(f"\nDetected {df['is_anomaly'].sum()} anomalies in the data")
        
        # Summary of anomalies
        if df['is_anomaly'].sum() > 0:
            print("\nTop 10 Anomalies:")
            top_anomalies = df[df['is_anomaly'] == 1].sort_values(by='residual', key=abs, ascending=False)
            print(top_anomalies[[df.index, sales_col, 'residual']].head(10))

    except Exception as e:
        print(f"Error in anomaly detection: {e}")
    
    return df


def test_stationarity(df, sales_col):
    """Tests time series stationarity using ADF test and plots."""
    print("\n===== Stationarity Tests =====")
    
    # ADF Test
    result = adfuller(df[sales_col].dropna())
    print('Augmented Dickey-Fuller Test:')
    print(f'ADF Statistic: {result[0]}')
    print(f'p-value: {result[1]}')
    is_stationary = result[1] < 0.05
    print(f'Is series stationary? {"Yes" if is_stationary else "No"}')
    
    # Plot rolling statistics
    rolling_mean = df[sales_col].rolling(window=12).mean()
    rolling_std = df[sales_col].rolling(window=12).std()
    
    plt.figure(figsize=(12, 6))
    plt.plot(df[sales_col], label='Original')
    plt.plot(rolling_mean, label='Rolling Mean')
    plt.plot(rolling_std, label='Rolling Std')
    plt.legend()
    plt.title('Rolling Mean & Standard Deviation')
    plt.show()
    
    # Plot ACF and PACF
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    plot_acf(df[sales_col].dropna(), ax=ax1, lags=30)
    plot_pacf(df[sales_col].dropna(), ax=ax2, lags=30)
    plt.tight_layout()
    plt.show()
    
    return is_stationary


def analyze_seasonality(df, sales_col):
    """Analyzes seasonality pattern in the time series."""
    print("\n===== Seasonality Analysis =====")
    
    # Make sure data is sorted by date
    df_ts = df.copy(deep=True)
    df_ts.sort_index(inplace=True)
    
    # Decompose time series
    try:
        # Set date as index for time series functions
        
        # Check if we have enough data for seasonal decomposition
        if len(df_ts) < 14:
            print("Not enough data for seasonal decomposition (need at least 14 data points)")
            return df
        
        # Try to determine seasonality automatically
        acf_values = acf(df_ts[sales_col].dropna(), nlags=len(df_ts) // 2)
        candidate_periods = []
        for i in range(2, len(acf_values) // 3):
            if acf_values[i] > 0.5 and acf_values[i] > acf_values[i-1] and acf_values[i] > acf_values[i+1]:
                candidate_periods.append(i)
        
        seasonal_period = 12  # Default to 12 (monthly)
        if candidate_periods:
            seasonal_period = candidate_periods[0]
            print(f"Automatically detected seasonal period: {seasonal_period}")
        else:
            print(f"No strong seasonality detected. Using default period: {seasonal_period}")
        
        # STL Decomposition
        stl = STL(df_ts[sales_col], period=seasonal_period)
        res = stl.fit()
        
        # Plot decomposition
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 10))
        ax1.plot(df_ts.index, df_ts[sales_col])
        ax1.set_title('Original Series')
        
        ax2.plot(df_ts.index, res.trend)
        ax2.set_title('Trend Component')
        
        ax3.plot(df_ts.index, res.seasonal)
        ax3.set_title('Seasonal Component')
        
        ax4.plot(df_ts.index, res.resid)
        ax4.set_title('Residual Component')
        
        plt.tight_layout()
        plt.show()
        
        # Calculate seasonal strength
        seasonal_strength = 1 - (np.var(res.resid) / np.var(res.seasonal + res.resid))
        print(f"Seasonal Strength: {seasonal_strength:.4f}")
        if seasonal_strength > 0.6:
            print("Strong seasonality detected")
        elif seasonal_strength > 0.3:
            print("Moderate seasonality detected")
        else:
            print("Weak seasonality detected")
        
        # Add decomposition components to dataframe
        df['trend_component'] = np.nan
        df['seasonal_component'] = np.nan
        df['residual_component'] = np.nan
        
        df.loc[df_ts.index, 'trend_component'] = res.trend
        df.loc[df_ts.index, 'seasonal_component'] = res.seasonal
        df.loc[df_ts.index, 'residual_component'] = res.resid
                
        # Additional seasonal analysis - Seasonal plot
        if seasonal_period <= 12:  # Only for reasonable periods
            # Create seasonal plot
            plt.figure(figsize=(12, 6))
            for year in df.year.unique():
                subset = df[df.year == year]
                plt.plot(subset.month, subset[sales_col], label=str(year))
            
            plt.title('Seasonal Plot by Month')
            plt.xlabel('Month')
            plt.ylabel(sales_col)
            plt.legend()
            plt.grid(True)
            plt.show()
    
    except Exception as e:
        print(f"Error in seasonality analysis: {e}")
    
    return df


def create_lag_features(df, sales_col, date_col, lags=[1, 7, 30]):
    """Creates lag features for time series data."""
    print("\n===== Creating Lag Features =====")
    
    df_sorted = df.sort_values(by=date_col).copy()
    
    for lag in lags:
        df_sorted[f'lag_{lag}'] = df_sorted[sales_col].shift(lag)
        
        # Also create percentage change features
        df_sorted[f'pct_change_{lag}'] = df_sorted[sales_col].pct_change(periods=lag)
    
    # Create rolling window features
    windows = [7, 14, 30]
    for window in windows:
        if len(df) > window:
            df_sorted[f'rolling_mean_{window}'] = df_sorted[sales_col].rolling(window=window).mean()
            df_sorted[f'rolling_std_{window}'] = df_sorted[sales_col].rolling(window=window).std()
            
            # Expanding mean - cumulative average up to current point
            df_sorted[f'expanding_mean'] = df_sorted[sales_col].expanding().mean()
    
    # Create trend indicator
    if len(df) >= 3:
        df_sorted['short_trend'] = df_sorted[sales_col].rolling(window=3).apply(
            lambda x: 1 if (x.iloc[2] > x.iloc[0]) else (-1 if (x.iloc[2] < x.iloc[0]) else 0)
        )
    
    # Create seasonality features if enough data (simple fourier terms)
    if len(df) >= 30:
        for period in [6, 12]:
            for order in [1, 2]:
                df_sorted[f'sin_{period}_{order}'] = np.sin(order * 2 * np.pi * df_sorted.index / period)
                df_sorted[f'cos_{period}_{order}'] = np.cos(order * 2 * np.pi * df_sorted.index / period)
    
    # Print created features
    new_features = [col for col in df_sorted.columns if col not in df.columns]
    print(f"Created {len(new_features)} new features: {', '.join(new_features)}")
    
    return df_sorted


def feature_importance_analysis(df, sales_col, date_col):
    """Uses XGBoost and SHAP to analyze feature importance."""
    print("\n===== Feature Importance Analysis =====")
    
    try:
        # Filter numeric columns only
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if date_col in num_cols:
            num_cols.remove(date_col)
        if sales_col in num_cols:
            num_cols.remove(sales_col)
        
        # Check if we have enough features and data
        if len(num_cols) < 2:
            print("Not enough numeric features for analysis")
            return df
        
        # Remove rows with NaN (from lag features)
        df_clean = df.dropna().copy()
        if len(df_clean) < len(df) * 0.5:  # If too many rows lost
            print(f"Warning: {len(df) - len(df_clean)} rows dropped due to missing values")
        
        # Prepare training data
        X = df_clean[num_cols]  # Features
        y = df_clean[sales_col]  # Target variable
        
        # Train XGBoost model
        model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Feature importance plot
        plt.figure(figsize=(12, 6))
        xgb.plot_importance(model, max_num_features=20, height=0.5)
        plt.title(f'XGBoost Feature Importance for {sales_col}')
        plt.tight_layout()
        plt.show()
        
        # SHAP values for more detailed feature importance
        explainer = shap.Explainer(model)
        shap_values = explainer(X)
        
        # Summary plot
        plt.figure(figsize=(12, 8))
        shap.summary_plot(shap_values, X, plot_size=(12, 8))
        plt.show()
        
        # Detailed SHAP plots for top features
        top_features = model.feature_importances_.argsort()[-5:][::-1]
        for i in top_features:
            feature_name = X.columns[i]
            plt.figure(figsize=(10, 4))
            shap.dependence_plot(feature_name, shap_values.values, X, show=False)
            plt.title(f'SHAP Dependence Plot for {feature_name}')
            plt.tight_layout()
            plt.show()
        
        # Store importance in dataframe
        importance_df = pd.DataFrame({
            'Feature': X.columns,
            'Importance': model.feature_importances_
        }).sort_values('Importance', ascending=False)
        
        print("\nTop 10 Most Important Features:")
        print(importance_df.head(10))
        
        # Find the most influential time features
        time_features = [f for f in importance_df['Feature'] if any(x in f for x in ['month', 'day', 'week', 'year', 'is_'])]
        if time_features:
            print("\nMost Important Time Features:")
            for feat in time_features[:5]:
                print(f"- {feat}")
        
        # Find the most influential lag features
        lag_features = [f for f in importance_df['Feature'] if 'lag_' in f or 'rolling_' in f]
        if lag_features:
            print("\nMost Important Lag Features:")
            for feat in lag_features[:5]:
                print(f"- {feat}")

    except Exception as e:
        print(f"Error in feature importance analysis: {e}")
    
    return df


def forecast_models(df, date_col, sales_col):
    """Forecasts future sales using various time series models."""
    print("\n===== Sales Forecasting =====")
    
    try:
        # Create time series dataframe
        df_ts = df[[date_col, sales_col]].sort_values(by=date_col).copy()
        df_ts = df_ts.set_index(date_col)
        
        # Determine forecast horizon
        forecast_periods = min(int(len(df_ts) * 0.2), 30)  # 20% of data or 30 periods max
        train_size = len(df_ts) - forecast_periods
        
        train = df_ts.iloc[:train_size]
        test = df_ts.iloc[train_size:]
        
        print(f"Training on {len(train)} periods, testing on {len(test)} periods")
        
        results = {}
        predictions = {}
        
        # 1. Exponential Smoothing (Holt-Winters)
        try:
            hw_model = ExponentialSmoothing(
                train, 
                seasonal_periods=12, 
                trend='add', 
                seasonal='add',
                use_boxcox=True
            ).fit()
            hw_pred = hw_model.forecast(len(test))
            
            results['Holt-Winters'] = np.sqrt(np.mean((test - hw_pred) ** 2))
            predictions['Holt-Winters'] = hw_pred
        except Exception as e:
            print(f"Holt-Winters error: {e}")
        
        # 2. ARIMA
        try:
            arima_model = ARIMA(train, order=(1, 1, 1)).fit()
            arima_pred = arima_model.forecast(len(test))
            
            results['ARIMA'] = np.sqrt(np.mean((test - arima_pred) ** 2))
            predictions['ARIMA'] = arima_pred
        except Exception as e:
            print(f"ARIMA error: {e}")
        
        # 3. Prophet
        try:
            # Prepare data for Prophet
            prophet_train = pd.DataFrame({
                'ds': train.index,
                'y': train.values.ravel()
            })
            
            prophet_model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
            prophet_model.fit(prophet_train)
            
            future = pd.DataFrame({'ds': test.index})
            prophet_pred = prophet_model.predict(future)
            
            results['Prophet'] = np.sqrt(np.mean((test.values.ravel() - prophet_pred['yhat']) ** 2))
            predictions['Prophet'] = pd.Series(prophet_pred['yhat'].values, index=test.index)
            
            # Plot Prophet components
            fig = prophet_model.plot_components(prophet_pred)
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print(f"Prophet error: {e}")
        
        # Print performance metrics
        if results:
            print("\nForecast Model Performance (RMSE):")
            for model, rmse in results.items():
                print(f"{model}: {rmse:.2f}")
            
            # Plot forecasts
            plt.figure(figsize=(12, 6))
            plt.plot(train.index, train, label='Training Data')
            plt.plot(test.index, test, label='Actual')
            
            for model, pred in predictions.items():
                plt.plot(test.index, pred, label=f'{model} Forecast')
            
            plt.title('Sales Forecasting')
            plt.legend()
            plt.grid(True)
            plt.show()
            
            # Future forecast with best model
            best_model = min(results, key=results.get)
            print(f"\nBest performing model: {best_model}")
            
            # Generate future forecast
            future_periods = 12  # Forecast 12 periods ahead
            
            if best_model == 'Holt-Winters':
                future_dates = pd.date_range(
                    start=df_ts.index[-1] + pd.Timedelta(days=1),
                    periods=future_periods,
                    freq=pd.infer_freq(df_ts.index)
                )
                
                hw_model = ExponentialSmoothing(
                    df_ts, 
                    seasonal_periods=12, 
                    trend='add', 
                    seasonal='add',
                    use_boxcox=True
                ).fit()
                
                future_forecast = hw_model.forecast(future_periods)
                future_forecast = pd.Series(future_forecast, index=future_dates)
                
            elif best_model == 'ARIMA':
                future_dates = pd.date_range(
                    start=df_ts.index[-1] + pd.Timedelta(days=1),
                    periods=future_periods,
                    freq=pd.infer_freq(df_ts.index)
                )
                
                arima_model = ARIMA(df_ts, order=(1, 1, 1)).fit()
                future_forecast = arima_model.forecast(future_periods)
                future_forecast = pd.Series(future_forecast, index=future_dates)
                
            elif best_model == 'Prophet':
                prophet_data = pd.DataFrame({
                    'ds': df_ts.index,
                    'y': df_ts.values.ravel()
                })
                
                prophet_model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
                prophet_model.fit(prophet_data)
                
                future_dates = prophet_model.make_future_dataframe(periods=future_periods)
                prophet_pred = prophet_model.predict(future_dates)
                
                # Filter only the future dates
                future_forecast = prophet_pred.iloc[-future_periods:]['yhat']
                future_forecast.index = prophet_pred.iloc[-future_periods:]['ds']
            
            # Plot future forecast
            plt.figure(figsize=(12, 6))
            plt.plot(df_ts.index, df_ts, label='Historical Data')
            plt.plot(future_forecast.index, future_forecast, label='Forecast', color='red')
            plt.title(f'Future {future_periods}-Period Sales Forecast using {best_model}')
            plt.legend()
            plt.grid(True)
            plt.show()
            
            # Print forecast values
            print(f"\nFuture {future_periods}-Period Forecast:")
            for date, value in zip(future_forecast.index, future_forecast.values):
                print(f"{date.date()}: {value:.2f}")
    
    except Exception as e:
        print(f"Error in forecasting: {e}")
    
    return df


def run_causal_impact(df, sales_col, date_col):
    """Applies CausalImpact to assess how an event affected sales."""
    print("\n===== Causal Impact Analysis =====")
    
    try:
        # Ask user for event date
        print("\nEnter the date when an event occurred (format: YYYY-MM-DD)")
        event_date = input().strip()
        
        # Ensure date format is correct
        try:
            event_date = pd.to_datetime(event_date)
            if event_date not in pd.to_datetime(df[date_col]).values:
                closest_date = pd.to_datetime(df[date_col]).iloc[
                    (pd.to_datetime(df[date_col]) - event_date).abs().argsort()[0]
                ]
                print(f"Event date not found in dataset. Using closest date: {closest_date}")
                event_date = closest_date
        except Exception as e:
            print(f"Invalid date format: {e}")
            return df
        
        # Define pre-event and post-event periods
        pre_event = df[pd.to_datetime(df[date_col]) < event_date]
        post_event = df[pd.to_datetime(df[date_col]) >= event_date]
        
        min_pre_periods = max(30, int(len(df) * 0.3))
        min_post_periods = max(10, int(len(df) * 0.1))
        
        if len(pre_event) < min_pre_periods or len(post_event) < min_post_periods:
            print(f"Warning: Not enough data before ({len(pre_event)}/{min_pre_periods}) or after ({len(post_event)}/{min_post_periods}) the event.")
            print("Analysis might not be reliable. Continuing anyway...")
        
        # Prepare data for CausalImpact (time series format)
        df_ci = df.sort_values(by=date_col).copy()
        df_ci.set_index(date_col, inplace=True)
        data = df_ci[[sales_col]]
        
        # Define time periods
        pre_period = [data.index.min(), event_date - pd.Timedelta(days=1)]
        post_period = [event_date, data.index.max()]
        
        # Run Causal Impact Analysis
        impact = CausalImpact(data, pre_period, post_period)
        
        # Plot impact
        impact.plot()
        plt.tight_layout()
        plt.show()
        
        # Show summary of impact
        print("\nImpact Summary:")
        print(impact.summary())
        
        # Detailed report
        print("\nDetailed Impact Report:")
        report = impact.summary(output='report')
        print(report)
        
        # Add impact results to dataframe
        df['causal_impact_rel_effect'] = np.nan
        df.loc[pd.to_datetime(df[date_col]) >= event_date, 'causal_impact_rel_effect'] = impact.summary_data.loc['average', 'rel_effect']
        
        # Create simple interpretation
        effect = impact.summary_data.loc['average', 'rel_effect'] * 100
        if effect > 0:
            direction = "positive"
        else:
            direction = "negative"
            effect = -effect
            
        p_value = impact.summary_data.loc['average', 'p']
        if p_value < 0.05:
            significance = "statistically significant"
        else:
            significance = "not statistically significant"
            
        print(f"\nSimple Interpretation:")
        print(f"The event had a {direction} impact of {effect:.2f}% on {sales_col}, which is {significance} (p-value = {p_value:.4f}).")
        
    except Exception as e:
        print(f"Error in causal impact analysis: {e}")
    
    return df


def analyze_change_points(df, date_col, sales_col):
    """Detects structural changes in the time series data."""
    print("\n===== Change Point Detection =====")
    
    try:
        from ruptures import Pelt, KernelCPD
        from sklearn.preprocessing import StandardScaler
        
        # Prepare data
        df_cp = df.sort_values(by=date_col).copy()
        series = df_cp[sales_col].values
        
        # Standardize for better detection
        series_std = StandardScaler().fit_transform(series.reshape(-1, 1)).flatten()
        
        # Pelt change point detection
        model = Pelt(model="rbf").fit(series_std)
        change_points = model.predict(pen=10)
        
        # Alternative: Kernel change point detection
        kernel_model = KernelCPD(kernel="rbf", jump=5).fit(series_std)
        kernel_change_points = kernel_model.predict(pen=3)
        
        # Plot results
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 1, 1)
        plt.plot(df_cp[date_col], series)
        for cp in change_points[:-1]:  # Exclude the last one which is the series end
            plt.axvline(x=df_cp[date_col].iloc[cp], color='r', linestyle='--')
        plt.title(f'Change Points in {sales_col} (Pelt Method)')
        plt.xlabel('Date')
        plt.ylabel(sales_col)
        
        plt.subplot(2, 1, 2)
        plt.plot(df_cp[date_col], series)
        for cp in kernel_change_points[:-1]:  # Exclude the last one which is the series end
            plt.axvline(x=df_cp[date_col].iloc[cp], color='g', linestyle='--')
        plt.title(f'Change Points in {sales_col} (Kernel Method)')
        plt.xlabel('Date')
        plt.ylabel(sales_col)
        
        plt.tight_layout()
        plt.show()
        
        # Print change point dates
        if change_points and len(change_points) > 1:
            print("\nDetected Change Points (Pelt Method):")
            for cp in change_points[:-1]:
                print(f"- {df_cp[date_col].iloc[cp]}")
                
        if kernel_change_points and len(kernel_change_points) > 1:
            print("\nDetected Change Points (Kernel Method):")
            for cp in kernel_change_points[:-1]:
                print(f"- {df_cp[date_col].iloc[cp]}")
                
        # Add change points to dataframe
        df['is_change_point'] = 0
        for cp in change_points[:-1]:
            df.loc[df[date_col] == df_cp[date_col].iloc[cp], 'is_change_point'] = 1
            
        return df
        
    except ImportError:
        print("Change point detection requires the 'ruptures' package. Please install with 'pip install ruptures'.")
        return df
    except Exception as e:
        print(f"Error in change point detection: {e}")
        return df


def identify_outlier_periods(df, date_col, sales_col):
    """Identifies periods where sales behaved unusually compared to expectations."""
    print("\n===== Outlier Period Analysis =====")
    
    try:
        # Need trend and seasonal components from STL decomposition
        if 'trend_component' not in df.columns or 'seasonal_component' not in df.columns:
            print("Running seasonal decomposition first...")
            df = analyze_seasonality(df, date_col, sales_col)
        
        if 'trend_component' not in df.columns:
            print("Seasonal decomposition failed. Skipping outlier period analysis.")
            return df
            
        # Calculate expected values (trend + seasonal)
        df['expected_value'] = df['trend_component'] + df['seasonal_component']
        df['deviation'] = df[sales_col] - df['expected_value']
        
        # Calculate z-scores of deviations
        df['deviation_zscore'] = (df['deviation'] - df['deviation'].mean()) / df['deviation'].std()
        
        # Flag outlier periods (absolute z-score > 2)
        df['is_outlier_period'] = (abs(df['deviation_zscore']) > 2).astype(int)
        
        # Identify clusters of outliers (outlier periods)
        outlier_periods = []
        current_period = []
        
        for i, row in df.sort_values(by=date_col).iterrows():
            if row['is_outlier_period'] == 1:
                current_period.append(row[date_col])
            elif current_period:
                if len(current_period) >= 2:  # Only consider periods with at least 2 consecutive outliers
                    outlier_periods.append((min(current_period), max(current_period)))
                current_period = []
        
        # Add the last period if it exists
        if current_period and len(current_period) >= 2:
            outlier_periods.append((min(current_period), max(current_period)))
        
        # Plot results
        plt.figure(figsize=(12, 6))
        plt.plot(df[date_col], df[sales_col], label='Actual')
        plt.plot(df[date_col], df['expected_value'], label='Expected (Trend+Seasonal)', linestyle='--')
        
        # Highlight outlier periods
        for start, end in outlier_periods:
            plt.axvspan(start, end, color='red', alpha=0.3)
        
        plt.title('Sales with Outlier Periods Highlighted')
        plt.legend()
        plt.grid(True)
        plt.show()
        
        # Print outlier periods
        if outlier_periods:
            print("\nIdentified Outlier Periods:")
            for start, end in outlier_periods:
                if start == end:
                    print(f"- {start}")
                else:
                    print(f"- {start} to {end}")
                    
                # Calculate average deviation during this period
                period_mask = (df[date_col] >= start) & (df[date_col] <= end)
                avg_deviation = df.loc[period_mask, 'deviation'].mean()
                if avg_deviation > 0:
                    direction = "above"
                else:
                    direction = "below"
                    avg_deviation = -avg_deviation
                
                print(f"  Average {direction} expected by {avg_deviation:.2f} ({(avg_deviation/df.loc[period_mask, 'expected_value'].mean())*100:.1f}%)")
        else:
            print("No significant outlier periods detected.")
        
    except Exception as e:
        print(f"Error in outlier period analysis: {e}")
    
    return df


def correlation_analysis(df, sales_col):
    """Analyzes correlations between sales and other numeric features."""
    print("\n===== Correlation Analysis =====")
    
    try:
        # Select numeric columns only
        num_df = df.select_dtypes(include=[np.number])
        
        # Calculate correlation with sales
        correlations = num_df.corr()[sales_col].sort_values(ascending=False)
        
        # Print top positive and negative correlations
        print("\nTop Positive Correlations with Sales:")
        print(correlations[correlations > 0].head(10))
        
        print("\nTop Negative Correlations with Sales:")
        print(correlations[correlations < 0].head(10))
        
        # Plot correlation heatmap (limited to top correlated features)
        top_corr_features = correlations.abs().sort_values(ascending=False).head(15).index
        
        plt.figure(figsize=(12, 10))
        corr_matrix = num_df[top_corr_features].corr()
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
        plt.title('Correlation Heatmap')
        plt.tight_layout()
        plt.show()
        
        # Scatter plots for top correlated features
        top_features = correlations.abs().sort_values(ascending=False).index[1:6]  # Exclude sales itself
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        axes = axes.flatten()
        
        for i, feature in enumerate(top_features[:4]):
            sns.regplot(x=feature, y=sales_col, data=df, ax=axes[i])
            axes[i].set_title(f'{feature} vs {sales_col}')
            
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"Error in correlation analysis: {e}")
    
    return df


def comprehensive_sales_analysis(df, date_col, sales_col):
    """Comprehensive analysis pipeline for sales data."""
    print("\n" + "="*50)
    print("COMPREHENSIVE SALES ANALYSIS")
    print("="*50)
    
    # Step 1: Basic EDA
    df = perform_basic_eda(df, date_col, sales_col)
    
    # Step 2: Add time features
    df = add_time_features(df, date_col)
    
    # Step 3: Time patterns analysis
    df = analyze_time_patterns(df, date_col, sales_col)
    
    # Step 4: Stationarity tests
    is_stationary = test_stationarity(df, sales_col)
    
    # Step 5: Seasonality analysis
    df = analyze_seasonality(df, date_col, sales_col)
    
    # Step 6: Anomaly detection
    df = detect_anomalies(df, date_col, sales_col)
    
    # Step 7: Create lag features
    df = create_lag_features(df, sales_col, date_col)
    
    # Step 8: Feature importance
    df = feature_importance_analysis(df, sales_col, date_col)
    
    # Step 9: Correlation analysis
    df = correlation_analysis(df, sales_col)
    
    # Step 10: Forecasting
    df = forecast_models(df, date_col, sales_col)
    
    # Step 11: Change point detection
    df = analyze_change_points(df, date_col, sales_col)
    
    # Step 12: Outlier period analysis
    df = identify_outlier_periods(df, date_col, sales_col)
    
    # Optional: Causal Impact (only if user has a specific event date)
    run_causal_impact_option = input("\nDo you want to run Causal Impact Analysis? (y/n): ").strip().lower()
    if run_causal_impact_option == 'y':
        df = run_causal_impact(df, sales_col, date_col)
    
    print("\n" + "="*50)
    print("ANALYSIS COMPLETED")
    print("="*50)
    
    # Save the enhanced dataframe with all features
    save_option = input("\nDo you want to save the enhanced dataset with all generated features? (y/n): ").strip().lower()
    if save_option == 'y':
        filename = f"enhanced_sales_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv"
        df.to_csv(filename, index=False)
        print(f"Enhanced dataset saved to {filename}")
    
    return df


def main():
    """Main function to run the analysis."""
    print("="*50)
    print("ADVANCED SALES TIME SERIES ANALYSIS")
    print("="*50)
    print("\nThis tool will help you analyze your sales data and identify key patterns, anomalies, and predictors.")
    
    # Load data
    df = load_csv()
    
    # Select columns
    df, date_col, sales_col = select_columns(df)
    
    # Run comprehensive analysis
    df = comprehensive_sales_analysis(df, date_col, sales_col)
    
    print("\nThank you for using the Advanced Sales Analysis Tool!")


if __name__ == "__main__":
    # Run the script
    main()