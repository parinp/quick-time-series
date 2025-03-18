import requests
import os
from dotenv import load_dotenv
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get ML API URL from environment variables
ML_API_URL = os.getenv("ML_API_URL", "http://localhost:8080")

def test_ml_api_connection():
    """Test connection to the ML API service"""
    logger.info(f"Testing connection to ML API at: {ML_API_URL}")
    
    try:
        # Try to connect to the root endpoint
        response = requests.get(f"{ML_API_URL}/")
        
        if response.status_code == 200:
            logger.info(f"Successfully connected to ML API. Status code: {response.status_code}")
            logger.info(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            logger.error(f"Failed to connect to ML API. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error connecting to ML API: {str(e)}")
        return False

def test_ml_api_health():
    """Test health check endpoint of the ML API service"""
    logger.info(f"Testing health endpoint of ML API at: {ML_API_URL}/health")
    
    try:
        # Try to connect to the health endpoint
        response = requests.get(f"{ML_API_URL}/health")
        
        if response.status_code == 200:
            logger.info(f"ML API health check successful. Status code: {response.status_code}")
            logger.info(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            logger.error(f"ML API health check failed. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error checking ML API health: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting ML API connection test")
    
    # Test basic connection
    connection_success = test_ml_api_connection()
    
    # Test health endpoint
    health_success = test_ml_api_health()
    
    if connection_success and health_success:
        logger.info("All tests passed! The ML API is accessible and healthy.")
    else:
        logger.error("Some tests failed. Please check the ML API configuration and connectivity.")
    
    logger.info("ML API connection test completed") 