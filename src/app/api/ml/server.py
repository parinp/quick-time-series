from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging
import os
from utils import analyze_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ML Analysis API",
    description="API for XGBoost regression and SHAP analysis",
    version="1.0.0",
)

# Get port from environment variable for Cloud Run
PORT = int(os.getenv("PORT", "8080"))

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:8000",  # Local API development
        "https://simple-timeseries-analysis.vercel.app",  # Vercel production
        "https://simple-timeseries-analysis.onrender.com",  # Render backend
        "*",  # Allow all origins during development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Define request model
class AnalysisRequest(BaseModel):
    data: List[Dict[str, Any]]
    dateColumn: str
    targetColumn: str
    multipleWaterfallPlots: bool = False

# Define API endpoints
@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    """
    Analyze data using XGBoost and SHAP.
    
    Args:
        request: AnalysisRequest with data, dateColumn, and targetColumn
    
    Returns:
        Analysis results including metrics, feature importance, and SHAP plots
    """
    try:
        logger.info(f"Analyzing data with {len(request.data)} records")
        logger.info(f"Date column: {request.dateColumn}")
        logger.info(f"Target column: {request.targetColumn}")
        logger.info(f"Multiple waterfall plots: {request.multipleWaterfallPlots}")
        
        if len(request.data) > 0:
            sample_row = request.data[0]
            logger.info(f"Available columns: {list(sample_row.keys())}")
        
        # Analyze the data
        results = analyze_data(request.data, request.dateColumn, request.targetColumn, request.multipleWaterfallPlots)
        
        return results
    
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "An error occurred during analysis", "message": str(e)}
        )

@app.get("/")
async def root():
    """
    Root endpoint that provides API information.
    """
    return {
        "message": "Welcome to the ML Analysis API",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "endpoints": {
            "/": "GET - This information",
            "/analyze": "POST - Analyze time series data",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "healthy"}

# Run the server if this file is executed directly
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=False) 