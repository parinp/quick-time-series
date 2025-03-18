from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.routers import upload, query, ml_proxy

# Load environment variables
load_dotenv()

# Get ML API URL from environment variables
ML_API_URL = os.getenv("ML_API_URL", "http://localhost:8080")

app = FastAPI(
    title="Time Series Analysis API",
    description="API for time series data analysis with CSV to Parquet conversion and DuckDB querying",
    version="2.0.0"
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(query.router)
app.include_router(ml_proxy.router)

@app.get("/")
async def root():
    return {
        "message": "Time Series Analysis API",
        "version": "2.0.0",
        "status": "running",
        "ml_api": ML_API_URL,
        "endpoints": {
            "/upload": "POST - Upload CSV files for analysis",
            "/query/{dataset_id}": "GET - Query dataset with optional filters",
            "/ml/analyze": "POST - Analyze dataset using ML service"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 