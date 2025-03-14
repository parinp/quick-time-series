import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose
import json
from typing import Dict, List, Any, Optional, Union
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import base64
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import io

def perform_eda(df: pd.DataFrame, date_col: Optional[str] = None, target_col: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform exploratory data analysis on time series data.
    
    Args:
        df: DataFrame containing the time series data
        date_col: Name of the date column
        target_col: Name of the target column to analyze
        
    Returns:
        Dictionary containing EDA results
    """
    results = {}
    
    # Basic information
    results["shape"] = list(df.shape)
    results["columns"] = df.columns.tolist()
    results["dtypes"] = {col: str(dtype) for col, dtype in df.dtypes.items()}
    results["head"] = df.head(5).to_dict(orient='records')
    
    # Missing values
    missing_values = df.isnull().sum().to_dict()
    results["missing_values"] = {k: int(v) for k, v in missing_values.items()}
    
    # Missing values plot
    if any(missing_values.values()):
        missing_plot = create_missing_values_plot(df)
        results["missing_values_plot"] = missing_plot
    
    # Basic statistics for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        # Convert to Python native types for JSON serialization
        stats = df[numeric_cols].describe().to_dict()
        for col in stats:
            stats[col] = {k: float(v) for k, v in stats[col].items()}
        results["statistics"] = stats
        
        # Distribution plots for numeric columns
        if target_col and target_col in numeric_cols:
            dist_plots = create_distribution_plots(df, target_col)
            results["distribution_plots"] = dist_plots
    
    # Time series specific analysis
    if date_col and target_col and date_col in df.columns and target_col in df.columns:
        # Ensure date column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            try:
                df[date_col] = pd.to_datetime(df[date_col])
            except Exception as e:
                results["warnings"] = [f"Could not convert {date_col} to datetime: {str(e)}"]
                return results
        
        if pd.api.types.is_datetime64_any_dtype(df[date_col]):
            # Set date as index for time series analysis
            ts_df = df.copy()
            ts_df = ts_df.set_index(date_col)
            
            # Time series patterns
            results["time_patterns"] = {}
            
            # Time series plot
            time_series_plot = create_time_series_plot(df, date_col, target_col)
            results["time_patterns"]["time_series_plot"] = time_series_plot
            
            # Resample to different frequencies if enough data
            if len(ts_df) >= 30:  # Only if we have enough data
                try:
                    # Monthly average
                    monthly_avg = ts_df[target_col].resample("M").mean()
                    results["time_patterns"]["monthly_avg"] = {
                        str(k.date()): float(v) for k, v in monthly_avg.items() if not pd.isna(v)
                    }
                    
                    # Monthly plot
                    monthly_plot = create_monthly_plot(monthly_avg, target_col)
                    results["time_patterns"]["monthly_plot"] = monthly_plot
                    
                    # Weekly average
                    weekly_avg = ts_df[target_col].resample("W").mean()
                    results["time_patterns"]["weekly_avg"] = {
                        str(k.date()): float(v) for k, v in weekly_avg.items() if not pd.isna(v)
                    }
                    
                    # Daily patterns by day of week
                    day_of_week = ts_df.groupby(ts_df.index.dayofweek)[target_col].mean().to_dict()
                    results["time_patterns"]["day_of_week_avg"] = {
                        int(k): float(v) for k, v in day_of_week.items()
                    }
                    
                    # Day of week plot
                    dow_plot = create_day_of_week_plot(ts_df, target_col)
                    results["time_patterns"]["day_of_week_plot"] = dow_plot
                    
                    # Monthly patterns
                    monthly_patterns = ts_df.groupby(ts_df.index.month)[target_col].mean().to_dict()
                    results["time_patterns"]["monthly_patterns"] = {
                        int(k): float(v) for k, v in monthly_patterns.items()
                    }
                    
                    # Month plot
                    month_plot = create_month_plot(ts_df, target_col)
                    results["time_patterns"]["month_plot"] = month_plot
                    
                    # Heatmap of day of week vs month
                    if len(ts_df) >= 60:  # Need enough data for meaningful heatmap
                        heatmap = create_time_heatmap(ts_df, target_col)
                        results["time_patterns"]["time_heatmap"] = heatmap
                    
                    # Try seasonal decomposition if enough data
                    if len(ts_df) >= 2 * 7:  # At least 2 weeks of data
                        try:
                            # For weekly seasonality
                            decomposition = seasonal_decompose(
                                ts_df[target_col].dropna(), 
                                model="additive", 
                                period=7
                            )
                            
                            # Get one full period of seasonality
                            seasonal_values = decomposition.seasonal.dropna().values
                            period_length = min(7, len(seasonal_values))
                            
                            results["time_patterns"]["seasonal_decomposition"] = {
                                "trend": [float(x) for x in decomposition.trend.dropna().values],
                                "seasonal": [float(x) for x in seasonal_values[:period_length]],
                                "dates": [str(x.date()) for x in decomposition.trend.dropna().index]
                            }
                            
                            # Decomposition plot
                            decomp_plot = create_decomposition_plot(decomposition)
                            results["time_patterns"]["decomposition_plot"] = decomp_plot
                        except Exception as e:
                            results["warnings"] = results.get("warnings", []) + [
                                f"Seasonal decomposition failed: {str(e)}"
                            ]
                except Exception as e:
                    results["warnings"] = results.get("warnings", []) + [
                        f"Time pattern analysis failed: {str(e)}"
                    ]
            
            # Autocorrelation and partial autocorrelation
            try:
                from statsmodels.tsa.stattools import acf, pacf
                
                # Calculate ACF and PACF
                acf_values = acf(ts_df[target_col].dropna(), nlags=min(40, len(ts_df) // 2))
                pacf_values = pacf(ts_df[target_col].dropna(), nlags=min(40, len(ts_df) // 2))
                
                results["time_patterns"]["autocorrelation"] = {
                    "acf": [float(x) for x in acf_values],
                    "pacf": [float(x) for x in pacf_values],
                    "lags": list(range(len(acf_values)))
                }
                
                # ACF/PACF plots
                acf_pacf_plot = create_acf_pacf_plot(acf_values, pacf_values)
                results["time_patterns"]["acf_pacf_plot"] = acf_pacf_plot
            except Exception as e:
                results["warnings"] = results.get("warnings", []) + [
                    f"Autocorrelation analysis failed: {str(e)}"
                ]
            
            # Stationarity test
            try:
                from statsmodels.tsa.stattools import adfuller
                
                # Perform ADF test
                adf_result = adfuller(ts_df[target_col].dropna())
                
                results["time_patterns"]["stationarity_test"] = {
                    "adf_statistic": float(adf_result[0]),
                    "p_value": float(adf_result[1]),
                    "is_stationary": bool(adf_result[1] < 0.05),
                    "critical_values": {str(k): float(v) for k, v in adf_result[4].items()}
                }
            except Exception as e:
                results["warnings"] = results.get("warnings", []) + [
                    f"Stationarity test failed: {str(e)}"
                ]
    
    return results

def create_missing_values_plot(df: pd.DataFrame) -> str:
    """Create a plot showing missing values"""
    plt.figure(figsize=(10, 6))
    
    # Calculate missing values percentage
    missing = df.isnull().sum() / len(df) * 100
    missing = missing[missing > 0].sort_values(ascending=False)
    
    if len(missing) > 0:
        plt.bar(range(len(missing)), missing.values)
        plt.xticks(range(len(missing)), missing.index, rotation=90)
        plt.ylabel('Percentage Missing')
        plt.title('Missing Values by Column')
        plt.tight_layout()
        
        # Save to BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        
        # Encode as base64
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    else:
        plt.close()
        return ""

def create_distribution_plots(df: pd.DataFrame, target_col: str) -> Dict[str, str]:
    """Create distribution plots for the target column"""
    plots = {}
    
    # Histogram
    plt.figure(figsize=(10, 6))
    plt.hist(df[target_col].dropna(), bins=30, alpha=0.7, color='skyblue')
    plt.title(f'Distribution of {target_col}')
    plt.xlabel(target_col)
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    
    # Save to BytesIO
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    
    # Encode as base64
    buf.seek(0)
    plots["histogram"] = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # Box plot
    plt.figure(figsize=(10, 6))
    plt.boxplot(df[target_col].dropna())
    plt.title(f'Box Plot of {target_col}')
    plt.ylabel(target_col)
    plt.grid(True, alpha=0.3)
    
    # Save to BytesIO
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    
    # Encode as base64
    buf.seek(0)
    plots["boxplot"] = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return plots

def create_time_series_plot(df: pd.DataFrame, date_col: str, target_col: str) -> str:
    """Create an interactive time series plot"""
    fig = px.line(df, x=date_col, y=target_col, 
                  title=f"{target_col} over time")
    
    # Add rolling averages
    for window in [7, 14, 30]:
        if len(df) >= window:
            rolling_avg = df[target_col].rolling(window=window).mean()
            fig.add_trace(
                go.Scatter(
                    x=df[date_col],
                    y=rolling_avg,
                    mode='lines',
                    name=f'{window}-day Rolling Average'
                )
            )
    
    # Convert to JSON
    plot_json = fig.to_json()
    
    return {
        "plot_type": "plotly",
        "plot_data": plot_json
    }

def create_monthly_plot(monthly_data: pd.Series, target_col: str) -> str:
    """Create a monthly trend plot"""
    # Reset index to get date as a column
    plot_data = monthly_data.reset_index()
    plot_data.columns = ['date', target_col]
    
    # Create a Plotly figure
    fig = px.line(plot_data, x='date', y=target_col, title=f'Monthly {target_col} Trend')
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title=f'Average {target_col}',
        template='plotly_white'
    )
    
    # Convert to JSON
    plot_json = pio.to_json(fig)
    
    return plot_json

def create_day_of_week_plot(df: pd.DataFrame, target_col: str) -> str:
    """Create a day of week pattern plot"""
    # Group by day of week
    dow_avg = df.groupby(df.index.dayofweek)[target_col].mean().reset_index()
    dow_avg.columns = ['day_of_week', target_col]
    
    # Map day numbers to names
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_avg['day_name'] = dow_avg['day_of_week'].apply(lambda x: days[x])
    
    # Create a Plotly figure
    fig = px.bar(dow_avg, x='day_name', y=target_col, title=f'Average {target_col} by Day of Week')
    fig.update_layout(
        xaxis_title='Day of Week',
        yaxis_title=f'Average {target_col}',
        template='plotly_white'
    )
    
    # Convert to JSON
    plot_json = pio.to_json(fig)
    
    return plot_json

def create_month_plot(df: pd.DataFrame, target_col: str) -> str:
    """Create a month pattern plot"""
    # Group by month
    month_avg = df.groupby(df.index.month)[target_col].mean().reset_index()
    month_avg.columns = ['month', target_col]
    
    # Map month numbers to names
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_avg['month_name'] = month_avg['month'].apply(lambda x: months[x-1])
    
    # Create a Plotly figure
    fig = px.bar(month_avg, x='month_name', y=target_col, title=f'Average {target_col} by Month')
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title=f'Average {target_col}',
        template='plotly_white'
    )
    
    # Convert to JSON
    plot_json = pio.to_json(fig)
    
    return plot_json

def create_time_heatmap(df: pd.DataFrame, target_col: str) -> str:
    """Create a heatmap of day of week vs month"""
    # Create pivot table
    heatmap_data = df.pivot_table(
        index=df.index.dayofweek,
        columns=df.index.month,
        values=target_col,
        aggfunc='mean'
    )
    
    # Map indices to day names and column names to month names
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Create a Plotly figure
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=[months[i-1] for i in heatmap_data.columns],
        y=[days[i] for i in heatmap_data.index],
        colorscale='Viridis',
        colorbar=dict(title=f'Average {target_col}')
    ))
    
    fig.update_layout(
        title=f'Heatmap of {target_col} by Day of Week and Month',
        xaxis_title='Month',
        yaxis_title='Day of Week',
        template='plotly_white'
    )
    
    # Convert to JSON
    plot_json = pio.to_json(fig)
    
    return plot_json

def create_decomposition_plot(decomposition) -> str:
    """Create a seasonal decomposition plot"""
    # Create a figure with subplots
    fig = make_subplots(rows=4, cols=1, 
                        subplot_titles=('Observed', 'Trend', 'Seasonal', 'Residual'))
    
    # Add traces
    fig.add_trace(
        go.Scatter(x=decomposition.observed.index, y=decomposition.observed.values, mode='lines', name='Observed'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=decomposition.trend.index, y=decomposition.trend.values, mode='lines', name='Trend'),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=decomposition.seasonal.index, y=decomposition.seasonal.values, mode='lines', name='Seasonal'),
        row=3, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=decomposition.resid.index, y=decomposition.resid.values, mode='lines', name='Residual'),
        row=4, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        title_text='Seasonal Decomposition',
        template='plotly_white'
    )
    
    # Convert to JSON
    plot_json = pio.to_json(fig)
    
    return plot_json

def create_acf_pacf_plot(acf_values, pacf_values) -> str:
    """Create ACF and PACF plots"""
    # Create a figure with subplots
    fig = make_subplots(rows=2, cols=1, subplot_titles=('Autocorrelation', 'Partial Autocorrelation'))
    
    # Add traces
    fig.add_trace(
        go.Bar(x=list(range(len(acf_values))), y=acf_values, name='ACF'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=list(range(len(pacf_values))), y=pacf_values, name='PACF'),
        row=2, col=1
    )
    
    # Add confidence intervals (approximately ±1.96/sqrt(n))
    n = len(acf_values)
    conf_int = 1.96 / np.sqrt(n)
    
    fig.add_trace(
        go.Scatter(x=list(range(len(acf_values))), y=[conf_int] * len(acf_values), 
                  mode='lines', line=dict(dash='dash', color='red'), showlegend=False),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=list(range(len(acf_values))), y=[-conf_int] * len(acf_values), 
                  mode='lines', line=dict(dash='dash', color='red'), showlegend=False),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=list(range(len(pacf_values))), y=[conf_int] * len(pacf_values), 
                  mode='lines', line=dict(dash='dash', color='red'), showlegend=False),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=list(range(len(pacf_values))), y=[-conf_int] * len(pacf_values), 
                  mode='lines', line=dict(dash='dash', color='red'), showlegend=False),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=600,
        title_text='ACF and PACF Analysis',
        template='plotly_white'
    )
    
    fig.update_xaxes(title_text='Lag', row=1, col=1)
    fig.update_xaxes(title_text='Lag', row=2, col=1)
    fig.update_yaxes(title_text='Correlation', row=1, col=1)
    fig.update_yaxes(title_text='Partial Correlation', row=2, col=1)
    
    # Convert to JSON
    plot_json = pio.to_json(fig)
    
    return plot_json 