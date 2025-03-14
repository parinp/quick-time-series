import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
import json
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
import io
import base64
import plotly.express as px
import plotly.graph_objects as go

def add_time_features(
    data: pd.DataFrame, 
    date_column: str,
    cyclical_encoding: bool = True
) -> pd.DataFrame:
    """
    Add time-based features to the dataframe
    
    Args:
        data: DataFrame containing the time series data
        date_column: Name of the column containing dates
        cyclical_encoding: Whether to use cyclical encoding for time features
        
    Returns:
        DataFrame with added time features
    """
    # Make a copy to avoid modifying the original dataframe
    df = data.copy()
    
    # Ensure date column is datetime
    df[date_column] = pd.to_datetime(df[date_column])
    
    # Extract time components
    df['year'] = df[date_column].dt.year
    df['month'] = df[date_column].dt.month
    df['day'] = df[date_column].dt.day
    df['day_of_week'] = df[date_column].dt.dayofweek
    df['day_of_year'] = df[date_column].dt.dayofyear
    df['week_of_year'] = df[date_column].dt.isocalendar().week
    df['quarter'] = df[date_column].dt.quarter
    
    # Add is_weekend flag
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Add cyclical encoding for periodic features
    if cyclical_encoding:
        # Month has period 12
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Day of week has period 7
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Day of month has period 30/31, using 30 as approximation
        df['day_sin'] = np.sin(2 * np.pi * df['day'] / 30)
        df['day_cos'] = np.cos(2 * np.pi * df['day'] / 30)
        
        # Week of year has period 52
        df['week_of_year_sin'] = np.sin(2 * np.pi * df['week_of_year'] / 52)
        df['week_of_year_cos'] = np.cos(2 * np.pi * df['week_of_year'] / 52)
        
        # Quarter has period 4
        df['quarter_sin'] = np.sin(2 * np.pi * df['quarter'] / 4)
        df['quarter_cos'] = np.cos(2 * np.pi * df['quarter'] / 4)
    
    return df

def add_lag_features(
    data: pd.DataFrame, 
    target_column: str, 
    lag_periods: List[int]
) -> pd.DataFrame:
    """
    Add lag features to the dataframe
    
    Args:
        data: DataFrame containing the time series data
        target_column: Name of the column containing the target variable
        lag_periods: List of lag periods to add
        
    Returns:
        DataFrame with added lag features
    """
    # Make a copy to avoid modifying the original dataframe
    df = data.copy()
    
    # Add lag features
    for lag in lag_periods:
        df[f'{target_column}_lag_{lag}'] = df[target_column].shift(lag)
    
    return df

def add_rolling_features(
    data: pd.DataFrame, 
    target_column: str, 
    window_sizes: List[int],
    functions: List[str] = ['mean', 'std', 'min', 'max']
) -> pd.DataFrame:
    """
    Add rolling window features to the dataframe
    
    Args:
        data: DataFrame containing the time series data
        target_column: Name of the column containing the target variable
        window_sizes: List of window sizes to use
        functions: List of functions to apply to the rolling windows
        
    Returns:
        DataFrame with added rolling window features
    """
    # Make a copy to avoid modifying the original dataframe
    df = data.copy()
    
    # Add rolling window features
    for window in window_sizes:
        rolling = df[target_column].rolling(window=window)
        
        if 'mean' in functions:
            df[f'{target_column}_rolling_{window}_mean'] = rolling.mean()
        
        if 'std' in functions:
            df[f'{target_column}_rolling_{window}_std'] = rolling.std()
        
        if 'min' in functions:
            df[f'{target_column}_rolling_{window}_min'] = rolling.min()
        
        if 'max' in functions:
            df[f'{target_column}_rolling_{window}_max'] = rolling.max()
        
        if 'median' in functions:
            df[f'{target_column}_rolling_{window}_median'] = rolling.median()
        
        if 'sum' in functions:
            df[f'{target_column}_rolling_{window}_sum'] = rolling.sum()
    
    return df

