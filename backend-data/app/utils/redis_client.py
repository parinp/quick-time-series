import json
import os
from typing import Dict, Any, Optional
import asyncio
import base64
import time
import traceback
from dotenv import load_dotenv
from upstash_redis import Redis

# Load environment variables from .env file
load_dotenv()

# Get Redis connection details from environment variables
REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL")
REDIS_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

print(f"DEBUG: Redis URL configured: {REDIS_URL is not None}")
print(f"DEBUG: Redis Token configured: {REDIS_TOKEN is not None}")
if REDIS_URL:
    print(f"DEBUG: Redis URL begins with: {REDIS_URL[:10]}...")

# Initialize Redis client based on available credentials
redis_client = None

if REDIS_URL and REDIS_TOKEN:
    try:
        print(f"Initializing Upstash Redis client with URL starting with: {REDIS_URL[:20]}...")
        # Initialize the official Upstash Redis SDK client
        redis_client = Redis(url=REDIS_URL, token=REDIS_TOKEN)
        
        # Test connection
        try:
            ping_result = redis_client.ping()
            print(f"Redis connection test result: {ping_result}")
            if ping_result:
                print("Successfully connected to Upstash Redis")
            else:
                print("Failed to connect to Upstash Redis, falling back to mock implementation")
                redis_client = None
        except Exception as e:
            print(f"Error testing Redis connection: {str(e)}")
            print(traceback.format_exc())
            redis_client = None
    except Exception as e:
        print(f"Error initializing Upstash Redis client: {str(e)}")
        print(traceback.format_exc())
        redis_client = None
else:
    print("Upstash Redis credentials not provided")
    redis_client = None

# If Redis connection failed or credentials not provided, use mock implementation
if redis_client is None:
    print("Using mock Redis implementation for development/testing")
    
    # Simple in-memory store for testing
    class MockRedis:
        def __init__(self):
            self.data = {}
            print("MockRedis initialized")
        
        def set(self, key, value, ex=None):
            print(f"MockRedis: Setting {key} (expires in {ex}s if specified)")
            self.data[key] = value
            return True
            
        def get(self, key):
            print(f"MockRedis: Getting {key}")
            return self.data.get(key)
            
        def ping(self):
            print("MockRedis: PING")
            return True
    
    redis_client = MockRedis()

# Maximum chunk size - smaller to account for base64 overhead (~33% increase)
# Upstash has a 1MB (1048576 bytes) limit, so we'll use ~700KB as base
MAX_CHUNK_SIZE = 700 * 1024  # ~700KB which becomes ~933KB after base64 encoding

# Fixed TTL for all data (15 minutes = 900 seconds)
DEFAULT_TTL = 900  # 15 minutes

