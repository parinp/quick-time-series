# Time Series Analysis Backend

This is the backend service for the Time Series Analysis application. It provides APIs for uploading CSV files, converting them to Parquet format, and querying the data using DuckDB.

## Features

- CSV to Parquet conversion
- Redis caching with TTL-based auto-delete
- DuckDB for efficient data querying
- FastAPI for high-performance API endpoints

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Redis (Upstash Redis recommended)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the `.env.example` file to `.env` and update the values:
   ```bash
   cp .env.example .env
   ```
4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Upload API

- `POST /upload`: Upload a CSV file for time series analysis
  - Converts CSV to Parquet format
  - Stores in Redis with TTL-based auto-delete
  - Returns dataset ID and metadata

### Query API

- `GET /query/{dataset_id}`: Query a dataset with filters
  - Retrieves Parquet data from Redis
  - Loads into DuckDB for efficient querying
  - Returns only the filtered data
- `GET /query/{dataset_id}/metadata`: Get metadata about a dataset
- `GET /query/{dataset_id}/columns`: Get the columns of a dataset

### ML Analysis API

- `POST /ml/analyze`: Analyze a dataset using ML
  - Proxies the request to the ML service
  - The ML service retrieves data directly from Redis
  - Returns analysis results including metrics and feature importance

- `POST /ml/analyze_efficient`: Analyze a dataset using memory-efficient ML
  - Optimized for GCP free tier (256MB memory, 1 vCPU)
  - Uses chunked processing to keep memory usage low
  - Returns analysis results with detailed resource usage metrics
  - Sample request:
    ```json
    {
      "dataset_id": "your_dataset_id",
      "date_column": "date",
      "target_column": "target",
      "exclude_columns": ["column1", "column2"],
      "test_size": 0.2,
      "max_memory_mb": 256,
      "processor_type": "chunked"
    }
    ```
  - Sample response:
    ```json
    {
      "success": true,
      "dataset_id": "your_dataset_id",
      "resource_usage": {
        "peak_memory_mb": 200,
        "processing_time_seconds": 2.5,
        "processor_used": "chunked",
        "estimated_monthly_usage": {
          "monthly_requests": 1000000,
          "percent_free_tier_memory": 15.5,
          "percent_free_tier_vcpu": 139.4
        }
      },
      "results": {
        "metrics": {
          "rmse": 1.23,
          "r2": 0.85
        },
        "feature_importance": [
          {"feature": "feature1", "importance": 0.45},
          {"feature": "feature2", "importance": 0.30}
        ]
      }
    }
    ```

## Deployment

### Deploying to Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
4. Add environment variables from your `.env` file
5. Deploy the service

## Running with ML Backend

For full functionality including machine learning analysis, you need to run both this data backend and the ML backend:

1. Start the ML backend:
   ```bash
   cd backend-ml
   python server.py
   ```

2. Start the data backend (this repo):
   ```bash
   cd backend-data
   python -m uvicorn app.main:app --reload --port 8000
   ```

The ML backend provides XGBoost regression analysis with SHAP explanations, while this data backend handles data storage, retrieval, and ML proxying.

## Memory-Efficient ML Analysis

This backend includes an endpoint to proxy requests to the memory-efficient ML implementation in the ML backend, optimized for the GCP free tier (256MB memory, 1 vCPU).

### Using the Memory-Efficient ML Endpoint

To use the memory-efficient ML implementation, make a POST request to:

```
POST /ml/analyze_efficient
```

Example request body:
```json
{
  "dataset_id": "your_dataset_id",
  "date_column": "date",
  "target_column": "target",
  "max_memory_mb": 256,
  "processor_type": "chunked"
}
```

Parameters:
- `dataset_id`: ID of the dataset stored in Redis
- `date_column`: Name of the date column in the dataset
- `target_column`: Name of the target column for prediction
- `max_memory_mb`: Maximum memory target in MB (default: 256)
- `processor_type`: Type of processor to use (`chunked`, `dask`, or `auto`)

This endpoint is ideal for resource-constrained environments or when processing large datasets that may exceed memory limits.

## Architecture

- FastAPI for API endpoints
- Pandas and PyArrow for data processing
- DuckDB for efficient querying
- Redis for caching with TTL-based auto-delete 