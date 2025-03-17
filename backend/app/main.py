from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.routers import upload, query

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Time Series Analysis API",
    description="API for time series data analysis with CSV to Parquet conversion and DuckDB querying",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(query.router)

@app.get("/")
async def root():
    return {
        "message": "Time Series Analysis API",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 