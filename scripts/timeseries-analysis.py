import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.seasonal import STL
import xgboost as xgb
import shap
from causalimpact import CausalImpact


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
    num_cols.remove(date_col) if date_col in num_cols else None

    if num_cols:
        sales_col = max(num_cols, key=lambda col: df[col].var())
        print(f"Auto-detected sales column: {sales_col}")
    else:
        while True:
            sales_col = input("Enter the sales column name: ").strip()
            if sales_col in df.columns and np.issubdtype(df[sales_col].dtype, np.number):
                break
            print("Error: Column not found or not numeric. Please enter a valid sales column.")

    return df, date_col, sales_col

def detect_anomalies(df, date_col, sales_col):
    """Performs anomaly detection using Isolation Forest and STL decomposition."""
    try:
        # Isolation Forest
        iso_forest = IsolationForest(contamination=0.05, random_state=42)
        df['anomaly'] = iso_forest.fit_predict(df[[sales_col]])

        # STL Decomposition
        stl = STL(df[sales_col], seasonal=13)
        res = stl.fit()
        df['stl_resid'] = res.resid
        threshold = 3 * df['stl_resid'].std()
        df['stl_anomaly'] = (abs(df['stl_resid']) > threshold).astype(int)

        # Plot results
        plt.figure(figsize=(12,6))
        plt.plot(df[date_col], df[sales_col], label='Sales', color='blue')
        plt.scatter(df[date_col][df['anomaly'] == -1], df[sales_col][df['anomaly'] == -1], color='red', label='Isolation Forest Anomaly')
        plt.scatter(df[date_col][df['stl_anomaly'] == 1], df[sales_col][df['stl_anomaly'] == 1], color='orange', label='STL Anomaly')
        plt.legend()
        plt.title('Sales Anomaly Detection')
        plt.show()

    except Exception as e:
        print(f"Error in anomaly detection: {e}")

def create_lag_features(df, sales_col, date_col, lags=[1, 7, 30]):
    """Creates lag features for time series data."""
    for lag in lags:
        df[f'lag_{lag}'] = df[sales_col].shift(lag)
    df.dropna(inplace=True)  # Drop NaN values from shifting
    return df

def feature_importance_analysis(df, sales_col, date_col):
    """Uses XGBoost and SHAP to analyze feature importance."""
    try:
        # Create lag features
        df = create_lag_features(df, sales_col, date_col)

        # Prepare training data
        X = df.drop(columns=[date_col, sales_col])  # Features
        y = df[sales_col]  # Target variable

        # Train XGBoost model
        model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, random_state=42)
        model.fit(X, y)

        # Compute SHAP values
        explainer = shap.Explainer(model)
        shap_values = explainer(X)

        # Plot Feature Importance
        shap.summary_plot(shap_values, X)

    except Exception as e:
        print(f"Error in feature importance analysis: {e}")

def run_causal_impact(df, sales_col, date_col):
    """Applies CausalImpact to assess how an event affected sales."""
    try:
        # Ask user for event date
        print("\nEnter the date when an event occurred (format: YYYY-MM-DD)")
        event_date = input().strip()
        
        # Ensure date format is correct
        try:
            event_date = pd.to_datetime(event_date)
            if event_date not in df[date_col].values:
                print("Error: Event date not found in dataset.")
                return
        except Exception as e:
            print(f"Invalid date format: {e}")
            return

        # Define pre-event and post-event periods
        pre_event = df[df[date_col] < event_date]
        post_event = df[df[date_col] >= event_date]

        if len(pre_event) < 30 or len(post_event) < 10:
            print("Error: Not enough data before or after the event for meaningful analysis.")
            return

        # Prepare data for CausalImpact (time series format)
        df.set_index(date_col, inplace=True)
        data = df[[sales_col]]

        # Define time periods
        pre_period = [data.index[0], event_date - pd.Timedelta(days=1)]
        post_period = [event_date, data.index[-1]]

        # Run Causal Impact Analysis
        impact = CausalImpact(data, pre_period, post_period)
        impact.plot()

        # Show summary of impact
        print("\nImpact Summary:")
        print(impact.summary())
        print("\nDetailed Report:")
        print(impact.summary(output='report'))

    except Exception as e:
        print(f"Error in causal impact analysis: {e}")

if __name__ == "__main__":
    # Run the script
    df = load_csv()
    df, date_col, sales_col = select_columns(df)
    detect_anomalies(df, date_col, sales_col)

    # Run Feature Importance Analysis
    feature_importance_analysis(df, sales_col, date_col)

    # Run Causal Impact Analysis
    run_causal_impact(df, sales_col, date_col)
