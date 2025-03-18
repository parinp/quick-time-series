from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import json
import traceback

from app.utils.redis_client import retrieve_data
from app.utils.duckdb_query import query_parquet_data

router = APIRouter(
    prefix="/query",
    tags=["query"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{dataset_id}")
async def query_dataset(
    dataset_id: str,
    filters: Optional[str] = Query(None, description="JSON string of filters to apply"),
    limit: Optional[int] = Query(1000, description="Maximum number of rows to return"),
    offset: Optional[int] = Query(0, description="Number of rows to skip"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    sort_order: Optional[str] = Query("asc", description="Sort order (asc or desc)"),
    date_column: Optional[str] = Query(None, description="Date column for GROUP BY"),
    target_column: Optional[str] = Query(None, description="Target column for aggregation (SUM)"),
):
    """
    Query a dataset with filters.
    
    - Retrieves Parquet data from Redis
    - Loads into DuckDB for efficient querying
    - Returns only the filtered data
    - If date_column and target_column are provided, performs GROUP BY on date_column with SUM on target_column
    
    Filters format example:
    {
        "column1": {"operator": "=", "value": 100},
        "column2": {"operator": ">", "value": "2023-01-01"}
    }
    """
    try:
        # Debug logs for request parameters
        print(f"Query parameters received:")
        print(f"dataset_id: {dataset_id}")
        print(f"limit: {limit}")
        print(f"offset: {offset}")
        print(f"sort_by: {sort_by}")
        print(f"sort_order: {sort_order}")
        print(f"date_column: {date_column}")
        print(f"target_column: {target_column}")
        
        # Retrieve data from Redis
        data = await retrieve_data(dataset_id)
        
        if not data:
            raise HTTPException(status_code=404, detail="Dataset not found or expired")
        
        # Parse filters if provided
        filter_dict = {}
        if filters:
            try:
                filter_dict = json.loads(filters)
                print(f"Applying filters: {filter_dict}")
            except json.JSONDecodeError as e:
                print(f"Filter parsing error: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid filter format: {str(e)}")
        
        # Get available columns
        available_columns = data.get("columns", [])
        
        # Validate sort column
        if sort_by and sort_by not in available_columns:
            print(f"Invalid sort column: {sort_by} not in {available_columns}")
            raise HTTPException(status_code=400, detail=f"Sort column '{sort_by}' not found in dataset columns")
        
        # Validate filter columns
        for column in filter_dict.keys():
            if column not in available_columns:
                print(f"Invalid filter column: {column} not in {available_columns}")
                raise HTTPException(status_code=400, detail=f"Filter column '{column}' not found in dataset columns")
        
        # Validate aggregation columns
        aggregate = None
        if date_column and target_column:
            if date_column not in available_columns:
                raise HTTPException(status_code=400, detail=f"Date column '{date_column}' not found in dataset columns")
            if target_column not in available_columns:
                raise HTTPException(status_code=400, detail=f"Target column '{target_column}' not found in dataset columns")
            
            print(f"Using aggregation: GROUP BY {date_column}, SUM({target_column})")
            aggregate = {
                'date_column': date_column,
                'target_column': target_column
            }
        
        # Query the data using DuckDB
        try:
            result = await query_parquet_data(
                data["parquet_data"],
                filter_dict,
                limit,
                offset,
                sort_by or date_column,  # If no sort_by is provided but we're aggregating, sort by date
                sort_order,
                aggregate
            )
            
            print(f"Query returned {len(result)} rows out of {data.get('row_count', 0)}")
            
            # Return the result with metadata
            return {
                "success": True,
                "dataset_id": dataset_id,
                "filtered_row_count": len(result),
                "total_row_count": data.get("row_count", 0),
                "data": result,
                "aggregated": aggregate is not None
            }
        except Exception as e:
            print(f"DuckDB query error: {str(e)}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Error querying data: {str(e)}")
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        print(f"Unhandled error in query_dataset: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to query the dataset: {str(e)}")

@router.get("/{dataset_id}/metadata")
async def get_dataset_metadata(dataset_id: str):
    """Get metadata about a dataset without retrieving the actual data"""
    try:
        # Retrieve data from Redis
        data = await retrieve_data(dataset_id)
        
        if not data:
            raise HTTPException(status_code=404, detail="Dataset not found or expired")
        
        # Return metadata only
        return {
            "success": True,
            "dataset_id": dataset_id,
            "filename": data.get("filename", "unknown"),
            "timestamp": data.get("timestamp", "unknown"),
            "row_count": data.get("row_count", 0),
            "columns": data.get("columns", [])
        }
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he 
    except Exception as e:
        print(f"Error retrieving dataset metadata: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dataset metadata: {str(e)}")

@router.get("/{dataset_id}/columns")
async def get_dataset_columns(dataset_id: str):
    """Get the columns of a dataset"""
    try:
        # Retrieve data from Redis
        data = await retrieve_data(dataset_id)
        
        if not data:
            raise HTTPException(status_code=404, detail="Dataset not found or expired")
        
        # Return columns only
        return {
            "success": True,
            "dataset_id": dataset_id,
            "columns": data.get("columns", [])
        }
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        print(f"Error retrieving dataset columns: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dataset columns: {str(e)}") 