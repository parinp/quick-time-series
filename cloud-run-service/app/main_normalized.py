from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import pandas as pd
import json
import os
from datetime import datetime, date

# Import the normalized client
from supabase_normalized_client import (
    get_rossmann_data,
    get_rossmann_stores,
    get_rossmann_sales_by_date,
    get_rossmann_sales_by_store,
    get_rossmann_dataset_info
)

# Create FastAPI app
app = FastAPI(
    title="Time Series Analysis API",
    description="API for time series analysis and forecasting",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define request models
class RossmannDataRequest(BaseModel):
    store_id: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = 1000

class RossmannAggregateRequest(BaseModel):
    store_id: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Time Series Analysis API is running"}

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Endpoint to get Rossmann dataset info
@app.get("/rossmann/info")
async def get_info():
    try:
        return get_rossmann_dataset_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get Rossmann data
@app.post("/rossmann/data")
async def get_data(request: RossmannDataRequest):
    try:
        data = get_rossmann_data(
            store_id=request.store_id,
            date_from=request.date_from,
            date_to=request.date_to,
            limit=request.limit
        )
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get all Rossmann stores
@app.get("/rossmann/stores")
async def get_stores():
    try:
        stores = get_rossmann_stores()
        return {"stores": stores, "count": len(stores)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get Rossmann sales aggregated by date
@app.post("/rossmann/sales_by_date")
async def get_sales_by_date(request: RossmannAggregateRequest):
    try:
        data = get_rossmann_sales_by_date(
            store_id=request.store_id,
            date_from=request.date_from,
            date_to=request.date_to
        )
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get Rossmann sales aggregated by store
@app.post("/rossmann/sales_by_store")
async def get_sales_by_store(request: RossmannAggregateRequest):
    try:
        data = get_rossmann_sales_by_store(
            date_from=request.date_from,
            date_to=request.date_to
        )
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Simple endpoint to get data for a specific store with GET parameters
@app.get("/rossmann/store/{store_id}")
async def get_store_data(
    store_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100
):
    try:
        data = get_rossmann_data(
            store_id=store_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 