import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from typing import List, Dict, Any
import io
import numpy as np

async def convert_to_parquet(data: List[Dict[str, Any]]) -> pa.Buffer:
    """
    Convert a list of dictionaries to Parquet format.
    
    Args:
        data: List of dictionaries, each representing a row
        
    Returns:
        PyArrow Buffer containing the Parquet data
    """
    try:
        # Convert to pandas DataFrame
        df = pd.DataFrame(data)
        
        # Pre-process problematic columns and convert object types to strings
        for column in df.columns:
            # Specifically handle StateHoliday column (the one from the error)
            if column == 'StateHoliday':
                df[column] = df[column].astype(str)
            
            # Handle all object types by converting to strings
            if df[column].dtype == 'object':
                df[column] = df[column].astype(str)
            
            # Handle any nan values
            if df[column].isna().any():
                if pd.api.types.is_numeric_dtype(df[column]):
                    # For numeric columns, replace NaN with 0
                    df[column] = df[column].fillna(0)
                else:
                    # For non-numeric columns, replace NaN with empty string
                    df[column] = df[column].fillna('')
        
        # Convert to PyArrow Table with string type for object columns
        table = pa.Table.from_pandas(df)
        
        # Write to in-memory buffer
        buffer = io.BytesIO()
        pq.write_table(table, buffer)
        
        # Get the buffer content
        buffer.seek(0)
        
        # Return as PyArrow Buffer
        return pa.py_buffer(buffer.getvalue())
    except Exception as e:
        print(f"Error converting to Parquet: {str(e)}")
        # Fallback to JSON as bytes
        try:
            print("Attempting fallback to JSON format")
            json_data = pd.DataFrame(data).to_json(orient='records')
            return pa.py_buffer(json_data.encode('utf-8'))
        except Exception as fallback_error:
            print(f"Fallback to JSON also failed: {str(fallback_error)}")
            raise Exception(f"Failed to convert to Parquet: {str(e)}")

async def parse_parquet_buffer(buffer: bytes) -> List[Dict[str, Any]]:
    """
    Parse Parquet buffer back to a list of dictionaries.
    
    Args:
        buffer: Parquet data as bytes
        
    Returns:
        List of dictionaries, each representing a row
    """
    try:
        # Create a buffer from the content
        io_buffer = io.BytesIO(buffer)
        
        try:
            # First try to read as Parquet
            table = pq.read_table(io_buffer)
            df = table.to_pandas()
        except Exception as e:
            print(f"Failed to parse as Parquet, trying JSON fallback: {str(e)}")
            # If Parquet fails, try reading as JSON
            io_buffer.seek(0)
            json_data = io_buffer.getvalue().decode('utf-8')
            df = pd.read_json(json_data, orient='records')
            
        # Convert DataFrame to list of dictionaries
        records = df.to_dict(orient='records')
        
        return records
    except Exception as e:
        print(f"Error parsing buffer: {str(e)}")
        raise Exception(f"Failed to parse buffer: {str(e)}") 