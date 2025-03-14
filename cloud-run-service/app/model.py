import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pickle
import base64
from io import BytesIO
import shap
import json
from typing import Dict, List, Any, Optional, Union
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import io
import ruptures as rpt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def train_model(
    data: pd.DataFrame, 
    target_column: str, 
    feature_columns: List[str],
    test_size: float = 0.2,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Train an XGBoost model on the provided data
    
    Args:
        data: DataFrame containing the features and target
        target_column: Name of the column containing the target variable
        feature_columns: List of column names to use as features
        test_size: Proportion of data to use for testing
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary containing model, metrics, and feature importance
    """
    # Prepare data
    X = data[feature_columns]
    y = data[target_column]
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    # Train model
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=random_state
    )
    
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Calculate metrics
    train_metrics = calculate_metrics(y_train, y_pred_train)
    test_metrics = calculate_metrics(y_test, y_pred_test)
    
    # Get feature importance
    feature_importance = get_feature_importance(model, X)
    
    # Generate SHAP values
    shap_values = generate_shap_values(model, X_test)
    
    # Create plots
    plots = create_model_plots(y_test, y_pred_test, feature_importance, shap_values, X_test)
    
    return {
        "model": model,
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "feature_importance": feature_importance,
        "plots": plots
    }

def train_time_series_model(
    data: pd.DataFrame,
    date_column: str,
    target_column: str,
    feature_columns: List[str],
    n_splits: int = 5
) -> Dict[str, Any]:
    """
    Train a time series model using time series cross-validation
    
    Args:
        data: DataFrame containing the features and target
        date_column: Name of the column containing dates
        target_column: Name of the column containing the target variable
        feature_columns: List of column names to use as features
        n_splits: Number of splits for time series cross-validation
        
    Returns:
        Dictionary containing model, metrics, and feature importance
    """
    # Ensure date column is datetime
    data[date_column] = pd.to_datetime(data[date_column])
    
    # Sort by date
    data = data.sort_values(by=date_column)
    
    # Prepare data
    X = data[feature_columns]
    y = data[target_column]
    
    # Time series cross-validation
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    # Initialize lists to store results
    cv_train_metrics = []
    cv_test_metrics = []
    cv_predictions = []
    
    # Train model with cross-validation
    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Train model
        model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Calculate metrics
        train_metrics = calculate_metrics(y_train, y_pred_train)
        test_metrics = calculate_metrics(y_test, y_pred_test)
        
        cv_train_metrics.append(train_metrics)
        cv_test_metrics.append(test_metrics)
        
        # Store predictions
        cv_predictions.append({
            "dates": data.iloc[test_idx][date_column].dt.strftime('%Y-%m-%d').tolist(),
            "actual": y_test.tolist(),
            "predicted": y_pred_test.tolist()
        })
    
    # Train final model on all data
    final_model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    
    final_model.fit(X, y)
    
    # Get feature importance
    feature_importance = get_feature_importance(final_model, X)
    
    # Generate SHAP values
    shap_values = generate_shap_values(final_model, X)
    
    # Calculate average metrics
    avg_train_metrics = {
        k: np.mean([m[k] for m in cv_train_metrics]) 
        for k in cv_train_metrics[0].keys()
    }
    
    avg_test_metrics = {
        k: np.mean([m[k] for m in cv_test_metrics]) 
        for k in cv_test_metrics[0].keys()
    }
    
    # Create plots
    plots = create_time_series_cv_plots(cv_predictions, feature_importance, shap_values, X)
    
    return {
        "model": final_model,
        "train_metrics": avg_train_metrics,
        "test_metrics": avg_test_metrics,
        "cv_predictions": cv_predictions,
        "feature_importance": feature_importance,
        "plots": plots
    }

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate regression metrics"""
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    # Calculate MAPE if no zeros in y_true
    if np.all(y_true != 0):
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    else:
        mape = None
    
    metrics = {
        "mse": float(mse),
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2)
    }
    
    if mape is not None:
        metrics["mape"] = float(mape)
    
    return metrics

def get_feature_importance(model: xgb.XGBRegressor, X: pd.DataFrame) -> Dict[str, float]:
    """Get feature importance from the model"""
    importance = model.feature_importances_
    feature_importance = dict(zip(X.columns, importance))
    
    # Sort by importance
    feature_importance = {
        k: float(v) for k, v in sorted(
            feature_importance.items(), 
            key=lambda item: item[1], 
            reverse=True
        )
    }
    
    return feature_importance

def generate_shap_values(model: xgb.XGBRegressor, X: pd.DataFrame) -> Dict[str, List[float]]:
    """Generate SHAP values for model interpretation"""
    # Create explainer
    explainer = shap.Explainer(model)
    
    # Calculate SHAP values
    shap_values = explainer(X)
    
    # Convert to dictionary
    shap_dict = {
        "values": shap_values.values.tolist(),
        "base_values": shap_values.base_values.tolist(),
        "feature_names": X.columns.tolist()
    }
    
    return shap_dict

