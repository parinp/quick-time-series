import duckdb
import io
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import json
from typing import Dict, List, Any, Optional
import traceback

async def query_parquet_data(
    parquet_data: bytes,
    filters: Dict[str, Dict[str, Any]] = None,
    limit: int = 1000,
    offset: int = 0,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    aggregate: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Query Parquet data using DuckDB.
    
    Args:
        parquet_data: Parquet data as bytes
        filters: Dictionary of filters to apply
        limit: Maximum number of rows to return
        offset: Number of rows to skip
        sort_by: Column to sort by
        sort_order: Sort order (asc or desc)
        aggregate: Dictionary with 'date_column' and 'target_column' for groupby aggregation
        
    Returns:
        List of dictionaries, each representing a row
    """
    try:
        # Create a buffer from the content
        buffer = io.BytesIO(parquet_data)
        
        # Determine if this is Parquet or JSON data
        try:
            # Try to read as Parquet
            table = pq.read_table(buffer)
            print("Data format: Parquet")
        except Exception as e:
            print(f"Not Parquet format: {str(e)}")
            try:
                # Try to parse as JSON
                buffer.seek(0)
                json_data = buffer.getvalue().decode('utf-8')
                df = pd.read_json(json_data, orient='records')
                print("Data format: JSON")
                
                # Create a DuckDB connection
                con = duckdb.connect(":memory:")
                
                # Register the DataFrame
                con.register("data", df)
            except Exception as json_error:
                print(f"Failed to parse as JSON: {str(json_error)}")
                print(traceback.format_exc())
                raise Exception("Data is neither valid Parquet nor JSON format")
        else:
            # If Parquet parsing was successful
            # Create a DuckDB connection
            con = duckdb.connect(":memory:")
            
            # Register the table
            con.register("data", table)
        
        # Build the query
        if aggregate and 'date_column' in aggregate and 'target_column' in aggregate:
            # Use GROUP BY with SUM aggregation
            date_column = aggregate['date_column']
            target_column = aggregate['target_column']
            query = f"SELECT {date_column}, SUM({target_column}) as {target_column} FROM data"
        else:
            # Standard query without aggregation
            query = "SELECT * FROM data"
        
        # Add filters if provided
        where_clauses = []
        if filters:
            for column, filter_info in filters.items():
                operator = filter_info.get("operator", "=")
                value = filter_info.get("value")
                
                # Skip if value is None
                if value is None:
                    continue
                
                # Handle different value types
                if isinstance(value, str):
                    # Escape single quotes in string values
                    value = value.replace("'", "''")
                    where_clauses.append(f"{column} {operator} '{value}'")
                elif isinstance(value, bool):
                    # Handle boolean values
                    where_clauses.append(f"{column} {operator} {str(value).lower()}")
                else:
                    where_clauses.append(f"{column} {operator} {value}")
        
        # Add WHERE clause if there are filters
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        # Add GROUP BY if using aggregation
        if aggregate and 'date_column' in aggregate and 'target_column' in aggregate:
            query += f" GROUP BY {aggregate['date_column']}"
        
        # Add ORDER BY clause if sort_by is provided
        if sort_by:
            query += f" ORDER BY {sort_by} {sort_order}"
        
        # Add LIMIT and OFFSET clauses
        query += f" LIMIT {limit} OFFSET {offset}"
        
        print(f"Executing DuckDB query: {query}")
        
        # Execute the query
        try:
            result = con.execute(query).fetchdf()
        except Exception as query_error:
            print(f"DuckDB query error: {str(query_error)}")
            # Try with a more fault-tolerant approach
            print("Trying a simplified query...")
            if aggregate and 'date_column' in aggregate and 'target_column' in aggregate:
                fallback_query = f"SELECT {aggregate['date_column']}, SUM({aggregate['target_column']}) as {aggregate['target_column']} FROM data GROUP BY {aggregate['date_column']} LIMIT {limit} OFFSET {offset}"
            else:
                fallback_query = f"SELECT * FROM data LIMIT {limit} OFFSET {offset}"
            result = con.execute(fallback_query).fetchdf()
        
        # Convert to list of dictionaries
        records = result.to_dict(orient='records')
        
        # Convert any non-serializable types to strings
        for record in records:
            for key, value in record.items():
                if not isinstance(value, (str, int, float, bool, type(None))):
                    record[key] = str(value)
        
        return records
    except Exception as e:
        print(f"Error querying data: {str(e)}")
        print(traceback.format_exc())
        raise Exception(f"Failed to query data: {str(e)}") 