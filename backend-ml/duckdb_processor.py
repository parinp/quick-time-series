import duckdb
import io
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import logging
from typing import Dict, List, Any, Optional, Set

# Configure logging
logger = logging.getLogger(__name__)

async def process_parquet_for_ml(
    parquet_data: bytes,
    date_column: str,
    target_column: str,
    exclude_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Process Parquet data using DuckDB, selecting only the relevant columns for ML.
    
    Args:
        parquet_data: Parquet data as bytes
        date_column: Name of the date column (will be included but can be used for filtering)
        target_column: Name of the target column for ML prediction
        exclude_columns: Additional columns to exclude
        
    Returns:
        Pandas DataFrame with selected columns
    """
    try:
        # Create a buffer from the content
        buffer = io.BytesIO(parquet_data)
        
        # Read as a PyArrow table for column inspection
        table = pq.read_table(buffer)
        all_columns = table.column_names
        logger.info(f"Parquet file has {len(all_columns)} columns: {all_columns}")
        
        # Determine which columns to use for ML
        columns_to_exclude = set()
        
        # Always include date and target columns
        if date_column not in all_columns:
            raise ValueError(f"Date column '{date_column}' not found in data")
        
        if target_column not in all_columns:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        # Add user-specified exclusions
        if exclude_columns:
            columns_to_exclude.update(exclude_columns)
        
        # Create the list of columns to select
        columns_to_select = [col for col in all_columns if col not in columns_to_exclude or col in [date_column, target_column]]
        logger.info(f"Selected {len(columns_to_select)} columns for ML out of {len(all_columns)}")
        
        # Create DuckDB connection
        con = duckdb.connect(":memory:")
        
        # Register the table
        con.register("data", table)
        
        # Build the query to select relevant columns
        column_list = ", ".join([f'"{col}"' for col in columns_to_select])
        query = f'SELECT {column_list} FROM data'
        
        logger.info(f"Executing DuckDB query: {query}")
        
        # Execute query and get DataFrame
        result = con.execute(query).fetchdf()
        logger.info(f"Loaded {len(result)} rows with {len(columns_to_select)} columns")
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing Parquet data: {str(e)}", exc_info=True)
        raise

async def filter_data_by_column_types(df: pd.DataFrame, date_column: str, target_column: str) -> pd.DataFrame:
    """
    Filter DataFrame to include only numeric and boolean columns (plus date and target).
    
    Args:
        df: Input DataFrame
        date_column: Name of the date column to preserve
        target_column: Name of the target column to preserve
        
    Returns:
        Filtered DataFrame with only useful columns for ML
    """
    try:
        # Get list of columns
        all_columns = df.columns.tolist()
        logger.info(f"DataFrame has {len(all_columns)} columns initially")
        
        # Identify numeric and boolean columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        bool_cols = df.select_dtypes(include=['bool']).columns.tolist()
        
        # Always include the target and date columns
        keep_columns = set(numeric_cols + bool_cols)
        keep_columns.add(date_column)
        keep_columns.add(target_column)
        
        # Filter out columns that can't be used for training
        filtered_df = df[list(keep_columns)]
        
        logger.info(f"Filtered to {len(filtered_df.columns)} columns useful for ML")
        logger.info(f"Removed {len(all_columns) - len(filtered_df.columns)} non-numeric/non-boolean columns")
        
        return filtered_df
    
    except Exception as e:
        logger.error(f"Error filtering data: {str(e)}", exc_info=True)
        raise 