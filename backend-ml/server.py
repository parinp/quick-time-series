from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging
import asyncio
import traceback
from utils import analyze_data
import redis_client
import duckdb_processor

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

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:8000",  # Local API development
        "https://simple-timeseries-analysis.vercel.app",  # Vercel production
        "*",  # Allow all origins during development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Define request models
class AnalysisRequest(BaseModel):
    data: List[Dict[str, Any]]
    dateColumn: str
    targetColumn: str
    multipleWaterfallPlots: bool = False

class RedisAnalysisRequest(BaseModel):
    """Request model for analyzing data from Redis"""
    dataset_id: str
    dateColumn: str
    targetColumn: str
    multipleWaterfallPlots: bool = False
    delete_after_analysis: bool = True
    exclude_columns: Optional[List[str]] = None

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

@app.post("/analyze_from_redis")
async def analyze_from_redis(request: RedisAnalysisRequest):
    """
    Analyze data stored in Redis.
    
    This endpoint retrieves data from Redis, processes it using DuckDB,
    and performs ML analysis. If requested, it also deletes the data
    from Redis after analysis is complete.
    
    Args:
        request: RedisAnalysisRequest with dataset_id, dateColumn, and targetColumn
    
    Returns:
        Analysis results including metrics, feature importance, and SHAP plots
    """
    try:
        logger.info(f"Analyzing data from Redis for dataset ID: {request.dataset_id}")
        logger.info(f"Date column: {request.dateColumn}")
        logger.info(f"Target column: {request.targetColumn}")
        logger.info(f"Multiple waterfall plots: {request.multipleWaterfallPlots}")
        logger.info(f"Delete after analysis: {request.delete_after_analysis}")
        
        # Step 1: Retrieve data from Redis
        parquet_data = await redis_client.retrieve_parquet_data(request.dataset_id)
        
        if not parquet_data:
            raise HTTPException(
                status_code=404, 
                detail={"error": "Dataset not found", "message": f"No data found for dataset ID: {request.dataset_id}"}
            )
        
        logger.info(f"Retrieved {len(parquet_data)} bytes from Redis")
        
        # Step 2: Process the Parquet data using DuckDB to select relevant columns
        try:
            df = await duckdb_processor.process_parquet_for_ml(
                parquet_data,
                request.dateColumn,
                request.targetColumn,
                request.exclude_columns
            )
            
            # Further filter to only include numeric and boolean columns
            df = await duckdb_processor.filter_data_by_column_types(
                df, 
                request.dateColumn,
                request.targetColumn
            )
            
            logger.info(f"Processed data shape: {df.shape}")
            
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail={"error": "Invalid column names", "message": str(ve)}
            )
        
        # Step 3: Convert DataFrame to list of dictionaries for analyze_data
        records = df.to_dict(orient='records')
        logger.info(f"Converted DataFrame to {len(records)} records")
        
        # Step 4: Analyze the data
        try:
            results = analyze_data(
                records, 
                request.dateColumn, 
                request.targetColumn, 
                request.multipleWaterfallPlots
            )
            logger.info("Analysis completed successfully")
        except Exception as analyze_error:
            logger.error(f"Error in analyze_data: {str(analyze_error)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Analysis error", "message": str(analyze_error)}
            )
        
        # Step 5: Delete data from Redis if requested
        if request.delete_after_analysis:
            # Use asyncio.create_task to delete data asynchronously
            # This way, we don't make the client wait for the deletion to complete
            asyncio.create_task(redis_client.delete_dataset(request.dataset_id))
            logger.info(f"Scheduled deletion of dataset {request.dataset_id}")
        
        return results
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "An error occurred", "message": str(e)}
        )

@app.get("/")
async def root():
    """
    Root endpoint that provides API information.
    """
    return {
        "message": "Welcome to the ML Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "/": "GET - This information",
            "/analyze": "POST - Analyze time series data directly",
            "/analyze_from_redis": "POST - Analyze time series data from Redis",
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
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True) 