def create_model_plots(
    y_true: np.ndarray, 
    y_pred: np.ndarray, 
    feature_importance: Dict[str, float],
    shap_values: Dict[str, Any],
    X_test: pd.DataFrame
) -> Dict[str, Any]:
    """Create plots for model evaluation"""
    plots = {}
    
    # Actual vs Predicted plot
    fig = px.scatter(
        x=y_true, 
        y=y_pred, 
        labels={'x': 'Actual', 'y': 'Predicted'},
        title='Actual vs Predicted'
    )
    
    # Add diagonal line
    min_val = min(min(y_true), min(y_pred))
    max_val = max(max(y_true), max(y_pred))
    fig.add_trace(
        go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            line=dict(color='red', dash='dash'),
            name='Perfect Prediction'
        )
    )
    
    plots["actual_vs_predicted"] = fig.to_json()
    
    # Feature importance plot
    fig = px.bar(
        x=list(feature_importance.values())[:10],
        y=list(feature_importance.keys())[:10],
        orientation='h',
        labels={'x': 'Importance', 'y': 'Feature'},
        title='Top 10 Feature Importance'
    )
    
    plots["feature_importance"] = fig.to_json()
    
    # SHAP summary plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(
        np.array(shap_values["values"]), 
        X_test,
        feature_names=shap_values["feature_names"],
        show=False
    )
    
    # Save SHAP plot to base64
    shap_buffer = io.BytesIO()
    plt.savefig(shap_buffer, format='png', bbox_inches='tight')
    shap_buffer.seek(0)
    shap_image = base64.b64encode(shap_buffer.read()).decode('utf-8')
    plt.close()
    
    plots["shap_summary"] = f"data:image/png;base64,{shap_image}"
    
    return plots

def create_time_series_cv_plots(
    cv_predictions: List[Dict[str, Any]],
    feature_importance: Dict[str, float],
    shap_values: Dict[str, Any],
    X: pd.DataFrame
) -> Dict[str, Any]:
    """Create plots for time series cross-validation"""
    plots = {}
    
    # Time series CV plot
    fig = go.Figure()
    
    for i, fold in enumerate(cv_predictions):
        fig.add_trace(
            go.Scatter(
                x=fold["dates"],
                y=fold["actual"],
                mode='lines',
                name=f'Actual (Fold {i+1})',
                line=dict(color='blue')
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=fold["dates"],
                y=fold["predicted"],
                mode='lines',
                name=f'Predicted (Fold {i+1})',
                line=dict(color='red', dash='dash')
            )
        )
    
    fig.update_layout(
        title='Time Series Cross-Validation',
        xaxis_title='Date',
        yaxis_title='Value'
    )
    
    plots["time_series_cv"] = fig.to_json()
    
    # Feature importance plot
    fig = px.bar(
        x=list(feature_importance.values())[:10],
        y=list(feature_importance.keys())[:10],
        orientation='h',
        labels={'x': 'Importance', 'y': 'Feature'},
        title='Top 10 Feature Importance'
    )
    
    plots["feature_importance"] = fig.to_json()
    
    # SHAP summary plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(
        np.array(shap_values["values"]), 
        X,
        feature_names=shap_values["feature_names"],
        show=False
    )
    
    # Save SHAP plot to base64
    shap_buffer = io.BytesIO()
    plt.savefig(shap_buffer, format='png', bbox_inches='tight')
    shap_buffer.seek(0)
    shap_image = base64.b64encode(shap_buffer.read()).decode('utf-8')
    plt.close()
    
    plots["shap_summary"] = f"data:image/png;base64,{shap_image}"
    
    return plots

def detect_change_points(
    data: pd.DataFrame,
    date_column: str,
    target_column: str,
    method: str = 'pelt',
    penalty: str = 'rbf',
    n_bkps: int = 5
) -> Dict[str, Any]:
    """
    Detect change points in time series data
    
    Args:
        data: DataFrame containing the time series data
        date_column: Name of the column containing dates
        target_column: Name of the column containing the target variable
        method: Change point detection method ('pelt', 'binseg', 'window')
        penalty: Penalty for the change point detection ('rbf', 'l1', 'l2', 'linear')
        n_bkps: Number of breakpoints to detect
        
    Returns:
        Dictionary containing change points and visualization
    """
    # Ensure date column is datetime
    data[date_column] = pd.to_datetime(data[date_column])
    
    # Sort by date
    data = data.sort_values(by=date_column)
    
    # Get the signal
    signal = data[target_column].values
    
    # Detect change points
    if method == 'pelt':
        algo = rpt.Pelt(model="rbf").fit(signal)
        change_points = algo.predict(pen=penalty)
    elif method == 'binseg':
        algo = rpt.Binseg(model="rbf").fit(signal)
        change_points = algo.predict(n_bkps=n_bkps)
    elif method == 'window':
        algo = rpt.Window(model="rbf").fit(signal)
        change_points = algo.predict(n_bkps=n_bkps)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Get dates for change points
    change_point_dates = data.iloc[change_points][date_column].dt.strftime('%Y-%m-%d').tolist()
    
    # Create visualization
    fig = px.line(
        data, 
        x=date_column, 
        y=target_column,
        title='Change Point Detection'
    )
    
    # Add vertical lines for change points
    for cp_date in data.iloc[change_points][date_column]:
        fig.add_vline(
            x=cp_date, 
            line_width=2, 
            line_dash="dash", 
            line_color="red"
        )
    
    # Return results
    return {
        "change_points": change_points,
        "change_point_dates": change_point_dates,
        "plot": fig.to_json()
    }

def make_predictions(
    model: xgb.XGBRegressor,
    data: pd.DataFrame,
    feature_columns: List[str]
) -> np.ndarray:
    """
    Make predictions using the trained model
    
    Args:
        model: Trained XGBoost model
        data: DataFrame containing the features
        feature_columns: List of column names to use as features
        
    Returns:
        Array of predictions
    """
    # Prepare data
    X = data[feature_columns]
    
    # Make predictions
    predictions = model.predict(X)
    
    return predictions 