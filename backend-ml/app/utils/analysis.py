import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

def train_xgboost_model(data: List[Dict[str, Any]], date_column: str, target_column: str, test_size: float = 0.2, random_state: int = 42):
    """
    Train an XGBoost regression model on the provided data.
    
    Args:
        data: List of dictionaries containing the data
        date_column: Name of the date column
        target_column: Name of the target column
        test_size: Proportion of data to use for testing
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary containing model, features, X_train, X_test, y_train, y_test, and metrics
    """
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    logger.info(f"Training XGBoost model with date column: '{date_column}' and target column: '{target_column}'")
    logger.info(f"DataFrame columns: {df.columns.tolist()}")
    
    # Verify columns exist
    if date_column not in df.columns:
        raise ValueError(f"Date column '{date_column}' not found in data. Available columns: {', '.join(df.columns)}")
    
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in data. Available columns: {', '.join(df.columns)}")
    
    # Convert date column to datetime
    try:
        df[date_column] = pd.to_datetime(df[date_column])
        logger.info(f"Successfully converted '{date_column}' to datetime")
    except Exception as e:
        logger.error(f"Error converting '{date_column}' to datetime: {str(e)}")
        logger.error(f"Sample values: {df[date_column].head().tolist()}")
        raise ValueError(f"Could not convert '{date_column}' to datetime. Make sure it contains valid date values.")
    
    # Extract features from date
    # df['year'] = df[date_column].dt.year
    # df['month'] = df[date_column].dt.month
    # df['day'] = df[date_column].dt.day
    # df['day_of_week'] = df[date_column].dt.dayofweek
    # df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    
    # Drop the date column and any rows with NaN values
    features = df.drop([date_column, target_column], axis=1)
    target = df[target_column]
    
    logger.info(f"Feature columns: {features.columns.tolist()}")
    logger.info(f"Target column: '{target_column}' with {len(target)} values")
    
    # Handle categorical columns
    # First, identify categorical columns (object dtype)
    categorical_columns = features.select_dtypes(include=['object']).columns.tolist()
    
    if categorical_columns:
        logger.info(f"Found categorical columns: {categorical_columns}")
        # Convert categorical columns to numeric using one-hot encoding
        features = pd.get_dummies(features, columns=categorical_columns, drop_first=True)
        logger.info(f"After one-hot encoding, feature columns: {features.columns.tolist()}")
    
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=test_size, random_state=random_state
    )
    
    logger.info(f"Training set size: {len(X_train)}, Test set size: {len(X_test)}")
    
    # Train the XGBoost model
    model = xgb.XGBRegressor(
        tree_method='hist',
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=random_state
    )
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Calculate metrics
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    
    metrics = {
        'train_rmse': float(train_rmse),
        'test_rmse': float(test_rmse),
        'train_r2': float(train_r2),
        'test_r2': float(test_r2)
    }
    
    logger.info(f"Model metrics: {metrics}")
    
    return {
        'model': model,
        'features': features.columns.tolist(),
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test,
        'metrics': metrics
    }

