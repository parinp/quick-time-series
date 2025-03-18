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

## Deployment

### Deploying to Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
4. Add environment variables from your `.env` file
5. Deploy the service

## Architecture

- FastAPI for API endpoints
- Pandas and PyArrow for data processing
- DuckDB for efficient querying
- Redis for caching with TTL-based auto-delete 