def detect_outliers(
    data: pd.DataFrame, 
    columns: List[str],
    method: str = 'isolation_forest',
    contamination: float = 0.05
) -> Dict[str, Any]:
    """
    Detect outliers in the dataframe
    
    Args:
        data: DataFrame containing the data
        columns: List of column names to check for outliers
        method: Method to use for outlier detection ('isolation_forest', 'zscore', 'iqr')
        contamination: Expected proportion of outliers (for isolation_forest)
        
    Returns:
        Dictionary containing outlier indices and visualization
    """
    # Make a copy to avoid modifying the original dataframe
    df = data.copy()
    
    # Select only numeric columns if not specified
    if not columns:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter to only include specified columns that exist in the dataframe
    columns = [col for col in columns if col in df.columns]
    
    if not columns:
        return {"error": "No valid columns specified for outlier detection"}
    
    # Prepare data for outlier detection
    X = df[columns].copy()
    
    # Handle missing values for outlier detection
    imputer = SimpleImputer(strategy='mean')
    X_imputed = imputer.fit_transform(X)
    
    # Detect outliers
    outlier_indices = []
    
    if method == 'isolation_forest':
        # Use Isolation Forest
        clf = IsolationForest(contamination=contamination, random_state=42)
        outliers = clf.fit_predict(X_imputed)
        outlier_indices = np.where(outliers == -1)[0].tolist()
    
    elif method == 'zscore':
        # Use Z-score method
        from scipy import stats
        z_scores = np.abs(stats.zscore(X_imputed))
        outlier_indices = np.where(np.any(z_scores > 3, axis=1))[0].tolist()
    
    elif method == 'iqr':
        # Use IQR method
        Q1 = np.percentile(X_imputed, 25, axis=0)
        Q3 = np.percentile(X_imputed, 75, axis=0)
        IQR = Q3 - Q1
        
        # Find outliers in any column
        outlier_mask = np.any(
            (X_imputed < (Q1 - 1.5 * IQR)) | (X_imputed > (Q3 + 1.5 * IQR)),
            axis=1
        )
        outlier_indices = np.where(outlier_mask)[0].tolist()
    
    else:
        return {"error": f"Unknown outlier detection method: {method}"}
    
    # Create visualization
    plots = {}
    
    # Create scatter plot for each pair of columns (up to 3 columns)
    if len(columns) >= 2:
        for i in range(min(3, len(columns))):
            for j in range(i+1, min(3, len(columns))):
                col1, col2 = columns[i], columns[j]
                
                # Create scatter plot
                fig = px.scatter(
                    df, 
                    x=col1, 
                    y=col2,
                    color=[
                        'Outlier' if idx in outlier_indices else 'Normal' 
                        for idx in range(len(df))
                    ],
                    color_discrete_map={'Normal': 'blue', 'Outlier': 'red'},
                    title=f'Outlier Detection: {col1} vs {col2}'
                )
                
                plots[f"{col1}_vs_{col2}"] = fig.to_json()
    
    # Create box plots for each column
    for col in columns[:5]:  # Limit to 5 columns
        fig = px.box(
            df, 
            y=col,
            title=f'Box Plot: {col}'
        )
        
        # Add outlier points
        if outlier_indices:
            fig.add_trace(
                go.Scatter(
                    x=['Outliers'] * len(outlier_indices),
                    y=df.iloc[outlier_indices][col],
                    mode='markers',
                    marker=dict(color='red', size=8),
                    name='Outliers'
                )
            )
        
        plots[f"box_{col}"] = fig.to_json()
    
    return {
        "outlier_indices": outlier_indices,
        "outlier_percentage": len(outlier_indices) / len(df) * 100,
        "plots": plots
    }

def impute_missing_values(
    data: pd.DataFrame, 
    columns: List[str],
    method: str = 'mean'
) -> pd.DataFrame:
    """
    Impute missing values in the dataframe
    
    Args:
        data: DataFrame containing the data
        columns: List of column names to impute
        method: Method to use for imputation ('mean', 'median', 'mode', 'ffill', 'bfill')
        
    Returns:
        DataFrame with imputed values
    """
    # Make a copy to avoid modifying the original dataframe
    df = data.copy()
    
    # Select only columns with missing values if not specified
    if not columns:
        missing_cols = df.columns[df.isnull().any()].tolist()
        columns = missing_cols
    
    # Filter to only include specified columns that exist in the dataframe
    columns = [col for col in columns if col in df.columns]
    
    if not columns:
        return df  # No columns to impute
    
    # Impute missing values
    if method in ['mean', 'median', 'most_frequent']:
        # Use scikit-learn imputer for mean, median, and mode
        strategy = 'most_frequent' if method == 'mode' else method
        imputer = SimpleImputer(strategy=strategy)
        
        # Impute only numeric columns with scikit-learn
        numeric_cols = [col for col in columns if np.issubdtype(df[col].dtype, np.number)]
        if numeric_cols:
            df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
        
        # Impute categorical columns with mode
        cat_cols = [col for col in columns if col not in numeric_cols]
        if cat_cols and method in ['mode', 'most_frequent']:
            for col in cat_cols:
                mode_value = df[col].mode()[0]
                df[col] = df[col].fillna(mode_value)
    
    elif method == 'ffill':
        # Forward fill
        df[columns] = df[columns].fillna(method='ffill')
        
        # If there are still missing values at the beginning, backward fill
        df[columns] = df[columns].fillna(method='bfill')
    
    elif method == 'bfill':
        # Backward fill
        df[columns] = df[columns].fillna(method='bfill')
        
        # If there are still missing values at the end, forward fill
        df[columns] = df[columns].fillna(method='ffill')
    
    elif method == 'interpolate':
        # Linear interpolation
        for col in columns:
            if np.issubdtype(df[col].dtype, np.number):
                df[col] = df[col].interpolate(method='linear')
        
        # Fill any remaining missing values (at the beginning or end)
        df[columns] = df[columns].fillna(method='ffill').fillna(method='bfill')
    
    else:
        raise ValueError(f"Unknown imputation method: {method}")
    
    return df

def scale_features(
    data: pd.DataFrame, 
    columns: List[str],
    method: str = 'standard'
) -> pd.DataFrame:
    """
    Scale features in the dataframe
    
    Args:
        data: DataFrame containing the data
        columns: List of column names to scale
        method: Method to use for scaling ('standard', 'minmax')
        
    Returns:
        DataFrame with scaled features
    """
    # Make a copy to avoid modifying the original dataframe
    df = data.copy()
    
    # Select only numeric columns if not specified
    if not columns:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter to only include specified columns that exist in the dataframe
    columns = [col for col in columns if col in df.columns]
    
    if not columns:
        return df  # No columns to scale
    
    # Scale features
    if method == 'standard':
        scaler = StandardScaler()
    elif method == 'minmax':
        scaler = MinMaxScaler()
    else:
        raise ValueError(f"Unknown scaling method: {method}")
    
    df[columns] = scaler.fit_transform(df[columns])
    
    return df

def convert_to_json_serializable(obj: Any) -> Any:
    """
    Convert an object to a JSON serializable format
    
    Args:
        obj: Object to convert
        
    Returns:
        JSON serializable object
    """
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.int64, np.int32, np.float64, np.float32)):
        return obj.item()
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj) 