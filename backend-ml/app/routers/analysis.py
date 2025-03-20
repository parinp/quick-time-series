from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import asyncio
import logging
import traceback
import time
from datetime import datetime
import pandas as pd
import numpy as np

# Import models
from .model import AnalysisRequest, RedisAnalysisRequest, MemoryEfficientAnalysisRequest 

# Import utilities
from ..utils.analysis import analyze_data
from ..utils.redis_client import retrieve_parquet_data, delete_dataset
from ..utils.duckdb_processor import process_parquet_for_ml, filter_data_by_column_types
from ..utils.memory_efficient_ml import MemoryEfficientML

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["analysis"])

# Define API endpoints
@router.post("/analyze")
async def analyze(request: AnalysisRequest):
    """Analyze time series data using XGBoost and SHAP."""
    try:
        logger.info(f"Analyzing data with {len(request.data)} records")
        logger.info(f"Date column: {request.dateColumn}")
        logger.info(f"Target column: {request.targetColumn}")
        logger.info(f"Multiple waterfall plots: {request.multipleWaterfallPlots}")
        
        if len(request.data) > 0:
            sample_row = request.data[0]
            logger.info(f"Available columns: {list(sample_row.keys())}")
        
        results = analyze_data(
            request.data, 
            request.dateColumn, 
            request.targetColumn, 
            request.multipleWaterfallPlots
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "An error occurred during analysis", "message": str(e)}
        )

@router.post("/analyze_from_redis")
async def analyze_from_redis(request: RedisAnalysisRequest):
    """Analyze time series data stored in Redis."""
    start_time = time.time()
    
    try:
        logger.info(f"Analyzing data from Redis for dataset ID: {request.dataset_id}")
        logger.info(f"Date column: {request.dateColumn}")
        logger.info(f"Target column: {request.targetColumn}")
        logger.info(f"Multiple waterfall plots: {request.multipleWaterfallPlots}")
        logger.info(f"Exclude columns: {request.exclude_columns}")
        
        # Step 1: Retrieve data from Redis
        parquet_data = await retrieve_parquet_data(request.dataset_id)
        if not parquet_data:
            raise HTTPException(
                status_code=404, 
                detail={"error": "Dataset not found", "message": f"No data found for dataset ID: {request.dataset_id}"}
            )
        
        redis_time = time.time()
        logger.info(f"Retrieved {len(parquet_data)} bytes from Redis in {redis_time - start_time:.2f} seconds")
        
        # Step 2: Process the Parquet data using DuckDB to select relevant columns
        try:
            df = await process_parquet_for_ml(
                parquet_data, 
                request.dateColumn, 
                request.targetColumn, 
                request.exclude_columns
            )
            
            # Further filter to only include numeric columns
            df = await filter_data_by_column_types(
                df, 
                request.dateColumn, 
                request.targetColumn
            )
            
            logger.info(f"Processed data shape: {df.shape}")
            
        except ValueError as ve:
            logger.error(f"Error processing data: {str(ve)}")
            raise HTTPException(
                status_code=400,
                detail={"error": "Invalid column names", "message": str(ve)}
            )
        
        processing_time = time.time()
        logger.info(f"Processed parquet data in {processing_time - redis_time:.2f} seconds")
        
        # Step 3: Convert DataFrame to list of dictionaries
        records = df.to_dict(orient='records')
        logger.info(f"Converted DataFrame to {len(records)} records")
        
        # Step 4: Analyze the data
        results = analyze_data(
            records, 
            request.dateColumn, 
            request.targetColumn, 
            request.multipleWaterfallPlots
        )
        
        analysis_time = time.time()
        logger.info(f"Analyzed data in {analysis_time - processing_time:.2f} seconds")
        
        # Step 5: Delete data from Redis if requested
        if request.delete_after_analysis:
            success = await delete_dataset(request.dataset_id)
            if success:
                logger.info(f"Deleted dataset {request.dataset_id} from Redis")
            else:
                logger.warning(f"Failed to delete dataset {request.dataset_id} from Redis")
        
        # Add timing information to results
        total_time = time.time() - start_time
        results["timing"] = {
            "redis_retrieval_seconds": redis_time - start_time,
            "processing_seconds": processing_time - redis_time,
            "analysis_seconds": analysis_time - processing_time,
            "total_seconds": total_time
        }
        
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

@router.post("/memory_efficient_analyze")
async def memory_efficient_analyze(request: MemoryEfficientAnalysisRequest):
    """
    Analyze time series data using memory-efficient processing.
    Optimized for single-CPU environments like GCP Cloud Run.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Memory-efficient analysis for dataset ID: {request.dataset_id}")
        logger.info(f"Date column: {request.dateColumn}")
        logger.info(f"Target column: {request.targetColumn}")
        logger.info(f"Processor type: {request.processor_type}")
        logger.info(f"Max memory: {request.max_memory_mb} MB")
        
        # Step 1: Retrieve data from Redis
        parquet_data = await retrieve_parquet_data(request.dataset_id)
        if not parquet_data:
            raise HTTPException(
                status_code=404, 
                detail={"error": "Dataset not found", "message": f"No data found for dataset ID: {request.dataset_id}"}
            )
        
        redis_time = time.time()
        logger.info(f"Retrieved {len(parquet_data)} bytes from Redis in {redis_time - start_time:.2f} seconds")
        
        # Step 2: Process with memory-efficient ML
        try:
            # Initialize the ML processor
            ml_processor = MemoryEfficientML(
                max_memory_mb=request.max_memory_mb,
                processor_type=request.processor_type
            )
            
            # Process the parquet data
            result = await ml_processor.process_parquet_bytes(
                parquet_data=parquet_data,
                date_column=request.dateColumn,
                target_column=request.targetColumn,
                exclude_columns=request.exclude_columns,
                test_size=request.test_size
            )
            
            logger.info(f"Memory-efficient analysis completed successfully with processor: {result.get('processor_type', 'unknown')}")
            
            # Sanitize the result to handle any infinite or NaN values
            def sanitize_value(val):
                if isinstance(val, float):
                    if np.isnan(val) or np.isinf(val):
                        return 0.0
                    return float(val)
                elif isinstance(val, dict):
                    return {k: sanitize_value(v) for k, v in val.items()}
                elif isinstance(val, list):
                    return [sanitize_value(item) for item in val]
                return val
            
            # Apply sanitization to the entire result dictionary
            result = sanitize_value(result)
            
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail={"error": "Invalid request", "message": str(ve)}
            )
        except Exception as analyze_error:
            logger.error(f"Error in memory efficient analysis: {str(analyze_error)}", exc_info=True)
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail={"error": "Analysis error", "message": str(analyze_error)}
            )
            
        # Step 3: Delete data from Redis if requested
        if request.delete_after_analysis:
            success = await delete_dataset(request.dataset_id)
            if success:
                logger.info(f"Deleted dataset {request.dataset_id} from Redis")
            else:
                logger.warning(f"Failed to delete dataset {request.dataset_id} from Redis")
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "An error occurred", "message": str(e)}
        ) 