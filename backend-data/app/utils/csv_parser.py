import pandas as pd
import io
from typing import List, Dict, Any

async def parse_csv(content: bytes) -> List[Dict[str, Any]]:
    """
    Parse CSV content into a list of dictionaries.
    
    Args:
        content: Raw CSV content as bytes
        
    Returns:
        List of dictionaries, each representing a row in the CSV
    """
    try:
        # Create a buffer from the content
        buffer = io.BytesIO(content)
        
        # Read CSV into a pandas DataFrame
        df = pd.read_csv(buffer)
        
        # Convert DataFrame to list of dictionaries
        records = df.to_dict(orient='records')
        
        return records
    except Exception as e:
        print(f"Error parsing CSV: {str(e)}")
        raise Exception(f"Failed to parse CSV: {str(e)}") 