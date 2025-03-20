from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import os
import json
import logging
import traceback
from ..utils.redis_client import retrieve_data

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/ml",
    tags=["ml"],
    responses={404: {"description": "Not found"}},
)

# Get ML service URL from environment variables
ML_API_URL = os.getenv("ML_API_URL", "http://localhost:8080")
logger.info(f"ML API URL: {ML_API_URL}")

class MLAnalysisRequest(BaseModel):
    """Request model for ML analysis proxy"""
    dataset_id: str
    date_column: str
    target_column: str
    multiple_waterfall_plots: bool = False
    exclude_columns: Optional[List[str]] = None

class MemoryEfficientMLRequest(BaseModel):
    """Request model for memory-efficient ML analysis proxy"""
    dataset_id: str
    date_column: str
    target_column: str
    exclude_columns: Optional[List[str]] = None
    test_size: float = 0.2
    max_memory_mb: int = 256
    processor_type: Optional[str] = "chunked"  # "chunked", "dask", or "auto"

@router.post("/analyze")
async def analyze_dataset(request: MLAnalysisRequest):
    """
    Proxy endpoint to analyze a dataset using the ML service.
    
    This endpoint:
    1. Verifies the dataset exists in Redis
    2. Calls the ML service to analyze the data directly from Redis
    3. Returns the analysis results
    
    The ML service will handle retrieving the data from Redis and can
    optionally delete it after analysis is complete.
    
    Args:
        request: MLAnalysisRequest with dataset_id, date_column, and target_column
        
    Returns:
        ML analysis results
    """
    try:
        logger.info(f"ML proxy: Analyzing dataset {request.dataset_id}")
        logger.info(f"Date column: {request.date_column}, Target column: {request.target_column}")
        
        # Step 1: Verify the dataset exists in Redis
        # Just check if metadata exists, don't retrieve the actual data
        meta_key = f"{request.dataset_id}:meta"
        metadata = await retrieve_data(meta_key)
        
        if not metadata:
            raise HTTPException(
                status_code=404, 
                detail=f"Dataset not found: {request.dataset_id}"
            )
        
        logger.info(f"Dataset {request.dataset_id} exists in Redis")
        
        # Step 2: Call the ML service
        try:
            async with httpx.AsyncClient() as client:
                # Map the request to ML service format
                ml_request = {
                    "dataset_id": request.dataset_id,
                    "dateColumn": request.date_column,
                    "targetColumn": request.target_column,
                    "multipleWaterfallPlots": request.multiple_waterfall_plots,
                    "delete_after_analysis": True,  # Always clean up after analysis
                    "exclude_columns": request.exclude_columns or []
                }
                
                logger.info(f"Calling ML service at {ML_API_URL}/analyze_from_redis")
                
                # Use a longer timeout for ML analysis (5 minutes)
                response = await client.post(
                    f"{ML_API_URL}/analyze_from_redis",
                    json=ml_request,
                    timeout=300.0
                )
                
                # Check for errors
                if response.status_code != 200:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", error_detail)
                    except:
                        error_detail = response.text
                    
                    logger.error(f"ML service error: {error_detail}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"ML service error: {error_detail}"
                    )
                
                # Parse and return the results
                results = response.json()
                logger.info("ML analysis completed successfully")
                
                return {
                    "success": True,
                    "dataset_id": request.dataset_id,
                    "results": results
                }
                
        except httpx.RequestError as e:
            logger.error(f"Error connecting to ML service: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"ML service unavailable: {str(e)}"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in ML proxy: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze the dataset: {str(e)}"
        )

@router.post("/analyze_efficient")
async def analyze_dataset_efficiently(request: MemoryEfficientMLRequest):
    """
    Proxy endpoint to analyze a dataset using the memory-efficient ML service.
    
    This endpoint:
    1. Verifies the dataset exists in Redis
    2. Calls the ML service's memory-efficient endpoint
    3. Returns the analysis results
    
    The ML service will handle retrieving the data from Redis and can
    optionally delete it after analysis is complete. This endpoint is optimized
    for the GCP free tier with memory and CPU constraints.
    
    Args:
        request: MemoryEfficientMLRequest with dataset_id, date_column, and target_column
        
    Returns:
        ML analysis results with resource usage metrics
    """
    try:
        logger.info(f"ML proxy: Analyzing dataset {request.dataset_id} with memory-efficient processing")
        logger.info(f"Date column: {request.date_column}, Target column: {request.target_column}")
        logger.info(f"Memory limit: {request.max_memory_mb} MB, Processor: {request.processor_type}")
        
        # Step 1: Verify the dataset exists in Redis
        # Just check if metadata exists, don't retrieve the actual data
        meta_key = f"{request.dataset_id}:meta"
        metadata = await retrieve_data(meta_key)
        
        if not metadata:
            raise HTTPException(
                status_code=404, 
                detail=f"Dataset not found: {request.dataset_id}"
            )
        
        logger.info(f"Dataset {request.dataset_id} exists in Redis")
        
        # Step 2: Call the ML service's memory-efficient endpoint
        try:
            async with httpx.AsyncClient() as client:
                # Map the request to ML service format
                ml_request = {
                    "dataset_id": request.dataset_id,
                    "dateColumn": request.date_column,
                    "targetColumn": request.target_column,
                    "exclude_columns": request.exclude_columns or [],
                    "test_size": request.test_size,
                    "max_memory_mb": request.max_memory_mb,
                    "processor_type": request.processor_type,
                    "delete_after_analysis": True  # Always clean up after analysis
                }
                
                logger.info(f"Calling ML service at {ML_API_URL}/memory_efficient_analyze")
                
                # Use a longer timeout for ML analysis (5 minutes)
                response = await client.post(
                    f"{ML_API_URL}/memory_efficient_analyze",
                    json=ml_request,
                    timeout=300.0
                )
                
                # Check for errors
                if response.status_code != 200:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", error_detail)
                    except:
                        error_detail = response.text
                    
                    logger.error(f"ML service error: {error_detail}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"ML service error: {error_detail}"
                    )
                
                # Parse and return the results
                results = response.json()
                logger.info("Memory-efficient ML analysis completed successfully")
                
                # Add resource usage information if available
                resource_info = {}
                if "resource_usage" in results:
                    resource_info = {
                        "peak_memory_mb": results["resource_usage"].get("peak_memory_mb", 0),
                        "processing_time_seconds": results["resource_usage"].get("processing_time_seconds", 0),
                        "processor_used": results.get("processor_used", "unknown")
                    }
                    
                    # Add GCP free tier estimates if available
                    if "estimated_monthly_usage" in results["resource_usage"]:
                        resource_info["estimated_monthly_usage"] = results["resource_usage"]["estimated_monthly_usage"]
                
                return {
                    "success": True,
                    "dataset_id": request.dataset_id,
                    "resource_usage": resource_info,
                    "results": results
                }
                
        except httpx.RequestError as e:
            logger.error(f"Error connecting to ML service: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"ML service unavailable: {str(e)}"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in ML proxy: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze the dataset: {str(e)}"
        ) 