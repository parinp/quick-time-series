# Time Series Analysis API

A FastAPI backend for analyzing time series data using XGBoost and SHAP.

## Project Structure

The project follows a modular structure with the following organization:

```
backend-ml/
├── app/                     # Main application package
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI app initialization
│   ├── routers/             # API route definitions
│   │   ├── __init__.py      # Routers package initialization
│   │   ├── analysis.py      # Analysis endpoints
│   │   ├── health.py        # Health check endpoints
│   │   └── model.py         # Pydantic models
│   └── utils/               # Utility functions
│       ├── __init__.py      # Utils package initialization
│       ├── analysis.py      # Data analysis functions
│       ├── redis_client.py  # Redis integration
│       ├── duckdb_processor.py  # DuckDB processor
│       ├── memory_efficient_ml.py  # Memory-efficient ML
│       ├── dask_processor.py  # Dask processor
│       └── chunked_processor.py  # Chunked processor
├── server.py                # Original server implementation
├── run_app.py               # Entry point for running the app
└── requirements.txt         # Package dependencies
```

## API Endpoints

- `/` - Root endpoint with API information
- `/health` - Health check endpoint
- `/analyze` - Analyze time series data
- `/analyze_from_redis` - Analyze time series data from Redis
- `/memory_efficient_analyze` - Memory-efficient analysis from Redis

## Getting Started

### Prerequisites

- Python 3.7+
- Redis (or Upstash Redis)
- Required Python packages (see requirements.txt)

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file with:
   ```
   REDIS_URL=your_redis_url
   REDIS_TOKEN=your_redis_token
   ```

### Running the API

Run the API using:

```
python run_app.py
```

This will start the server at http://0.0.0.0:8080 with auto-reload enabled.

## Making Requests

### Analyze Data Directly

```
POST /analyze
{
  "data": [{"date": "2023-01-01", "value": 100, ...}, ...],
  "dateColumn": "date",
  "targetColumn": "value",
  "multipleWaterfallPlots": false
}
```

### Analyze Data from Redis

```
POST /analyze_from_redis
{
  "dataset_id": "your_dataset_id",
  "dateColumn": "date",
  "targetColumn": "value",
  "multipleWaterfallPlots": false,
  "delete_after_analysis": true,
  "exclude_columns": ["col1", "col2"]
}
```

### Memory-Efficient Analysis

```
POST /memory_efficient_analyze
{
  "dataset_id": "your_dataset_id",
  "dateColumn": "date",
  "targetColumn": "value",
  "exclude_columns": ["col1", "col2"],
  "test_size": 0.2,
  "max_memory_mb": 100,
  "processor_type": "auto",
  "delete_after_analysis": true
}
```

## Development

To add new endpoints, create a new module in the `app/routers` directory and register the router in `app/main.py`.

## Note on Original Code

The project was restructured from a single-file implementation (server.py) to a modular package structure. The original functionality is preserved, with the code organized into modules for better maintainability.

The original `server.py` file is kept for reference, but the application now uses the modular structure with `run_app.py` as the entry point. 