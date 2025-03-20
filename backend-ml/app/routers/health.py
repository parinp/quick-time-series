from fastapi import APIRouter, HTTPException
from typing import Dict, Any

# Create router
router = APIRouter(tags=["health"])

@router.get("/")
async def root():
    """Root endpoint that provides API information."""
    return {
        "message": "Welcome to the ML Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "/": "GET - This information",
            "/analyze": "POST - Analyze time series data directly",
            "/analyze_from_redis": "POST - Analyze time series data from Redis",
            "/memory_efficient_analyze": "POST - Analyze time series data from Redis using memory-efficient processing",
            "/health": "GET - Health check"
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "healthy"} 