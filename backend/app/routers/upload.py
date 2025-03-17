from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
import os
import traceback
from typing import Optional

from app.utils.csv_parser import parse_csv
from app.utils.parquet_converter import convert_to_parquet
from app.utils.redis_client import store_data, DEFAULT_TTL

router = APIRouter(
    prefix="/upload",
    tags=["upload"],
    responses={404: {"description": "Not found"}},
)

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes

@router.post("/")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a CSV file for time series analysis.
    
    - Converts CSV to Parquet format
    - Stores in Redis with a fixed TTL of 15 minutes
    - Returns dataset ID and metadata
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # Generate a unique ID for this dataset
    dataset_id = str(uuid.uuid4())
    
    try:
        # Read file content
        contents = await file.read()
        
        # Check file size
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File size exceeds the 50MB limit")
        
        # Parse CSV data
        try:
            parsed_data = await parse_csv(contents)
        except Exception as e:
            print(f"CSV parsing error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
        
        if not parsed_data or len(parsed_data) == 0:
            raise HTTPException(status_code=400, detail="No data found in the CSV file")
        
        # Get a sample row for column info
        sample_row = parsed_data[0]
        column_info = {col: str(type(val).__name__) for col, val in sample_row.items()}
        
        print(f"Parsed {len(parsed_data)} rows with columns: {list(column_info.keys())}")
        print(f"Column types: {column_info}")
        
        # Convert to Parquet (run in background to avoid blocking)
        background_tasks.add_task(
            process_and_store_data,
            dataset_id,
            parsed_data,
            file.filename
        )
        
        # Calculate expiry time in minutes
        minutes = DEFAULT_TTL // 60
        seconds = DEFAULT_TTL % 60
        expiry_text = f"{minutes} minutes"
        if seconds > 0:
            expiry_text += f", {seconds} seconds"
        
        # Return immediate response with dataset ID
        return {
            "success": True,
            "message": "File upload started, processing in background",
            "dataset_id": dataset_id,
            "ttl_seconds": DEFAULT_TTL,
            "expiry_time": f"Data will be available for {expiry_text}",
            "row_count_estimate": len(parsed_data),
            "columns": list(sample_row.keys()) if parsed_data else [],
            "column_types": column_info
        }
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        print(f"Unhandled error in upload_file: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to process the file: {str(e)}")

async def process_and_store_data(dataset_id: str, data: list, filename: str):
    """Background task to convert data to Parquet and store in Redis"""
    try:
        # Convert to Parquet
        try:
            parquet_buffer = await convert_to_parquet(data)
            print(f"Successfully converted {len(data)} rows to Parquet format")
        except Exception as e:
            print(f"Error in Parquet conversion: {str(e)}")
            print(traceback.format_exc())
            # Continue with default handling - the converter should fall back to JSON
            raise e
        
        # Store in Redis with fixed TTL
        try:
            success = await store_data(
                dataset_id, 
                {
                    "parquet_data": parquet_buffer.to_pybytes(),
                    "filename": filename,
                    "timestamp": str(uuid.uuid1()),
                    "row_count": len(data),
                    "columns": list(data[0].keys()) if data else []
                }
            )
            
            if success:
                print(f"Successfully stored dataset {dataset_id} in Redis with TTL {DEFAULT_TTL}s")
            else:
                print(f"Failed to store dataset {dataset_id} in Redis")
        except Exception as e:
            print(f"Error storing data in Redis: {str(e)}")
            print(traceback.format_exc())
    except Exception as e:
        print(f"Error in background processing: {str(e)}")
        print(traceback.format_exc()) 