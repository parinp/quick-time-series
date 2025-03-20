#!/usr/bin/env python3
"""
Script to test the connection between the backend service and ML service.
Tests both the direct API call and the Redis-based approach.
"""

import os
import json
import time
import random
import requests
from dotenv import load_dotenv
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get ML service URL from environment variable or use default
ML_API_URL = os.getenv("ML_API_URL", "http://localhost:8080")

def test_direct_connection():
    """Test the direct connection to the ML service API"""
    logger.info(f"Testing direct connection to ML service at {ML_API_URL}...")
    
    try:
        # Check if the ML service is healthy
        response = requests.get(f"{ML_API_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ ML service is healthy: {data}")
            return True
        else:
            logger.error(f"❌ ML service responded with status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to connect to ML service: {str(e)}")
        return False

def test_redis_connection():
    """Test the Redis-based approach by creating a mock dataset and analyzing it"""
    # This simulates what the backend-data service would do
    backend_api_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
    
    logger.info(f"Testing Redis-based approach via backend service at {backend_api_url}...")
    
    try:
        # 1. Create a simple mock dataset
        data = []
        start_date = pd.Timestamp('2022-01-01')
        
        for i in range(100):
            date = start_date + pd.Timedelta(days=i)
            value = 100 + i + random.randint(-10, 10)
            data.append({"date": date.strftime("%Y-%m-%d"), "value": value})
        
        # 2. Upload the dataset to the backend
        upload_response = requests.post(
            f"{backend_api_url}/datasets/", 
            json={"data": data},
            timeout=30
        )
        
        if upload_response.status_code != 200:
            logger.error(f"❌ Failed to upload dataset: {upload_response.status_code}: {upload_response.text}")
            return False
        
        dataset_info = upload_response.json()
        dataset_id = dataset_info.get("dataset_id")
        
        if not dataset_id:
            logger.error("❌ No dataset_id returned from upload")
            return False
        
        logger.info(f"✅ Successfully uploaded dataset with ID: {dataset_id}")
        
        # 3. Request ML analysis via the Redis-based approach
        analysis_response = requests.post(
            f"{backend_api_url}/ml/analyze",
            json={
                "dataset_id": dataset_id,
                "date_column": "date",
                "target_column": "value",
                "multiple_waterfall_plots": True
            },
            timeout=60
        )
        
        if analysis_response.status_code != 200:
            logger.error(f"❌ ML analysis failed: {analysis_response.status_code}: {analysis_response.text}")
            return False
        
        analysis_result = analysis_response.json()
        
        # 4. Verify the response has expected fields
        if "results" in analysis_result and "metrics" in analysis_result["results"]:
            logger.info("✅ Successfully received ML analysis results via Redis-based approach")
            logger.info(f"✅ Metrics: {json.dumps(analysis_result['results']['metrics'], indent=2)}")
            return True
        else:
            logger.error(f"❌ Unexpected response format: {json.dumps(analysis_result, indent=2)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing Redis-based approach: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("ML Service Connection Test")
    logger.info("=" * 80)
    
    # Test direct connection
    direct_test_result = test_direct_connection()
    
    logger.info("\n" + "=" * 80)
    
    # Test Redis-based approach
    redis_test_result = test_redis_connection()
    
    logger.info("\n" + "=" * 80)
    logger.info("Summary:")
    logger.info(f"Direct API connection: {'✅ PASS' if direct_test_result else '❌ FAIL'}")
    logger.info(f"Redis-based approach: {'✅ PASS' if redis_test_result else '❌ FAIL'}")
    logger.info("=" * 80)
    
    # Overall success/failure
    if direct_test_result and redis_test_result:
        logger.info("All tests passed! The services are properly connected.")
        exit(0)
    else:
        logger.error("Some tests failed. Please check the connection between services.")
        exit(1) 