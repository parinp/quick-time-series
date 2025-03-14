import os
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
from typing import Dict, List, Any, Optional, Union
import json
import re

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def get_sample_data(dataset_name: str = "rossmann") -> List[Dict[str, Any]]:
    """
    Get sample data from Supabase.
    
    Args:
        dataset_name: Name of the dataset to retrieve
        
    Returns:
        List of dictionaries containing the data
    """
    try:
        # Check if this is a chunked dataset
        chunk_pattern = re.compile(r'^(.+)_chunk_(\d+)$')
        match = chunk_pattern.match(dataset_name)
        
        if match:
            # This is already a specific chunk, retrieve it directly
            response = supabase.table("sample_data").select("*").eq("dataset_name", dataset_name).execute()
            
            if not response.data:
                raise ValueError(f"No sample data found for dataset chunk: {dataset_name}")
            
            data_json = response.data[0].get("data")
            
            # Parse the JSON data
            if isinstance(data_json, str):
                return json.loads(data_json)
            else:
                return data_json
        
        # First try to get the dataset as a single entity
        response = supabase.table("sample_data").select("*").eq("dataset_name", dataset_name).execute()
        
        if response.data:
            # Dataset exists as a single entity
            data_json = response.data[0].get("data")
            
            # Parse the JSON data
            if isinstance(data_json, str):
                return json.loads(data_json)
            else:
                return data_json
        
        # If not found, check if it's a chunked dataset
        # Query for chunks
        response = supabase.table("sample_data").select("*").like("dataset_name", f"{dataset_name}_chunk_%").execute()
        
        if not response.data:
            raise ValueError(f"No sample data found for dataset: {dataset_name}")
        
        # Sort chunks by number
        chunks = sorted(response.data, key=lambda x: int(x["dataset_name"].split("_chunk_")[1]))
        
        # Combine all chunks
        combined_data = []
        for chunk in chunks:
            data_json = chunk.get("data")
            
            # Parse the JSON data
            if isinstance(data_json, str):
                chunk_data = json.loads(data_json)
            else:
                chunk_data = data_json
                
            combined_data.extend(chunk_data)
        
        return combined_data
    except Exception as e:
        print(f"Error retrieving sample data: {str(e)}")
        raise

def get_available_datasets() -> Dict[str, Any]:
    """
    Get a list of available sample datasets.
    
    Returns:
        Dictionary with dataset information
    """
    try:
        # Query the sample_data table for all datasets
        response = supabase.table("sample_data").select("dataset_name, description, created_at").execute()
        
        # Process dataset names to group chunks
        datasets = {}
        chunk_pattern = re.compile(r'^(.+)_chunk_(\d+)$')
        
        for row in response.data:
            dataset_name = row.get("dataset_name")
            description = row.get("description")
            created_at = row.get("created_at")
            
            match = chunk_pattern.match(dataset_name)
            if match:
                # This is a chunk
                base_name = match.group(1)
                chunk_num = int(match.group(2))
                
                if base_name not in datasets:
                    datasets[base_name] = {
                        "name": base_name,
                        "is_chunked": True,
                        "chunks": [],
                        "description": description.split(" (Chunk")[0] if description else None,
                        "created_at": created_at
                    }
                
                datasets[base_name]["chunks"].append({
                    "name": dataset_name,
                    "chunk_num": chunk_num,
                    "created_at": created_at
                })
            else:
                # This is a regular dataset
                datasets[dataset_name] = {
                    "name": dataset_name,
                    "is_chunked": False,
                    "description": description,
                    "created_at": created_at
                }
        
        # Sort chunks within each dataset
        for dataset in datasets.values():
            if dataset["is_chunked"] and "chunks" in dataset:
                dataset["chunks"] = sorted(dataset["chunks"], key=lambda x: x["chunk_num"])
                dataset["chunk_count"] = len(dataset["chunks"])
        
        return {
            "datasets": list(datasets.values())
        }
    except Exception as e:
        print(f"Error retrieving dataset names: {str(e)}")
        raise

def save_model_results(model_name: str, dataset_name: str, metrics: Dict[str, Any], 
                      feature_importance: Dict[str, float], user_id: Optional[str] = None) -> int:
    """
    Save model results to Supabase.
    
    Args:
        model_name: Name of the model
        dataset_name: Name of the dataset
        metrics: Dictionary of model metrics
        feature_importance: Dictionary of feature importance values
        user_id: Optional user ID
        
    Returns:
        ID of the inserted record
    """
    try:
        # Prepare data for insertion
        data = {
            "model_name": model_name,
            "dataset_name": dataset_name,
            "metrics": json.dumps(metrics),
            "feature_importance": json.dumps(feature_importance),
            "user_id": user_id
        }
        
        # Insert data into the model_results table
        response = supabase.table("model_results").insert(data).execute()
        
        # Return the ID of the inserted record
        return response.data[0].get("id")
    except Exception as e:
        print(f"Error saving model results: {str(e)}")
        raise

def save_predictions(model_id: int, predictions: List[float], dates: List[str]) -> None:
    """
    Save predictions to Supabase.
    
    Args:
        model_id: ID of the model
        predictions: List of prediction values
        dates: List of dates corresponding to predictions
    """
    try:
        # Prepare data for insertion
        data = []
        for i, (date, pred) in enumerate(zip(dates, predictions)):
            data.append({
                "model_id": model_id,
                "date": date,
                "predicted_value": pred
            })
        
        # Insert data into the predictions table
        supabase.table("predictions").insert(data).execute()
    except Exception as e:
        print(f"Error saving predictions: {str(e)}")
        raise

def upload_sample_data(dataset_name: str, data: List[Dict[str, Any]], description: Optional[str] = None) -> None:
    """
    Upload sample data to Supabase.
    
    Args:
        dataset_name: Name of the dataset
        data: List of dictionaries containing the data
        description: Optional description of the dataset
    """
    try:
        # Prepare data for insertion
        insert_data = {
            "dataset_name": dataset_name,
            "data": json.dumps(data),
            "description": description or f"Sample data for {dataset_name}"
        }
        
        # Check if dataset already exists
        response = supabase.table("sample_data").select("*").eq("dataset_name", dataset_name).execute()
        
        if response.data:
            # Update existing dataset
            supabase.table("sample_data").update(insert_data).eq("dataset_name", dataset_name).execute()
        else:
            # Insert new dataset
            supabase.table("sample_data").insert(insert_data).execute()
    except Exception as e:
        print(f"Error uploading sample data: {str(e)}")
        raise 