# Project Structure

This document provides an overview of the project structure for the Time Series Analysis API.

## Directory Structure

```
cloud-run-service/
├── app/                        # Main application code
│   ├── __init__.py             # Package initialization
│   ├── main.py                 # FastAPI application entry point
│   ├── eda.py                  # Exploratory data analysis module
│   ├── model.py                # Model training and prediction module
│   ├── utils.py                # Utility functions for data processing
│   └── supabase_client.py      # Supabase database client
├── .dockerignore               # Files to exclude from Docker build
├── .env.example                # Template for environment variables
├── .gitignore                  # Git ignore file
├── Dockerfile                  # Docker configuration
├── PROJECT_STRUCTURE.md        # This file
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
├── supabase_setup.sql          # SQL scripts for Supabase setup
└── upload_sample_data.py       # Script to upload sample data to Supabase
```

## Module Descriptions

### app/main.py

The main FastAPI application that defines all API endpoints. It handles:
- API routing
- Request validation using Pydantic models
- Response formatting
- Error handling
- Integration with other modules

### app/eda.py

Exploratory Data Analysis module that provides:
- Time series analysis functions
- Statistical analysis
- Visualization generation
- Seasonal decomposition
- Autocorrelation analysis

### app/model.py

Model training and prediction module that includes:
- XGBoost model training
- Time series cross-validation
- Feature importance calculation
- SHAP value generation for model interpretation
- Change point detection
- Prediction functions

### app/utils.py

Utility functions for data processing:
- Time feature engineering
- Lag feature creation
- Rolling window feature creation
- Outlier detection
- Missing value imputation
- Data scaling
- JSON serialization helpers

### app/supabase_client.py

Supabase database client that handles:
- Connection to Supabase
- Sample data retrieval
- Model results storage
- Prediction storage
- Sample data upload

## Configuration Files

### Dockerfile

Defines the Docker container configuration for deployment to Google Cloud Run.

### requirements.txt

Lists all Python package dependencies with specific versions.

### .env.example

Template for environment variables needed by the application.

### supabase_setup.sql

SQL scripts to set up the necessary tables and permissions in Supabase.

## Scripts

### upload_sample_data.py

Script to upload sample datasets to Supabase for demonstration purposes. 