async def store_data(key: str, data: Dict[str, Any]) -> bool:
    """
    Store data in Redis with a fixed TTL of 15 minutes.
    
    Args:
        key: Redis key
        data: Data to store
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"Storing data for key: {key} with TTL: {DEFAULT_TTL}s")
        
        # Check if data contains binary content (Parquet data)
        if "parquet_data" in data and hasattr(data["parquet_data"], "__len__"):
            # Get the Parquet data
            parquet_data = data["parquet_data"]
            parquet_size = len(parquet_data)
            print(f"Parquet data size: {parquet_size} bytes")
            
            # Calculate optimal chunk size based on total size
            # For very large files, use smaller chunks to stay well below limit
            if parquet_size > 10 * 1024 * 1024:  # > 10MB
                chunk_size = 500 * 1024  # ~500KB
            elif parquet_size > 5 * 1024 * 1024:  # > 5MB
                chunk_size = 600 * 1024  # ~600KB
            else:
                chunk_size = MAX_CHUNK_SIZE  # ~700KB
                
            print(f"Using chunk size of {chunk_size / 1024:.1f}KB")
            
            # Remove Parquet data from the metadata to store separately
            metadata = {k: v for k, v in data.items() if k != "parquet_data"}
            
            # Store metadata
            meta_key = f"{key}:meta"
            print(f"Storing metadata for key: {meta_key}")
            try:
                meta_result = redis_client.set(meta_key, json.dumps(metadata), ex=DEFAULT_TTL)
                print(f"Metadata storage result: {meta_result}")
                if not meta_result:
                    print(f"Failed to store metadata for key {key}")
                    return False
            except Exception as e:
                print(f"Error storing metadata: {str(e)}")
                print(traceback.format_exc())
                return False
            
            # Calculate number of chunks needed
            total_size = len(parquet_data)
            num_chunks = (total_size + chunk_size - 1) // chunk_size
            print(f"Splitting data into {num_chunks} chunks")
            
            # Update metadata with chunk info
            metadata["total_chunks"] = num_chunks
            metadata["total_size"] = total_size
            metadata["chunk_size"] = chunk_size
            
            try:
                meta_update_result = redis_client.set(meta_key, json.dumps(metadata), ex=DEFAULT_TTL)
                print(f"Metadata update result: {meta_update_result}")
                if not meta_update_result:
                    print(f"Failed to update metadata with chunk info for key {key}")
                    return False
            except Exception as e:
                print(f"Error updating metadata: {str(e)}")
                print(traceback.format_exc())
                return False
            
            # Store data in chunks
            successful_chunks = 0
            for i in range(num_chunks):
                start = i * chunk_size
                end = min(start + chunk_size, total_size)
                chunk = parquet_data[start:end]
                chunk_size_actual = len(chunk)
                chunk_key = f"{key}:chunk:{i}"
                print(f"Storing chunk {i} for key {chunk_key}, size: {chunk_size_actual} bytes")
                
                try:
                    # Use base64 encoding for binary data
                    encoded_chunk = base64.b64encode(chunk).decode('utf-8')
                    encoded_size = len(encoded_chunk)
                    print(f"Encoded chunk to base64 string, new size: {encoded_size} bytes")
                    
                    if encoded_size >= 1000000:  # Close to 1MB limit
                        print(f"WARNING: Encoded chunk size ({encoded_size}) is close to Upstash limit (1MB)")
                    
                    # Store the base64 encoded string
                    chunk_result = redis_client.set(chunk_key, encoded_chunk, ex=DEFAULT_TTL)
                    print(f"Chunk {i} storage result: {chunk_result}")
                    if not chunk_result:
                        print(f"Failed to store chunk {i} for key {key}")
                        return False
                    
                    successful_chunks += 1
                except Exception as e:
                    print(f"Error storing chunk {i}: {str(e)}")
                    print(traceback.format_exc())
                    
                    # If we hit a size limit, try with a smaller chunk
                    if "max request size exceeded" in str(e).lower():
                        # Calculate a smaller size for this chunk
                        retry_size = int(chunk_size_actual * 0.7)  # 70% of original size
                        print(f"Retrying with smaller chunk size: {retry_size} bytes")
                        
                        # Split this chunk further
                        for j in range((chunk_size_actual + retry_size - 1) // retry_size):
                            sub_start = start + j * retry_size
                            sub_end = min(sub_start + retry_size, end)
                            sub_chunk = parquet_data[sub_start:sub_end]
                            sub_key = f"{key}:chunk:{i}:{j}"
                            
                            try:
                                sub_encoded = base64.b64encode(sub_chunk).decode('utf-8')
                                sub_result = redis_client.set(sub_key, sub_encoded, ex=DEFAULT_TTL)
                                if not sub_result:
                                    print(f"Failed to store sub-chunk {i}:{j}")
                                    return False
                                
                                # Update metadata to indicate this chunk is split
                                metadata[f"chunk_{i}_split"] = True
                                metadata[f"chunk_{i}_parts"] = (chunk_size_actual + retry_size - 1) // retry_size
                                redis_client.set(meta_key, json.dumps(metadata), ex=DEFAULT_TTL)
                                
                                successful_chunks += 1
                            except Exception as sub_e:
                                print(f"Error storing sub-chunk {i}:{j}: {str(sub_e)}")
                                return False
                    else:
                        return False
                
            print(f"Successfully stored all {successful_chunks} chunks for key {key}")
            return True
        else:
            # Store regular data
            print(f"Storing regular data for key {key}")
            try:
                # Convert data to JSON if it's a dictionary
                data_to_store = json.dumps(data) if isinstance(data, (dict, list)) else data
                result = redis_client.set(key, data_to_store, ex=DEFAULT_TTL)
                print(f"Regular data storage result: {result}")
                return result
            except Exception as e:
                print(f"Error storing regular data: {str(e)}")
                print(traceback.format_exc())
                return False
            
    except Exception as e:
        print(f"Error storing data in Redis: {str(e)}")
        print(traceback.format_exc())
        return False

async def retrieve_data(key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve data from Redis.
    
    Args:
        key: Redis key
        
    Returns:
        Data if found, None otherwise
    """
    try:
        print(f"Retrieving data for key: {key}")
        
        # Check if this is chunked data
        meta_key = f"{key}:meta"
        try:
            metadata_raw = redis_client.get(meta_key)
            print(f"Metadata retrieval result: {metadata_raw is not None}")
        except Exception as e:
            print(f"Error retrieving metadata: {str(e)}")
            print(traceback.format_exc())
            metadata_raw = None
        
        if metadata_raw:
            print(f"Found metadata for key: {meta_key}")
            
            # Parse metadata
            try:
                if isinstance(metadata_raw, bytes):
                    metadata = json.loads(metadata_raw.decode('utf-8'))
                elif isinstance(metadata_raw, str):
                    metadata = json.loads(metadata_raw)
                else:
                    # Assuming already parsed JSON
                    metadata = metadata_raw
            except Exception as e:
                print(f"Error parsing metadata: {str(e)}")
                print(traceback.format_exc())
                return None
            
            # Get number of chunks
            num_chunks = metadata.get("total_chunks", 0)
            print(f"Dataset has {num_chunks} chunks")
            
            if num_chunks > 0:
                # Retrieve all chunks
                chunks = []
                for i in range(num_chunks):
                    # Check if this chunk was split into sub-chunks
                    if metadata.get(f"chunk_{i}_split"):
                        num_sub_chunks = metadata.get(f"chunk_{i}_parts", 0)
                        print(f"Chunk {i} was split into {num_sub_chunks} sub-chunks")
                        sub_chunks = []
                        
                        for j in range(num_sub_chunks):
                            sub_key = f"{key}:chunk:{i}:{j}"
                            print(f"Retrieving sub-chunk {j} for key {sub_key}")
                            
                            try:
                                encoded_sub_chunk = redis_client.get(sub_key)
                                if not encoded_sub_chunk:
                                    print(f"Missing sub-chunk {i}:{j} for key {key}")
                                    raise Exception(f"Missing sub-chunk {i}:{j} for key {key}")
                                
                                # Decode from base64 to binary
                                if isinstance(encoded_sub_chunk, bytes):
                                    encoded_sub_chunk = encoded_sub_chunk.decode('utf-8')
                                
                                sub_chunk = base64.b64decode(encoded_sub_chunk)
                                print(f"Decoded sub-chunk {i}:{j} from base64, size: {len(sub_chunk)} bytes")
                                sub_chunks.append(sub_chunk)
                            except Exception as e:
                                print(f"Error retrieving sub-chunk {i}:{j}: {str(e)}")
                                print(traceback.format_exc())
                                return None
                        
                        # Combine all sub-chunks for this chunk
                        combined_chunk = b"".join(sub_chunks)
                        print(f"Combined {len(sub_chunks)} sub-chunks for chunk {i}, size: {len(combined_chunk)} bytes")
                        chunks.append(combined_chunk)
                    else:
                        # Regular chunk
                        chunk_key = f"{key}:chunk:{i}"
                        print(f"Retrieving chunk {i} for key {chunk_key}")
                        
                        try:
                            # Get the base64 encoded chunk
                            encoded_chunk = redis_client.get(chunk_key)
                            if not encoded_chunk:
                                print(f"Missing chunk {i} for key {key}")
                                raise Exception(f"Missing chunk {i} for key {key}")
                            
                            # Decode from base64 to binary
                            if isinstance(encoded_chunk, bytes):
                                encoded_chunk = encoded_chunk.decode('utf-8')
                            
                            chunk = base64.b64decode(encoded_chunk)
                            print(f"Decoded chunk {i} from base64, size: {len(chunk)} bytes")
                            chunks.append(chunk)
                        except Exception as e:
                            print(f"Error retrieving chunk {i}: {str(e)}")
                            print(traceback.format_exc())
                            return None
                
                # Combine chunks
                parquet_data = b"".join(chunks)
                print(f"Combined {len(chunks)} chunks, total size: {len(parquet_data)} bytes")
                
                # Return combined data with metadata
                return {
                    **metadata,
                    "parquet_data": parquet_data
                }
            else:
                # Return metadata only
                return metadata
        else:
            # Try regular key
            print(f"No metadata found, trying regular key: {key}")
            
            try:
                data_raw = redis_client.get(key)
                print(f"Regular data retrieval result: {data_raw is not None}")
            except Exception as e:
                print(f"Error retrieving regular data: {str(e)}")
                print(traceback.format_exc())
                return None
            
            if data_raw:
                print(f"Found data for key: {key}")
                # Try to parse data
                try:
                    if isinstance(data_raw, bytes):
                        try:
                            # Try to decode as JSON
                            return json.loads(data_raw.decode('utf-8'))
                        except:
                            # If not JSON, return as is
                            return {"data": data_raw}
                    elif isinstance(data_raw, str):
                        try:
                            # Try to parse as JSON
                            return json.loads(data_raw)
                        except:
                            # If not JSON, return as is
                            return {"data": data_raw}
                    else:
                        # Already parsed data
                        return data_raw
                except Exception as e:
                    print(f"Error parsing data: {str(e)}")
                    print(traceback.format_exc())
                    return None
            else:
                print(f"No data found for key: {key}")
                return None
                
    except Exception as e:
        print(f"Error retrieving data from Redis: {str(e)}")
        print(traceback.format_exc())
        return None 