def generate_shap_plots(model_data: Dict[str, Any], multiple_waterfall_plots: bool = False):
    """
    Generate SHAP plots for the trained model.
    
    Args:
        model_data: Dictionary containing model and data from train_xgboost_model
        multiple_waterfall_plots: Whether to generate multiple waterfall plots for different examples
        
    Returns:
        Dictionary containing base64-encoded plot images
    """
    model = model_data['model']
    X_test = model_data['X_test']
    y_test = model_data['y_test']
    
    # Create a SHAP explainer
    explainer = shap.Explainer(model)
    shap_values = explainer(X_test, check_additivity=False)
    
    # Generate and save plots
    plots = {}
    
    # 1. Summary plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test, show=False)
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    plots['summary_plot'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # 2. Bar plot
    plt.figure(figsize=(10, 8))
    shap.plots.bar(shap_values, show=False)
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    plots['bar_plot'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # 3. Beeswarm plot
    plt.figure(figsize=(10, 8))
    shap.plots.beeswarm(shap_values, show=False)
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    plots['beeswarm_plot'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # 4. Waterfall plot for first instance (keep for backward compatibility)
    plt.figure(figsize=(10, 8))
    shap.plots.waterfall(shap_values[0], show=False)
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    plots['waterfall_plot'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # 5. Multiple waterfall plots for different examples if requested
    if multiple_waterfall_plots:
        # Get predictions for all test instances
        y_pred = model.predict(X_test)
        
        # Find indices for low, medium, and high predictions
        sorted_indices = np.argsort(y_pred)
        n_samples = len(sorted_indices)
        
        # Get indices for low (10th percentile), medium (50th percentile), and high (90th percentile)
        low_idx = sorted_indices[int(n_samples * 0.1)]
        med_idx = sorted_indices[int(n_samples * 0.5)]
        high_idx = sorted_indices[int(n_samples * 0.9)]
        
        # Generate force plot for low sales example
        plt.figure(figsize=(14, 6))
        plt.title(f"Low Sales Example (Predicted: {y_pred[low_idx]:.2f}, Actual: {y_test.iloc[low_idx]:.2f})")
        shap.plots.force(shap_values[low_idx], matplotlib=True, show=False, figsize=(14, 3))
        buf = BytesIO()
        plt.tight_layout(pad=3.0)
        plt.savefig(buf, format='png', dpi=120)
        plt.close()
        plots['waterfall_plot_low'] = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # Generate force plot for medium sales example
        plt.figure(figsize=(14, 6))
        plt.title(f"Medium Sales Example (Predicted: {y_pred[med_idx]:.2f}, Actual: {y_test.iloc[med_idx]:.2f})")
        shap.plots.force(shap_values[med_idx], matplotlib=True, show=False, figsize=(14, 3))
        buf = BytesIO()
        plt.tight_layout(pad=3.0)
        plt.savefig(buf, format='png', dpi=120)
        plt.close()
        plots['waterfall_plot_medium'] = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # Generate force plot for high sales example
        plt.figure(figsize=(14, 6))
        plt.title(f"High Sales Example (Predicted: {y_pred[high_idx]:.2f}, Actual: {y_test.iloc[high_idx]:.2f})")
        shap.plots.force(shap_values[high_idx], matplotlib=True, show=False, figsize=(14, 3))
        buf = BytesIO()
        plt.tight_layout(pad=3.0)
        plt.savefig(buf, format='png', dpi=120)
        plt.close()
        plots['waterfall_plot_high'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return {
        'plots': plots
    }

def get_feature_importance(model_data: Dict[str, Any]):
    """
    Get feature importance from the trained model.
    
    Args:
        model_data: Dictionary containing model and features from train_xgboost_model
        
    Returns:
        List of dictionaries containing feature names and importance scores
    """
    model = model_data['model']
    feature_names = model_data['features']
    
    # Get feature importance
    importance = model.feature_importances_
    
    # Create a list of dictionaries with feature names and importance scores
    feature_importance = [
        {'feature': feature, 'importance': float(score)}
        for feature, score in zip(feature_names, importance)
    ]
    
    # Sort by importance (descending)
    feature_importance.sort(key=lambda x: x['importance'], reverse=True)
    
    return feature_importance

def analyze_data(data: List[Dict[str, Any]], date_column: str, target_column: str, multiple_waterfall_plots: bool = False):
    """
    Analyze data using XGBoost and SHAP.
    
    Args:
        data: List of dictionaries containing the data
        date_column: Name of the date column
        target_column: Name of the target column
        multiple_waterfall_plots: Whether to generate multiple waterfall plots for different examples
        
    Returns:
        Dictionary containing metrics, feature importance, and SHAP plots
    """
    # Train model
    model_data = train_xgboost_model(data, date_column, target_column)
    
    # Get metrics
    metrics = model_data['metrics']
    
    # Get feature importance
    feature_importance = get_feature_importance(model_data)
    
    # Generate SHAP plots
    shap_data = generate_shap_plots(model_data, multiple_waterfall_plots)
    
    # Return results
    return {
        'metrics': metrics,
        'feature_importance': feature_importance,
        'shap_plots': shap_data['plots']
    } 