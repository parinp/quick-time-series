import os
import json
import base64
import io
import logging
from typing import Dict, Any, Optional, Union, List
from dotenv import load_dotenv
from upstash_redis import Redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Redis connection details from environment variables
REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL")
REDIS_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

logger.info(f"Redis URL configured: {REDIS_URL is not None}")
logger.info(f"Redis Token configured: {REDIS_TOKEN is not None}")

# Initialize Redis client
redis_client = None

if REDIS_URL and REDIS_TOKEN:
    try:
        logger.info(f"Initializing Upstash Redis client...")
        redis_client = Redis(url=REDIS_URL, token=REDIS_TOKEN)
        
        # Test connection
        ping_result = redis_client.ping()
        if ping_result:
            logger.info("Successfully connected to Upstash Redis")
        else:
            logger.warning("Failed to connect to Upstash Redis, falling back to mock implementation")
            redis_client = None
    except Exception as e:
        logger.error(f"Error initializing Redis client: {str(e)}", exc_info=True)
        redis_client = None
else:
    logger.warning("Redis credentials not provided")

# If Redis client is None, use mock implementation for testing
if redis_client is None:
    logger.warning("Using mock Redis implementation for development/testing")
    
    class MockRedis:
        def __init__(self):
            self.data = {}
            logger.info("MockRedis initialized")
        
        def get(self, key):
            logger.info(f"MockRedis: Getting {key}")
            return self.data.get(key)
            
        def delete(self, key):
            logger.info(f"MockRedis: Deleting {key}")
            if key in self.data:
                del self.data[key]
                return 1
            return 0
            
        def ping(self):
            logger.info("MockRedis: PING")
            return True
    
    redis_client = MockRedis()

async def retrieve_parquet_data(dataset_id: str) -> Optional[bytes]:
    """
    Retrieve Parquet data from Redis based on dataset ID.
    This function handles the retrieval of metadata and chunked data.
    
    Args:
        dataset_id: The ID of the dataset in Redis
        
    Returns:
        Parquet data as bytes if successful, None otherwise
    """
    try:
        logger.info(f"Retrieving data for dataset: {dataset_id}")
        
        # Step 1: Get metadata
        meta_key = f"{dataset_id}:meta"
        metadata_json = redis_client.get(meta_key)
        
        if not metadata_json:
            logger.warning(f"No metadata found for dataset ID: {dataset_id}")
            return None
        
        # Parse metadata
        try:
            metadata = json.loads(metadata_json)
            logger.info(f"Retrieved metadata for dataset {dataset_id}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in metadata for dataset {dataset_id}")
            return None
        
        # Step 2: Check if chunked
        total_chunks = metadata.get("total_chunks", 1)
        logger.info(f"Dataset {dataset_id} has {total_chunks} chunks")
        
        # Step 3: Retrieve all chunks and combine
        parquet_data = bytearray()
        
        for i in range(total_chunks):
            # Check if this chunk is split
            if metadata.get(f"chunk_{i}_split", False):
                # Handle split chunks
                chunk_parts = metadata.get(f"chunk_{i}_parts", 0)
                for j in range(chunk_parts):
                    sub_key = f"{dataset_id}:chunk:{i}:{j}"
                    sub_encoded = redis_client.get(sub_key)
                    
                    if not sub_encoded:
                        logger.warning(f"Sub-chunk {i}:{j} not found for dataset {dataset_id}")
                        continue
                    
                    # Decode base64
                    sub_chunk = base64.b64decode(sub_encoded)
                    parquet_data.extend(sub_chunk)
            else:
                # Regular chunk
                chunk_key = f"{dataset_id}:chunk:{i}"
                encoded_chunk = redis_client.get(chunk_key)
                
                if not encoded_chunk:
                    logger.warning(f"Chunk {i} not found for dataset {dataset_id}")
                    continue
                
                # Decode base64
                chunk = base64.b64decode(encoded_chunk)
                parquet_data.extend(chunk)
        
        logger.info(f"Retrieved {len(parquet_data)} bytes of data for dataset {dataset_id}")
        
        # Return the complete Parquet data
        return bytes(parquet_data)
        
    except Exception as e:
        logger.error(f"Error retrieving data from Redis: {str(e)}", exc_info=True)
        return None

async def delete_dataset(dataset_id: str) -> bool:
    """
    Delete a dataset and all its associated chunks from Redis.
    
    Args:
        dataset_id: The ID of the dataset to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Deleting dataset: {dataset_id}")
        
        # First get metadata to know how many chunks to delete
        meta_key = f"{dataset_id}:meta"
        metadata_json = redis_client.get(meta_key)
        
        deleted_keys = 0
        
        if metadata_json:
            try:
                metadata = json.loads(metadata_json)
                total_chunks = metadata.get("total_chunks", 1)
                
                # Delete each chunk
                for i in range(total_chunks):
                    # Check if this chunk is split
                    if metadata.get(f"chunk_{i}_split", False):
                        chunk_parts = metadata.get(f"chunk_{i}_parts", 0)
                        for j in range(chunk_parts):
                            sub_key = f"{dataset_id}:chunk:{i}:{j}"
                            result = redis_client.delete(sub_key)
                            deleted_keys += result
                    else:
                        chunk_key = f"{dataset_id}:chunk:{i}"
                        result = redis_client.delete(chunk_key)
                        deleted_keys += result
                
                # Delete metadata
                result = redis_client.delete(meta_key)
                deleted_keys += result
                
                logger.info(f"Deleted {deleted_keys} keys for dataset {dataset_id}")
                
                return deleted_keys > 0
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in metadata for dataset {dataset_id}")
                
                # Try to delete metadata anyway
                redis_client.delete(meta_key)
                return False
        else:
            logger.warning(f"No metadata found for dataset ID: {dataset_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting dataset from Redis: {str(e)}", exc_info=True)
        return False 