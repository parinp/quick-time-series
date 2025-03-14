# ML Analysis API

This is a FastAPI-based API for performing machine learning analysis on time series data using XGBoost regression and SHAP (SHapley Additive exPlanations) for model interpretability.

## Features

- XGBoost regression model training on time series data
- Feature extraction from date fields
- Model performance metrics (RMSE, R²)
- Feature importance analysis
- SHAP analysis with visualizations:
  - Summary plot
  - Bar plot
  - Beeswarm plot
  - Waterfall plot

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- XGBoost
- SHAP
- Pandas
- NumPy
- Scikit-learn
- Matplotlib

## Installation

Make sure you have all the required packages installed:

```bash
pip install fastapi uvicorn xgboost shap pandas numpy scikit-learn matplotlib
```

## Running the API Server

### Windows

```bash
# Navigate to the API directory
cd src/app/api/ml

# Run the server
run_server.bat
```

Or directly:

```bash
python server.py
```

### Unix/Linux/Mac

```bash
# Navigate to the API directory
cd src/app/api/ml

# Make the script executable
chmod +x run_server.sh

# Run the server
./run_server.sh
```

Or directly:

```bash
python server.py
```

The server will start on http://localhost:8000 by default.

## API Documentation

Once the server is running, you can access the auto-generated API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### POST /analyze

Analyzes time series data using XGBoost and SHAP.

**Request Body:**

```json
{
  "data": [
    {
      "date": "2023-01-01",
      "value": 100,
      "other_feature": 1.5
    },
    {
      "date": "2023-01-02",
      "value": 105,
      "other_feature": 2.0
    }
  ],
  "dateColumn": "date",
  "targetColumn": "value"
}
```

**Response:**

```json
{
  "metrics": {
    "train_rmse": 10.5,
    "test_rmse": 12.3,
    "train_r2": 0.85,
    "test_r2": 0.82
  },
  "feature_importance": [
    {
      "feature": "month",
      "importance": 0.45
    },
    {
      "feature": "day_of_week",
      "importance": 0.30
    },
    {
      "feature": "other_feature",
      "importance": 0.25
    }
  ],
  "shap_plots": {
    "summary_plot": "base64_encoded_image",
    "bar_plot": "base64_encoded_image",
    "beeswarm_plot": "base64_encoded_image",
    "waterfall_plot": "base64_encoded_image"
  },
  "timestamp": "2023-06-01T12:34:56.789Z"
}
```

### GET /health

Health check endpoint to verify the API is running.

**Response:**

```json
{
  "status": "healthy"
}
```

## Integration with Frontend

The frontend application is configured to connect to this API server. Make sure the API server is running before using the ML Analysis features in the frontend. 