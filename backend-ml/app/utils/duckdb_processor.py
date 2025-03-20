import duckdb
import pandas as pd
import io
import logging
import asyncio
from typing import List, Optional, Dict, Any, Union
import pyarrow as pa
import pyarrow.parquet as pq

# Configure logging
logger = logging.getLogger(__name__)

# Configure DuckDB for memory-efficient operation
DUCKDB_MEMORY_LIMIT = "50%"  # Default memory limit is 50% of system memory
DUCKDB_TEMP_DIR = None  # Use default temporary directory

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

def process_parquet_pandas(parquet_data: bytes,
                          date_column: str,
                          target_column: str,
                          exclude_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Fallback method to process Parquet data using pandas.
    
    Args:
        parquet_data: The Parquet file content as bytes
        date_column: The name of the date column
        target_column: The name of the target column
        exclude_columns: List of columns to exclude
        
    Returns:
        Pandas DataFrame with the processed data
    """
    logger.info("Processing Parquet data with pandas")
    
    # Create a buffer from the bytes
    buffer = io.BytesIO(parquet_data)
    
    # Read the schema to get column names without loading all data
    parquet_file = pd.read_parquet(buffer, columns=[])
    all_columns = parquet_file.columns.tolist()
    
    # Determine which columns to select
    columns_to_select = []
    
    # Always include date and target columns
    columns_to_select.append(date_column)
    if target_column != date_column:  # Avoid duplication
        columns_to_select.append(target_column)
        
    # Add other columns, excluding those specified
    for col in all_columns:
        if col not in columns_to_select:  # Skip already added columns
            if exclude_columns and col in exclude_columns:
                continue  # Skip excluded columns
            columns_to_select.append(col)
    
    # Reset buffer position
    buffer.seek(0)
    
    # Read only the selected columns
    df = pd.read_parquet(buffer, columns=columns_to_select)
    logger.info(f"Pandas processed DataFrame shape: {df.shape}")
    
    return df

async def filter_data_by_column_types(df: pd.DataFrame, date_column: str, target_column: str) -> pd.DataFrame:
    """
    Filter DataFrame to include only numeric and boolean columns (plus date and target).
    
    Args:
        df: DataFrame to filter
        date_column: Name of the date column (always included)
        target_column: Name of the target column (always included)
        
    Returns:
        Filtered DataFrame
    """
    # Get numeric and boolean columns
    numeric_cols = df.select_dtypes(include=['number', 'bool']).columns.tolist()
    
    # Always include date and target columns
    columns_to_keep = list(set(numeric_cols + [date_column, target_column]))
    
    # Log what we're keeping and dropping
    all_columns = df.columns.tolist()
    dropped_columns = [col for col in all_columns if col not in columns_to_keep]
    
    logger.info(f"Keeping {len(columns_to_keep)} columns: {columns_to_keep}")
    if dropped_columns:
        logger.info(f"Dropping {len(dropped_columns)} non-numeric columns: {dropped_columns}")
    
    # Return filtered DataFrame
    return df[columns_to_keep]

async def compute_column_statistics(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Compute column statistics for a DataFrame.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dictionary of column statistics
    """
    stats = {}
    
    for col in df.columns:
        col_stats = {
            "dtype": str(df[col].dtype),
            "count": int(df[col].count()),
            "null_count": int(df[col].isna().sum()),
            "unique_count": int(df[col].nunique())
        }
        
        # Add numeric stats if applicable
        if pd.api.types.is_numeric_dtype(df[col]):
            col_stats.update({
                "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                "median": float(df[col].median()) if not pd.isna(df[col].median()) else None,
                "std": float(df[col].std()) if not pd.isna(df[col].std()) else None
            })
        
        stats[col] = col_stats
    
    return stats

async def execute_duckdb_query(
    parquet_data: bytes,
    query: str
) -> pd.DataFrame:
    """
    Execute a custom DuckDB query on Parquet data.
    
    Args:
        parquet_data: Parquet file as bytes
        query: SQL query to execute (should reference the table as 'parquet_data')
        
    Returns:
        DataFrame with query results
    """
    try:
        # Create a DuckDB connection with memory settings
        conn = duckdb.connect(":memory:")
        conn.execute(f"PRAGMA memory_limit='{DUCKDB_MEMORY_LIMIT}'")
        
        if DUCKDB_TEMP_DIR:
            conn.execute(f"PRAGMA temp_directory='{DUCKDB_TEMP_DIR}'")
        
        # Register the parquet data as a view
        conn.execute("CREATE VIEW parquet_data AS SELECT * FROM parquet_scan(?)", [parquet_data])
        
        # Execute the query
        df = conn.execute(query).df()
        
        logger.info(f"Executed DuckDB query, returned {len(df)} rows")
        
        # Close DuckDB connection
        conn.close()
        
        return df
    
    except Exception as e:
        logger.error(f"Error executing DuckDB query: {str(e)}")
        raise 